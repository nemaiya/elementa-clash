import math
import random
from typing import override, final, TypeAlias, Literal

import pygame
from pygame.surface import Surface

from components.Button import Button, ImageOption
from components.Image import ImageComponent, TextImageComponent, TextOption
from .BasePage import BasePage
from util.Game.BattlePlayer import DIE_FACES, MAX_HAND_SIZE, BattlePlayer, OtherBattlePlayer
from util.Game.Card import ActionCard, CharacterCard
from util.Game.Combat import CombatEngine, CombatResult
from util.GlobalHolder import GlobalHolder


BattleSubEvents: TypeAlias = Literal["action_card_selector", "character_selector", "first_player_flip", "roll", "action", "game_over"]


class TestPage(BasePage):
    FLIP_DURATION_MS: int = 2400
    COIN_SIZE: tuple[int, int] = (130, 130)
    COIN_CENTER: tuple[int, int] = (480, 270)

    DICE_ROLL_MS: int = 700
    DICE_FACE_SWAP_MS: int = 70
    DIE_SIZE: tuple[int, int] = (64, 64)
    DIE_POSITIONS: list[tuple[int, int]] = [
        (214, 235), (290, 235), (366, 235), (442, 235), (518, 235), (594, 235), (670, 235), (746, 235),
        (214, 340), (290, 340), (366, 340), (442, 340), (518, 340), (594, 340), (670, 340), (746, 340),
    ]
    DIE_COLORS: dict[str, tuple[int, int, int]] = {
        "omni": (255, 236, 190),
        "pyro": (239, 121, 56),
        "hydro": (75, 170, 230),
        "anemo": (116, 214, 180),
        "electro": (175, 130, 230),
        "dendro": (150, 200, 60),
        "cryo": (160, 220, 235),
        "geo": (240, 190, 70),
    }

    BOARD_CENTER_X: int = 443
    BOARD_CHARACTER_XS: list[int] = [345, 445, 545]
    BOARD_CHARACTER_SIZE: tuple[int, int] = (84, 112)
    OPPONENT_ROW_Y: int = 128
    PLAYER_ROW_Y: int = 388
    ACTIVE_CHARACTER_OFFSET: int = 20
    HAND_CARD_SIZE: tuple[int, int] = (68, 94)
    HAND_Y: int = 530
    HAND_RAISED_Y: int = 490
    HAND_SPACING: int = 72
    OPPONENT_HAND_CARD_SIZE: tuple[int, int] = (56, 78)
    OPPONENT_HAND_Y: int = 8
    OPPONENT_HAND_SPACING: int = 52
    BOARD_DICE_SIZE: tuple[int, int] = (24, 24)
    BOARD_DICE_X: int = 838
    BOARD_DICE_TOP_Y: int = 162
    BOARD_DICE_SPACING: int = 26
    BOARD_DICE_PER_COLUMN: int = 8
    BOT_THINK_MS: int = 1200
    ROUND_END_DELAY_MS: int = 1500
    BANNER_MS: int = 1400
    CARDS_DRAWN_PER_ROUND: int = 2

    @final
    def __init__(self) -> None:
        if not GlobalHolder.player:
            raise ValueError("Player not found")

        # Create both battle sides and the engine that resolves combat.
        self.battle_player: BattlePlayer = BattlePlayer(player=GlobalHolder.player, deck=GlobalHolder.player.selected_deck)
        self.other_battle_player: OtherBattlePlayer = OtherBattlePlayer(bot=True)
        self.engine: CombatEngine = CombatEngine(player=self.battle_player, opponent=self.other_battle_player)

        # Both sides are dealt 4 action cards before the selector opens.
        self.battle_player.draw_starting_hand(number_of_cards=4)
        self.other_battle_player.draw_starting_hand(number_of_cards=4)

        # The battle is split into sections, the same way Auth uses auth_sub_events.
        self.battle_sub_events: dict[BattleSubEvents, bool] = {
            "action_card_selector": True,
            "character_selector": False,
            "first_player_flip": False,
            "roll": False,
            "action": False,
            "game_over": False,
        }

        self.selected_card_indexes: set[int] = set()
        self.hand_confirmed: bool = False

        self.selected_character_index: int | None = None
        self.character_confirmed: bool = False

        self.first_player: BattlePlayer | None = None
        self.flip_start_ms: int | None = None
        self.flip_half_turns: int = 0
        self.flip_finished: bool = False

        self.round_number: int = 1
        self.kept_dice_indexes: set[int] = set()
        self.dice_rerolled: bool = False
        self.dice_roll_start_ms: int | None = None
        self.dice_last_swap_ms: int = 0
        self.rolling_dice_indexes: list[int] = []
        self.bot_rerolled_count: int = 0

        self.current_turn: BattlePlayer | None = None
        # Players who have pressed "end round", in the order they declared.
        self.declared_end: list[BattlePlayer] = []
        self.bot_action_due_ms: int | None = None
        self.round_end_due_ms: int | None = None
        self.banner_until_ms: int = 0
        self.selected_hand_index: int | None = None
        self.choosing_new_active: BattlePlayer | None = None
        self.pending_pass: bool = False
        self.winner: BattlePlayer | None = None

        super().__init__()
        self.change_page(new_state="test")

    def selector_is_open(self) -> bool:
        return self.battle_sub_events["action_card_selector"] and not self.hand_confirmed

    def character_selector_is_open(self) -> bool:
        return self.battle_sub_events["character_selector"] and not self.character_confirmed

    def _flip_is_spinning(self) -> bool:
        return self.battle_sub_events["first_player_flip"] and not self.flip_finished

    def _prepare_is_open(self) -> bool:
        return (self.battle_sub_events["action_card_selector"] or self.battle_sub_events["character_selector"] or self.battle_sub_events["first_player_flip"]) and not self._flip_is_spinning()

    def _roll_phase_open(self) -> bool:
        return self.battle_sub_events["roll"]

    def _dice_are_rolling(self) -> bool:
        return self._roll_phase_open() and self.dice_roll_start_ms is not None

    def _dice_selector_is_open(self) -> bool:
        return self._roll_phase_open() and not self.dice_rerolled and not self._dice_are_rolling()

    def _confirm_is_active(self) -> bool:
        return self._prepare_is_open() or (self._roll_phase_open() and not self._dice_are_rolling())

    def _action_phase_open(self) -> bool:
        return self.battle_sub_events["action"]

    def _is_player_turn(self) -> bool:
        return (
            self._action_phase_open()
            and not self.battle_sub_events["game_over"]
            and self.choosing_new_active is None
            and self.round_end_due_ms is None
            and self.current_turn is self.battle_player
            and self.battle_player not in self.declared_end
        )

    def _player_characters_clickable(self) -> bool:
        return self._action_phase_open() and not self.battle_sub_events["game_over"] and (self._is_player_turn() or self.choosing_new_active is self.battle_player)

    @override
    def init(self) -> None:
        super().init()
        # Change the background of the battle
        self.init_background(image_key="battle_bg1")

        # Starting hand selector labels
        self.action_card_selector_title: TextImageComponent = TextImageComponent(text_option=TextOption(text="Starting Hand", size=32, align="center", bold=True, color=(255, 250, 250)), base_pos=(480, 108), anchor="center") # pyright: ignore[reportUninitializedInstanceVariable]
        self.action_card_selector_subtitle: TextImageComponent = TextImageComponent(text_option=TextOption(text="Select card(s) to switch", size=14, align="center", color=(230, 226, 216)), base_pos=(480, 140), anchor="center") # pyright: ignore[reportUninitializedInstanceVariable]
        self.opponent_label: TextImageComponent = TextImageComponent(text_option=TextOption(text="Opponent", size=14, align="center", color=(230, 226, 216)), base_pos=(270, 42), anchor="center") # pyright: ignore[reportUninitializedInstanceVariable]

        # End round button sits on the left of the board
        self.end_round_button: Button = Button(image_option=ImageOption(image=pygame.transform.smoothscale(surface=self.load_image(image_key="end_of_turn"), size=(56, 56))), text_option=TextOption(text="", size=0), position=(42, 270), anchor="center") # pyright: ignore[reportUninitializedInstanceVariable]
        self.end_round_button.on_activate = lambda: self.declare_end(player=self.battle_player)

        self.starting_hand_buttons: list[Button] = [] # pyright: ignore[reportUninitializedInstanceVariable]
        self.opponent_hidden_cards: list[ImageComponent] = [] # pyright: ignore[reportUninitializedInstanceVariable]
        self._build_starting_hand()

        # Character selector labels
        self.character_selector_title: TextImageComponent = TextImageComponent(text_option=TextOption(text="Choose Your Active Character", size=28, align="center", bold=True, color=(255, 250, 250)), base_pos=(480, 128), anchor="center") # pyright: ignore[reportUninitializedInstanceVariable]
        self.character_selector_subtitle: TextImageComponent = TextImageComponent(text_option=TextOption(text="Select the character that will fight first", size=14, align="center", color=(230, 226, 216)), base_pos=(480, 158), anchor="center") # pyright: ignore[reportUninitializedInstanceVariable]
        self.opponent_character_label: TextImageComponent = TextImageComponent(text_option=TextOption(text="Opponent", size=14, align="center", color=(230, 226, 216)), base_pos=(330, 52), anchor="center") # pyright: ignore[reportUninitializedInstanceVariable]

        self.character_buttons: list[Button] = [] # pyright: ignore[reportUninitializedInstanceVariable]
        self.character_name_labels: list[TextImageComponent] = [] # pyright: ignore[reportUninitializedInstanceVariable]
        self.character_info_labels: list[TextImageComponent] = [] # pyright: ignore[reportUninitializedInstanceVariable]
        self.opponent_character_images: list[ImageComponent] = [] # pyright: ignore[reportUninitializedInstanceVariable]
        self._build_character_selector()

        # Coin flip components
        self.flip_title: TextImageComponent = TextImageComponent(text_option=TextOption(text="Who Goes First?", size=32, align="center", bold=True, color=(255, 250, 250)), base_pos=(480, 108), anchor="center") # pyright: ignore[reportUninitializedInstanceVariable]
        self.flip_subtitle: TextImageComponent = TextImageComponent(text_option=TextOption(text="Flipping...", size=14, align="center", color=(230, 226, 216)), base_pos=(480, 140), anchor="center") # pyright: ignore[reportUninitializedInstanceVariable]
        self.flip_result_text: TextImageComponent = TextImageComponent(text_option=TextOption(text="", size=30, align="center", bold=True, color=(255, 214, 90)), base_pos=(480, 400), anchor="center") # pyright: ignore[reportUninitializedInstanceVariable]
        self.coin_faces: dict[str, Surface] = {
            "player": self._coin_face_surface(label="YOU", fill=(52, 104, 186)),
            "opponent": self._coin_face_surface(label="OPPONENT", fill=(168, 52, 60)),
        }
        self.coin_image: ImageComponent = ImageComponent(image_option=self.coin_faces["player"], base_pos=self.COIN_CENTER, anchor="center") # pyright: ignore[reportUninitializedInstanceVariable]
        self.flip_player_label: TextImageComponent = TextImageComponent(text_option=TextOption(text="You", size=16, align="center", bold=True, color=(255, 250, 240)), base_pos=(220, 372), anchor="center") # pyright: ignore[reportUninitializedInstanceVariable]
        self.flip_opponent_label: TextImageComponent = TextImageComponent(text_option=TextOption(text="Opponent", size=16, align="center", bold=True, color=(255, 250, 240)), base_pos=(740, 372), anchor="center") # pyright: ignore[reportUninitializedInstanceVariable]
        self.flip_player_character: ImageComponent | None = None
        self.flip_opponent_character: ImageComponent | None = None

        # Roll phase labels and dice buttons
        self.roll_title: TextImageComponent = TextImageComponent(text_option=TextOption(text="Roll Phase", size=32, align="center", bold=True, color=(255, 250, 250)), base_pos=(480, 92), anchor="center") # pyright: ignore[reportUninitializedInstanceVariable]
        self.roll_round_label: TextImageComponent = TextImageComponent(text_option=TextOption(text="Round 1", size=13, align="center", color=(196, 168, 110)), base_pos=(480, 122), anchor="center") # pyright: ignore[reportUninitializedInstanceVariable]
        self.roll_subtitle: TextImageComponent = TextImageComponent(text_option=TextOption(text="Rolling...", size=14, align="center", color=(230, 226, 216)), base_pos=(480, 148), anchor="center") # pyright: ignore[reportUninitializedInstanceVariable]
        self.roll_opponent_label: TextImageComponent = TextImageComponent(text_option=TextOption(text="", size=13, align="center", color=(214, 208, 196)), base_pos=(480, 412), anchor="center") # pyright: ignore[reportUninitializedInstanceVariable]
        self.die_faces: dict[str, Surface] = {face: self._die_face_surface(face=face) for face in DIE_FACES}
        self.dice_buttons: list[Button] = [] # pyright: ignore[reportUninitializedInstanceVariable]
        for index, position in enumerate(self.DIE_POSITIONS):
            button: Button = Button(image_option=ImageOption(image=self.die_faces["omni"]), text_option=TextOption(text="", size=0), position=position, anchor="center")
            button.on_activate = lambda index=index: self._toggle_kept_die(index=index)
            self.dice_buttons.append(button)

        self._init_battlefield()

        # Shared confirm button used by prepare and roll
        self.confirm_hand_button: Button = Button(image_option=ImageOption(image=self.load_image(image_key="button1")), text_option=TextOption(text="Confirm", size=16), position=(480, 470), anchor="center") # pyright: ignore[reportUninitializedInstanceVariable]
        self.confirm_hand_button.on_activate = self.on_confirm
        return

    def _init_battlefield(self) -> None:
        self.board_player_character_buttons: list[Button] = []
        self.board_opponent_characters: list[ImageComponent] = []
        self.board_opponent_hand: list[ImageComponent] = []
        self.board_dice: list[ImageComponent] = []

        self.board_dice_counter: ImageComponent = ImageComponent(image_option=pygame.transform.smoothscale(surface=self.load_image(image_key="dice_number"), size=(40, 42)), base_pos=(self.BOARD_DICE_X, 128), anchor="center")
        self.board_dice_count_text: TextImageComponent = TextImageComponent(text_option=TextOption(text="0", size=16, align="center", bold=True, color=(255, 250, 240)), base_pos=(self.BOARD_DICE_X, 127), anchor="center")

        blank_character: Surface = pygame.Surface(size=self.BOARD_CHARACTER_SIZE, flags=pygame.SRCALPHA)
        for index in range(3):
            button: Button = Button(image_option=ImageOption(image=blank_character.copy()), text_option=TextOption(text="", size=0), position=(self.BOARD_CHARACTER_XS[index], self.PLAYER_ROW_Y), anchor="center")
            button.on_activate = lambda index=index: self._on_player_character(index=index)
            self.board_player_character_buttons.append(button)

        # Hand slots are created once because event listeners can't be removed; unused slots stay hidden.
        hidden: Surface = pygame.transform.smoothscale(surface=self._hidden_card_surface(), size=self.HAND_CARD_SIZE)
        self.hand_slot_buttons: list[Button] = []
        for index in range(MAX_HAND_SIZE):
            button = Button(image_option=ImageOption(image=hidden), text_option=TextOption(text="", size=0), position=(self.BOARD_CENTER_X, self.HAND_Y), anchor="center")
            button.on_activate = lambda index=index: self._on_hand_card(index=index)
            self.hand_slot_buttons.append(button)

        attack_image: Surface = pygame.transform.smoothscale(surface=self.load_image(image_key="attack_placeholder"), size=(52, 51))
        self.skill_buttons: dict[str, Button] = {}
        for skill_key, label, x in (("burst", "Burst", 672), ("skill", "Skill", 737), ("normal", "Attack", 802)):
            button = Button(image_option=ImageOption(image=attack_image), text_option=TextOption(text=label, size=10, bold=True, color=(255, 246, 225)), position=(x, 436), anchor="center")
            button.on_activate = lambda skill_key=skill_key: self._on_skill_pressed(skill_key=skill_key)
            self.skill_buttons[skill_key] = button

        self.turn_label: TextImageComponent = TextImageComponent(text_option=TextOption(text="", size=11, align="center", bold=True, color=(255, 214, 90)), base_pos=(42, 312), anchor="center")
        self.player_declared_label: TextImageComponent = TextImageComponent(text_option=TextOption(text="Round ended", size=12, align="center", bold=True, color=(236, 120, 120)), base_pos=(250, self.PLAYER_ROW_Y), anchor="center")
        self.opponent_declared_label: TextImageComponent = TextImageComponent(text_option=TextOption(text="Round ended", size=12, align="center", bold=True, color=(236, 120, 120)), base_pos=(250, self.OPPONENT_ROW_Y), anchor="center")

        banner_bg: Surface = pygame.Surface(size=(420, 54), flags=pygame.SRCALPHA)
        _ = pygame.draw.rect(surface=banner_bg, color=(20, 24, 38, 215), rect=banner_bg.get_rect(), border_radius=14)
        _ = pygame.draw.rect(surface=banner_bg, color=(196, 168, 110), rect=banner_bg.get_rect(), width=2, border_radius=14)
        self.banner_bg: ImageComponent = ImageComponent(image_option=banner_bg, base_pos=(480, 270), anchor="center")
        self.banner_text: TextImageComponent = TextImageComponent(text_option=TextOption(text="", size=20, align="center", bold=True, color=(255, 250, 240)), base_pos=(480, 270), anchor="center")
        self.status_line: TextImageComponent = TextImageComponent(text_option=TextOption(text="", size=11, align="center", color=(230, 226, 216), max_width=420), base_pos=(443, 248), anchor="center")
        self.game_over_title: TextImageComponent = TextImageComponent(text_option=TextOption(text="", size=36, align="center", bold=True, color=(255, 214, 90)), base_pos=(480, 250), anchor="center")
        self.game_over_subtitle: TextImageComponent = TextImageComponent(text_option=TextOption(text="All characters on one side have fallen", size=14, align="center", color=(230, 226, 216)), base_pos=(480, 292), anchor="center")
        return

    @staticmethod
    def _fit_surface(surface: Surface, size: tuple[int, int]) -> Surface:
        # The Card draw helpers already apply the screen scale, so undo it here and let ImageComponent rescale.
        scale: float = GlobalHolder.scale or 1
        if scale != 1:
            base_size: tuple[int, int] = (max(1, round(surface.get_width() / scale)), max(1, round(surface.get_height() / scale)))
            surface = pygame.transform.smoothscale(surface=surface, size=base_size)
        return pygame.transform.smoothscale(surface=surface, size=size)

    def _card_surface(self, card: ActionCard, size: tuple[int, int] = (100, 138)) -> Surface:
        die_needed: int = int(card.cost.get("unaligned", 0))
        surface: Surface = ActionCard.draw_action_card(card_key=card.image_key, die_needed=die_needed)
        return self._fit_surface(surface=surface, size=size)

    def _character_surface(self, character_key: str, size: tuple[int, int], current_hp: int | None = None, current_energy: int | None = None, applied_element: str | None = None, defeated: bool = False) -> Surface:
        surface: Surface = CharacterCard.draw_battle_card(character_key=character_key, current_hp=current_hp, current_energy=current_energy)
        fitted: Surface = self._fit_surface(surface=surface, size=size)
        if applied_element and applied_element != "omni":
            icon: Surface = pygame.transform.smoothscale(surface=GlobalHolder.load_image(image_key=f"element_{applied_element}"), size=(18, 18))
            _ = fitted.blit(source=icon, dest=(fitted.get_width() - 22, 4))
        if defeated:
            veil: Surface = pygame.Surface(size=fitted.get_size(), flags=pygame.SRCALPHA)
            _ = veil.fill(color=(12, 14, 22, 150))
            _ = fitted.blit(source=veil, dest=(0, 0))
        return fitted

    def _character_board_surface(self, character: CharacterCard) -> Surface:
        return self._character_surface(character_key=character.character_id, size=self.BOARD_CHARACTER_SIZE, current_hp=character.current_hp, current_energy=character.current_energy, applied_element=character.applied_element, defeated=not character.is_alive)

    def _coin_face_surface(self, label: str, fill: tuple[int, int, int]) -> Surface:
        surface: Surface = pygame.Surface(size=self.COIN_SIZE, flags=pygame.SRCALPHA)
        center: tuple[int, int] = surface.get_rect().center
        radius: int = min(self.COIN_SIZE) // 2
        _ = pygame.draw.circle(surface=surface, color=(196, 168, 110), center=center, radius=radius)
        _ = pygame.draw.circle(surface=surface, color=fill, center=center, radius=radius - 7)
        _ = pygame.draw.circle(surface=surface, color=(230, 206, 150), center=center, radius=radius - 14, width=2)
        text: Surface = GlobalHolder.font_manager.render(text=label, size=24 if len(label) <= 3 else 15, color=(255, 250, 240), bold=True)
        _ = surface.blit(source=text, dest=text.get_rect(center=center))
        return surface

    def _die_face_surface(self, face: str) -> Surface:
        surface: Surface = pygame.Surface(size=self.DIE_SIZE, flags=pygame.SRCALPHA)
        rect = surface.get_rect()
        color: tuple[int, int, int] = self.DIE_COLORS[face]
        size = self.DIE_SIZE[0]
        corner = max(8, round(size * 0.19))
        _ = pygame.draw.rect(surface=surface, color=(34, 40, 60), rect=rect, border_radius=corner)
        _ = pygame.draw.rect(surface=surface, color=color, rect=rect, width=max(3, round(size * 0.05)), border_radius=corner)

        if face == "omni":
            # There is no Omni icon asset, so draw a four-point star in its place.
            cx, cy = rect.center
            points: list[tuple[float, float]] = []
            for i in range(8):
                radius = size * (0.33 if i % 2 == 0 else 0.11)
                angle = math.pi / 4 * i - math.pi / 2
                points.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
            _ = pygame.draw.polygon(surface=surface, color=color, points=points)
            _ = pygame.draw.circle(surface=surface, color=(255, 255, 255), center=rect.center, radius=max(3, round(size * 0.06)))
        else:
            icon_size = max(24, round(size * 0.76))
            icon: Surface = pygame.transform.smoothscale(surface=GlobalHolder.load_image(image_key=f"element_{face}"), size=(icon_size, icon_size))
            _ = surface.blit(source=icon, dest=icon.get_rect(center=rect.center))
        return surface

    def _hidden_card_surface(self) -> Surface:
        surface: Surface = pygame.Surface(size=(64, 88), flags=pygame.SRCALPHA)
        rect = surface.get_rect()
        _ = pygame.draw.rect(surface=surface, color=(36, 44, 68), rect=rect, border_radius=8)
        _ = pygame.draw.rect(surface=surface, color=(196, 168, 110), rect=rect, width=3, border_radius=8)
        _ = pygame.draw.rect(surface=surface, color=(58, 70, 102), rect=rect.inflate(-16, -18), border_radius=6)
        return surface

    def _build_starting_hand(self) -> None:
        player_positions: list[tuple[int, int]] = [(246, 300), (402, 300), (558, 300), (714, 300)]
        opponent_positions: list[tuple[int, int]] = [(360, 42), (440, 42), (520, 42), (600, 42)]
        hidden_surface: Surface = self._hidden_card_surface()

        self.starting_hand_buttons.clear()
        for index, card in enumerate(self.battle_player.hand):
            if index >= len(player_positions):
                break
            button: Button = Button(
                image_option=ImageOption(image=self._card_surface(card=card)),
                text_option=TextOption(text=card.name, size=10, color=(255, 250, 240), align="center", max_width=88),
                position=player_positions[index],
                anchor="center",
            )
            button.on_activate = lambda index=index: self._toggle_starting_card(index=index)
            self.starting_hand_buttons.append(button)

        self.opponent_hidden_cards.clear()
        for index in range(len(self.other_battle_player.hand)):
            if index >= len(opponent_positions):
                break
            self.opponent_hidden_cards.append(ImageComponent(image_option=hidden_surface.copy(), base_pos=opponent_positions[index], anchor="center"))
        return

    def _build_character_selector(self) -> None:
        player_positions: list[tuple[int, int]] = [(320, 300), (480, 300), (640, 300)]
        opponent_positions: list[tuple[int, int]] = [(410, 52), (480, 52), (550, 52)]

        self.character_buttons.clear()
        self.character_name_labels.clear()
        self.character_info_labels.clear()
        for index, character in enumerate(self.battle_player.list_of_characters[:len(player_positions)]):
            x, y = player_positions[index]
            button: Button = Button(image_option=ImageOption(image=self._character_surface(character_key=character.character_id, size=(116, 154))), text_option=TextOption(text="", size=0), position=(x, y), anchor="center")
            button.on_activate = lambda index=index: self._select_character(index=index)
            self.character_buttons.append(button)
            self.character_name_labels.append(TextImageComponent(text_option=TextOption(text=character.name, size=16, align="center", bold=True, color=(255, 250, 240)), base_pos=(x, y + 92), anchor="center"))
            self.character_info_labels.append(TextImageComponent(text_option=TextOption(text=f"{character.element.title()}  |  {character.weapon.title()}  |  {character.max_hp} HP", size=11, align="center", color=(214, 208, 196)), base_pos=(x, y + 112), anchor="center"))

        self.opponent_character_images.clear()
        for index, character in enumerate(self.other_battle_player.list_of_characters[:len(opponent_positions)]):
            self.opponent_character_images.append(ImageComponent(image_option=self._character_surface(character_key=character.character_id, size=(54, 72)), base_pos=opponent_positions[index], anchor="center"))
        return

    def _clear_battle_sub_events(self) -> None:
        # Turn every battle section off before enabling the next one.
        for key in self.battle_sub_events:
            self.battle_sub_events[key] = False

    def set_character_selector(self) -> None:
        # Move from the starting hand step to the active character step.
        self._clear_battle_sub_events()
        self.battle_sub_events["character_selector"] = True
        self.confirm_hand_button.text_surface.set_text(text="Confirm")
        return

    def set_first_player_flip(self) -> None:
        # Move from character select to the coin flip.
        self._clear_battle_sub_events()
        self.battle_sub_events["first_player_flip"] = True
        self.confirm_hand_button.text_surface.set_text(text="Confirm")
        self._start_first_player_flip()
        return

    def set_roll_phase(self) -> None:
        # Move from prepare into the dice roll.
        self._clear_battle_sub_events()
        self.battle_sub_events["roll"] = True
        self._start_roll_phase()
        return

    def set_action_phase(self) -> None:
        # Move from the roll into the main battlefield.
        self._clear_battle_sub_events()
        self.battle_sub_events["action"] = True
        self.confirm_hand_button.text_surface.set_text(text="Confirm")
        self.declared_end.clear()
        self.round_end_due_ms = None
        self.selected_hand_index = None
        self.choosing_new_active = None
        self.pending_pass = False
        logs: list[str] = self.engine.start_action_phase()
        self._refresh_battlefield()
        self._begin_turn(player=self.first_player or self.battle_player)
        if logs:
            self._show_banner(text=logs[-1])
        return

    def _toggle_starting_card(self, index: int) -> None:
        if index in self.selected_card_indexes:
            self.selected_card_indexes.remove(index)
        else:
            self.selected_card_indexes.add(index)

        count: int = len(self.selected_card_indexes)
        if count == 0:
            text = "Select card(s) to switch"
        elif count == 1:
            text = "1 card selected"
        else:
            text = f"{count} cards selected"
        self.action_card_selector_subtitle.set_text(text=text)

    def _select_character(self, index: int) -> None:
        self.selected_character_index = index
        character: CharacterCard = self.battle_player.list_of_characters[index]
        self.character_selector_subtitle.set_text(text=f"{character.name} selected")

    def _refresh_starting_hand(self) -> None:
        for button, card in zip(self.starting_hand_buttons, self.battle_player.hand):
            button.surface._raw_image = self._card_surface(card=card)
            button.surface.outline_image = None
            button.text_surface.text_option.set_text(text=card.name)
            button.surface.update_layout()
            button.text_surface.update_layout()

    def on_confirm(self) -> None:
        # The same Confirm button is reused for prepare and roll.
        if self._roll_phase_open():
            self.advance_roll_phase()
        else:
            self.advance_prepare()

    def advance_prepare(self) -> None:
        if self.battle_sub_events["action_card_selector"]:
            if not self.hand_confirmed:
                self.confirm_starting_hand()
            else:
                self.set_character_selector()
        elif self.battle_sub_events["character_selector"]:
            if not self.character_confirmed:
                self.confirm_active_character()
            else:
                self.set_first_player_flip()
        elif self.battle_sub_events["first_player_flip"] and self.flip_finished:
            self.set_roll_phase()

    def confirm_starting_hand(self) -> None:
        if self.hand_confirmed:
            return

        indexes: list[int] = sorted(self.selected_card_indexes)
        self.battle_player.switch_cards(indexes=indexes)
        # The bot also switches, but its cards stay face down.
        self.other_battle_player.switch_random_cards()
        self.selected_card_indexes.clear()
        self._refresh_starting_hand()
        self.hand_confirmed = True

        if len(indexes) == 0:
            message = "No cards switched"
        elif len(indexes) == 1:
            message = "1 card switched"
        else:
            message = f"{len(indexes)} cards switched"
        self.action_card_selector_subtitle.set_text(text=message)
        self.confirm_hand_button.text_surface.set_text(text="Done")

    def confirm_active_character(self) -> None:
        if self.character_confirmed:
            return
        if self.selected_character_index is None:
            self.character_selector_subtitle.set_text(text="Select a character first")
            return

        self.battle_player.set_active_character(index=self.selected_character_index)
        # The bot chooses at the same time, so its choice is only revealed after the player confirms.
        self.other_battle_player.choose_random_active_character()
        self.character_confirmed = True

        player_character: CharacterCard | None = self.battle_player.active_character
        bot_character: CharacterCard | None = self.other_battle_player.active_character
        if player_character and bot_character:
            self.character_selector_subtitle.set_text(text=f"{player_character.name} vs {bot_character.name}")
        self.confirm_hand_button.text_surface.set_text(text="Start")

    def _start_first_player_flip(self) -> None:
        self.first_player = random.choice([self.battle_player, self.other_battle_player])
        # The coin shows the player's face every even half turn, so the parity decides where it lands.
        self.flip_half_turns = 12 if self.first_player is self.battle_player else 13
        self.flip_start_ms = pygame.time.get_ticks()
        self.flip_finished = False
        self.flip_subtitle.set_text(text="Flipping...")
        self.flip_result_text.set_text(text="")

        player_character: CharacterCard | None = self.battle_player.active_character
        bot_character: CharacterCard | None = self.other_battle_player.active_character
        if player_character:
            self.flip_player_character = ImageComponent(image_option=self._character_surface(character_key=player_character.character_id, size=(116, 154)), base_pos=(220, 270), anchor="center")
            self.flip_player_character.update_layout()
        if bot_character:
            self.flip_opponent_character = ImageComponent(image_option=self._character_surface(character_key=bot_character.character_id, size=(116, 154)), base_pos=(740, 270), anchor="center")
            self.flip_opponent_character.update_layout()

    def _update_first_player_flip(self) -> None:
        if self.flip_start_ms is None:
            return
        progress: float = min(1.0, (pygame.time.get_ticks() - self.flip_start_ms) / self.FLIP_DURATION_MS)
        # Ease-out cubic so the coin spins fast at first and slows down as it lands.
        eased: float = 1 - (1 - progress) ** 3
        angle: float = eased * self.flip_half_turns * math.pi

        face_key: str = "player" if round(angle / math.pi) % 2 == 0 else "opponent"
        face: Surface = self.coin_faces[face_key]
        width: int = max(2, round(face.get_width() * abs(math.cos(angle))))
        self.coin_image._raw_image = pygame.transform.smoothscale(surface=face, size=(width, face.get_height()))
        lift: int = round(math.sin(progress * math.pi) * 70)
        self.coin_image._raw_base_pos = (self.COIN_CENTER[0], self.COIN_CENTER[1] - lift)
        self.coin_image.update_layout()

        if progress >= 1.0:
            self._finish_first_player_flip()

    def _finish_first_player_flip(self) -> None:
        self.flip_finished = True
        player_first: bool = self.first_player is self.battle_player
        self.flip_subtitle.set_text(text="The coin has landed")
        self.flip_result_text.text_option.set_color(color=(255, 214, 90) if player_first else (236, 120, 120))
        self.flip_result_text.set_text(text="You go first!" if player_first else "Opponent goes first!")
        self.confirm_hand_button.text_surface.set_text(text="Start Battle")

    def _start_roll_phase(self) -> None:
        self.kept_dice_indexes.clear()
        self.dice_rerolled = False
        self.roll_round_label.set_text(text=f"Round {self.round_number}")
        self.roll_subtitle.set_text(text="Rolling...")
        self.roll_opponent_label.set_text(text="")
        self.confirm_hand_button.text_surface.set_text(text="Reroll")

        self.battle_player.roll_dice()
        # The bot decides straight away; only the outcome is shown once the player has finished.
        self.other_battle_player.roll_dice()
        bot_kept: list[int] = self.other_battle_player.choose_dice_to_keep()
        self.bot_rerolled_count = len(self.other_battle_player.reroll_dice(indexes=[i for i in range(len(self.other_battle_player.dice)) if i not in bot_kept]))
        self.other_battle_player.sort_dice()
        self._start_dice_animation(indexes=list(range(len(self.battle_player.dice))))

    def _toggle_kept_die(self, index: int) -> None:
        if index in self.kept_dice_indexes:
            self.kept_dice_indexes.remove(index)
        else:
            self.kept_dice_indexes.add(index)

        kept: int = len(self.kept_dice_indexes)
        total: int = len(self.battle_player.dice)
        if kept == 0:
            text = "Select the dice you want to keep. The rest will be rerolled."
        else:
            text = f"Keeping {kept} - rerolling {total - kept}"
        self.roll_subtitle.set_text(text=text)
        self.confirm_hand_button.text_surface.set_text(text="Keep All" if kept == total else "Reroll")

    def advance_roll_phase(self) -> None:
        if self._dice_are_rolling():
            return
        if not self.dice_rerolled:
            self.confirm_reroll()
        else:
            self.set_action_phase()

    def confirm_reroll(self) -> None:
        to_reroll: list[int] = [index for index in range(len(self.battle_player.dice)) if index not in self.kept_dice_indexes]
        rerolled: list[int] = self.battle_player.reroll_dice(indexes=to_reroll)
        self.dice_rerolled = True
        self.kept_dice_indexes.clear()
        if rerolled:
            self.roll_subtitle.set_text(text="Rerolling...")
            self._start_dice_animation(indexes=rerolled)
        else:
            self._finish_dice_animation()

    def _other(self, player: BattlePlayer) -> BattlePlayer:
        return self.other_battle_player if player is self.battle_player else self.battle_player

    def _show_banner(self, text: str) -> None:
        self.banner_text.set_text(text=text)
        self.banner_until_ms = pygame.time.get_ticks() + self.BANNER_MS

    def _begin_turn(self, player: BattlePlayer, announce: bool = True) -> None:
        self.current_turn = player
        if player is self.battle_player:
            self.bot_action_due_ms = None
            self.turn_label.set_text(text="Your Turn")
            if announce:
                self._show_banner(text="Your Turn")
        else:
            self.bot_action_due_ms = pygame.time.get_ticks() + self.BOT_THINK_MS
            self.turn_label.set_text(text="Opponent's Turn")
            if announce:
                self._show_banner(text="Opponent's Turn")

    def declare_end(self, player: BattlePlayer) -> None:
        """The player can't (or won't) act any more this round; the other player keeps acting until they also declare."""
        if self.battle_sub_events["game_over"] or player in self.declared_end or player is not self.current_turn or self.round_end_due_ms is not None:
            return
        self.declared_end.append(player)
        is_user: bool = player is self.battle_player
        self._show_banner(text="You ended the round" if is_user else "Opponent ended the round")

        other: BattlePlayer = self._other(player=player)
        if other in self.declared_end:
            self._schedule_round_end()
        else:
            self._begin_turn(player=other)
            # Keep the "ended the round" banner visible instead of replacing it with the turn banner.
            self._show_banner(text="You ended the round" if is_user else "Opponent ended the round")

    def _bot_take_turn(self) -> None:
        self.bot_action_due_ms = None
        if self.battle_sub_events["game_over"] or self.round_end_due_ms is not None:
            return
        if self.choosing_new_active is self.other_battle_player:
            self._auto_choose_active(side=self.other_battle_player)
            return

        kind, skill_key, hand_index, target_index = self.engine.decide_bot_action(bot=self.other_battle_player)
        if kind == "card" and hand_index is not None:
            result: CombatResult = self.engine.play_card(user=self.other_battle_player, hand_index=hand_index, target_index=target_index)
        elif kind == "skill" and skill_key is not None:
            result = self.engine.use_skill(user=self.other_battle_player, skill_key=skill_key)
        elif kind == "switch" and target_index is not None:
            result = self.engine.switch_character(user=self.other_battle_player, index=target_index)
        else:
            self.declare_end(player=self.other_battle_player)
            return
        self._resolve_action(result=result, actor=self.other_battle_player)

    def _schedule_round_end(self) -> None:
        self.current_turn = None
        self.bot_action_due_ms = None
        self.round_end_due_ms = pygame.time.get_ticks() + self.ROUND_END_DELAY_MS
        self.turn_label.set_text(text="")
        self._show_banner(text=f"Round {self.round_number} over")

    def _end_round(self) -> None:
        self.round_end_due_ms = None
        self.battle_sub_events["action"] = False
        result: CombatResult = self.engine.end_phase()
        self._apply_result(result=result)
        if result.winner is not None:
            return
        self._ensure_actives()
        # Whoever declared first acts first next round.
        self.first_player = self.declared_end[0] if self.declared_end else self.first_player
        self.round_number += 1
        self.battle_player.draw_to_hand(number_of_cards=self.CARDS_DRAWN_PER_ROUND)
        self.other_battle_player.draw_to_hand(number_of_cards=self.CARDS_DRAWN_PER_ROUND)
        self.set_roll_phase()

    def _on_skill_pressed(self, skill_key: str) -> None:
        if not self._is_player_turn():
            return
        result: CombatResult = self.engine.use_skill(user=self.battle_player, skill_key=skill_key)  # type: ignore[arg-type]
        self._resolve_action(result=result, actor=self.battle_player)

    def _on_hand_card(self, index: int) -> None:
        if not self._is_player_turn() or index >= len(self.battle_player.hand):
            return
        if self.selected_hand_index == index:
            self.selected_hand_index = None
            self._show_banner(text="Card deselected")
            return
        card: ActionCard = self.battle_player.hand[index]
        if self.engine.card_needs_target(card=card):
            self.selected_hand_index = index
            self._show_banner(text=f"Choose a character for {card.name}")
            return
        self.selected_hand_index = None
        result: CombatResult = self.engine.play_card(user=self.battle_player, hand_index=index, target_index=None)
        self._resolve_action(result=result, actor=self.battle_player)

    def _on_player_character(self, index: int) -> None:
        if self.choosing_new_active is self.battle_player:
            result: CombatResult = self.engine.switch_character(user=self.battle_player, index=index, free=True)
            if result.ok:
                self.choosing_new_active = None
                self._refresh_battlefield()
                self._show_banner(text=result.message)
                if self.pending_pass:
                    self.pending_pass = False
                    self._pass_turn(actor=self.current_turn or self.battle_player)
            else:
                self._show_banner(text=result.message)
            return
        if not self._is_player_turn():
            return
        if self.selected_hand_index is not None:
            result = self.engine.play_card(user=self.battle_player, hand_index=self.selected_hand_index, target_index=index)
            self.selected_hand_index = None
            self._resolve_action(result=result, actor=self.battle_player)
            return
        result = self.engine.switch_character(user=self.battle_player, index=index)
        self._resolve_action(result=result, actor=self.battle_player)

    def _resolve_action(self, result: CombatResult, actor: BattlePlayer) -> None:
        self._apply_result(result=result)
        if not result.ok or result.winner is not None:
            return
        if result.need_active is not None:
            self.pending_pass = result.combat_action
            self._request_active(side=result.need_active)
            return
        if result.combat_action:
            self._pass_turn(actor=actor)
        elif actor is self.other_battle_player:
            self.bot_action_due_ms = pygame.time.get_ticks() + 700

    def _apply_result(self, result: CombatResult) -> None:
        if result.ok and result.logs:
            text: str = result.logs[-1]
            if result.reaction:
                text = f"{result.reaction}! {text}"
            self._show_banner(text=text)
        elif not result.ok:
            self._show_banner(text=result.message)
        self._refresh_battlefield()
        if result.winner is not None:
            self._finish_game(winner=result.winner)

    def _pass_turn(self, actor: BattlePlayer) -> None:
        if self.winner is not None or self.round_end_due_ms is not None:
            return
        other: BattlePlayer = self._other(player=actor)
        if other in self.declared_end:
            self._begin_turn(player=actor, announce=False)
        else:
            self._begin_turn(player=other, announce=False)

    def _request_active(self, side: BattlePlayer) -> None:
        alive: list[int] = side.alive_indexes()
        if not alive:
            winner: BattlePlayer | None = self.engine.winner()
            if winner:
                self._finish_game(winner=winner)
            return
        if len(alive) == 1 or side is self.other_battle_player:
            self._auto_choose_active(side=side)
            return
        self.choosing_new_active = side
        self._show_banner(text="Choose a new active character")

    def _auto_choose_active(self, side: BattlePlayer) -> None:
        alive: list[int] = side.alive_indexes()
        if not alive:
            return
        result: CombatResult = self.engine.switch_character(user=side, index=alive[0], free=True)
        self.choosing_new_active = None
        self._refresh_battlefield()
        if result.message:
            self._show_banner(text=result.message)
        if self.pending_pass:
            self.pending_pass = False
            self._pass_turn(actor=self.current_turn or self._other(player=side))

    def _ensure_actives(self) -> None:
        for side in (self.battle_player, self.other_battle_player):
            active: CharacterCard | None = side.active_character
            if (active is None or not active.is_alive) and side.alive_indexes():
                side.set_active_character(index=side.alive_indexes()[0])

    def _finish_game(self, winner: BattlePlayer) -> None:
        self.winner = winner
        self.battle_sub_events["game_over"] = True
        self.bot_action_due_ms = None
        self.round_end_due_ms = None
        you_won: bool = winner is self.battle_player
        self.game_over_title.text_option.set_color(color=(255, 214, 90) if you_won else (236, 120, 120))
        self.game_over_title.set_text(text="You Win!" if you_won else "You Lose")
        self._show_banner(text="You Win!" if you_won else "You Lose")

    def _board_character_pos(self, index: int, is_player: bool, active: bool) -> tuple[int, int]:
        x: int = self.BOARD_CHARACTER_XS[index]
        if is_player:
            return x, self.PLAYER_ROW_Y - (self.ACTIVE_CHARACTER_OFFSET if active else 0)
        return x, self.OPPONENT_ROW_Y + (self.ACTIVE_CHARACTER_OFFSET if active else 0)

    def _build_board_characters(self, battle_player: BattlePlayer, is_player: bool) -> list[ImageComponent]:
        images: list[ImageComponent] = []
        for index, character in enumerate(battle_player.list_of_characters[:len(self.BOARD_CHARACTER_XS)]):
            image: ImageComponent = ImageComponent(image_option=self._character_board_surface(character=character), base_pos=self._board_character_pos(index=index, is_player=is_player, active=index == battle_player.active_character_index), anchor="center")
            image.update_layout()
            images.append(image)
        return images

    def _refresh_player_characters(self) -> None:
        for index, button in enumerate(self.board_player_character_buttons):
            if index >= len(self.battle_player.list_of_characters):
                continue
            character: CharacterCard = self.battle_player.list_of_characters[index]
            button.surface._raw_image = self._character_board_surface(character=character)
            button.surface.outline_image = None
            button.change_base_position(position=self._board_character_pos(index=index, is_player=True, active=index == self.battle_player.active_character_index))

    def _refresh_status_line(self) -> None:
        bits: list[str] = []
        if self.battle_player.supports:
            bits.append("Supports: " + ", ".join(card.name for card in self.battle_player.supports))
        if self.battle_player.summons:
            bits.append("Summons: " + ", ".join(str(summon["name"]) for summon in self.battle_player.summons))
        active: CharacterCard | None = self.battle_player.active_character
        if active and active.applied_element:
            bits.append(f"{active.name}: {active.applied_element.title()}")
        if active and active.shield:
            bits.append(f"Shield {active.shield}")
        self.status_line.set_text(text="  |  ".join(bits))

    def _refresh_battlefield(self) -> None:
        self._refresh_player_characters()
        self.board_opponent_characters = self._build_board_characters(battle_player=self.other_battle_player, is_player=False)
        self._refresh_hand_slots()
        self._refresh_opponent_hand()
        self._refresh_board_dice()
        self._refresh_status_line()

    def _hand_x(self, index: int, count: int, spacing: int) -> int:
        return round(self.BOARD_CENTER_X - (count - 1) * spacing / 2 + index * spacing)

    def _refresh_hand_slots(self) -> None:
        hand: list[ActionCard] = self.battle_player.hand
        for index, button in enumerate(self.hand_slot_buttons):
            if index >= len(hand):
                continue
            button.surface._raw_image = self._card_surface(card=hand[index], size=self.HAND_CARD_SIZE)
            button.surface.outline_image = None
            button.change_base_position(position=(self._hand_x(index=index, count=len(hand), spacing=self.HAND_SPACING), self.HAND_Y))

    def _refresh_opponent_hand(self) -> None:
        hidden: Surface = pygame.transform.smoothscale(surface=self._hidden_card_surface(), size=self.OPPONENT_HAND_CARD_SIZE)
        count: int = len(self.other_battle_player.hand)
        self.board_opponent_hand = []
        for index in range(count):
            image: ImageComponent = ImageComponent(image_option=hidden.copy(), base_pos=(self._hand_x(index=index, count=count, spacing=self.OPPONENT_HAND_SPACING), self.OPPONENT_HAND_Y), anchor="center")
            image.update_layout()
            self.board_opponent_hand.append(image)

    def _refresh_board_dice(self) -> None:
        self.board_dice = []
        for index, face in enumerate(self.battle_player.dice):
            column, row = divmod(index, self.BOARD_DICE_PER_COLUMN)
            position: tuple[int, int] = (self.BOARD_DICE_X - column * 28, self.BOARD_DICE_TOP_Y + row * self.BOARD_DICE_SPACING)
            image: ImageComponent = ImageComponent(image_option=pygame.transform.smoothscale(surface=self.die_faces[face], size=self.BOARD_DICE_SIZE), base_pos=position, anchor="center")
            image.update_layout()
            self.board_dice.append(image)
        self.board_dice_count_text.set_text(text=str(len(self.battle_player.dice)))

    def _update_hand_hover(self) -> None:
        count: int = len(self.battle_player.hand)
        for index, button in enumerate(self.hand_slot_buttons[:count]):
            target: tuple[int, int] = (self._hand_x(index=index, count=count, spacing=self.HAND_SPACING), self.HAND_RAISED_Y if button.focused else self.HAND_Y)
            if button.surface._raw_base_pos != target:
                button.change_base_position(position=target)

    def _update_action_phase(self) -> None:
        now: int = pygame.time.get_ticks()
        if self.battle_sub_events["game_over"]:
            return
        if self.round_end_due_ms is not None:
            if now >= self.round_end_due_ms:
                self._end_round()
            return
        if self.choosing_new_active is self.battle_player:
            return
        if self.current_turn is self.other_battle_player and self.bot_action_due_ms is not None and now >= self.bot_action_due_ms:
            self._bot_take_turn()
        self._update_hand_hover()

    def _set_die_face(self, index: int, face: str) -> None:
        button: Button = self.dice_buttons[index]
        button.surface._raw_image = self.die_faces[face]
        button.surface.outline_image = None
        button.surface.update_layout()

    def _refresh_dice(self) -> None:
        for index, face in enumerate(self.battle_player.dice):
            if index < len(self.dice_buttons):
                self._set_die_face(index=index, face=face)

    def _start_dice_animation(self, indexes: list[int]) -> None:
        self.rolling_dice_indexes = indexes
        self.dice_roll_start_ms = pygame.time.get_ticks()
        self.dice_last_swap_ms = 0

    def _update_dice_animation(self) -> None:
        if self.dice_roll_start_ms is None:
            return
        now: int = pygame.time.get_ticks()
        if now - self.dice_roll_start_ms >= self.DICE_ROLL_MS:
            self._finish_dice_animation()
            return
        if now - self.dice_last_swap_ms >= self.DICE_FACE_SWAP_MS:
            self.dice_last_swap_ms = now
            for index in self.rolling_dice_indexes:
                self._set_die_face(index=index, face=random.choice(DIE_FACES))

    def _finish_dice_animation(self) -> None:
        self.dice_roll_start_ms = None
        self.rolling_dice_indexes = []
        if not self.dice_rerolled:
            self._refresh_dice()
            self.roll_subtitle.set_text(text="Select the dice you want to keep. The rest will be rerolled.")
            return

        self.battle_player.sort_dice()
        self._refresh_dice()
        omni: int = self.battle_player.dice.count("omni")
        self.roll_subtitle.set_text(text=f"Your dice are ready - {omni} Omni")
        self.roll_opponent_label.set_text(text=f"Opponent rerolled {self.bot_rerolled_count} dice")
        self.confirm_hand_button.text_surface.set_text(text="Done")

    @override
    def update(self) -> None:
        super().update()
        if self._flip_is_spinning():
            self._update_first_player_flip()
        if self._dice_are_rolling():
            self._update_dice_animation()
        if self._action_phase_open():
            self._update_action_phase()
        return

    @override
    def add_events(self) -> None:
        super().add_events()

        self.end_round_button.add_event_listeners(page_state="test", condition=self._is_player_turn)
        for button in self.skill_buttons.values():
            button.add_event_listeners(page_state="test", condition=self._is_player_turn)
        for button in self.board_player_character_buttons:
            button.add_event_listeners(page_state="test", condition=self._player_characters_clickable)
        for index, button in enumerate(self.hand_slot_buttons):
            button.add_event_listeners(page_state="test", condition=lambda index=index: self._is_player_turn() and index < len(self.battle_player.hand))
        self.confirm_hand_button.add_event_listeners(page_state="test", condition=self._confirm_is_active)
        for button in self.dice_buttons:
            button.add_event_listeners(page_state="test", condition=self._dice_selector_is_open)
        for button in self.starting_hand_buttons:
            button.add_event_listeners(page_state="test", condition=self.selector_is_open)
        for button in self.character_buttons:
            button.add_event_listeners(page_state="test", condition=self.character_selector_is_open)
        return

    @override
    def update_layout(self) -> None:
        super().update_layout()

        self.action_card_selector_subtitle.update_layout()
        self.action_card_selector_title.update_layout()
        self.opponent_label.update_layout()
        self.end_round_button.update_layout()
        self.confirm_hand_button.update_layout()
        for button in self.starting_hand_buttons:
            button.update_layout()
        for card in self.opponent_hidden_cards:
            card.update_layout()

        self.character_selector_title.update_layout()
        self.character_selector_subtitle.update_layout()
        self.opponent_character_label.update_layout()
        for button in self.character_buttons:
            button.update_layout()
        for label in self.character_name_labels + self.character_info_labels:
            label.update_layout()
        for image in self.opponent_character_images:
            image.update_layout()

        self.flip_title.update_layout()
        self.flip_subtitle.update_layout()
        self.flip_result_text.update_layout()
        self.coin_image.update_layout()
        self.flip_player_label.update_layout()
        self.flip_opponent_label.update_layout()
        if self.flip_player_character:
            self.flip_player_character.update_layout()
        if self.flip_opponent_character:
            self.flip_opponent_character.update_layout()

        self.roll_title.update_layout()
        self.roll_round_label.update_layout()
        self.roll_subtitle.update_layout()
        self.roll_opponent_label.update_layout()
        for button in self.dice_buttons:
            button.update_layout()

        for image in self.board_opponent_characters + self.board_opponent_hand + self.board_dice:
            image.update_layout()
        self.board_dice_counter.update_layout()
        self.board_dice_count_text.update_layout()
        self.turn_label.update_layout()
        self.player_declared_label.update_layout()
        self.opponent_declared_label.update_layout()
        self.banner_bg.update_layout()
        self.banner_text.update_layout()
        self.status_line.update_layout()
        self.game_over_title.update_layout()
        self.game_over_subtitle.update_layout()
        for button in self.board_player_character_buttons + self.hand_slot_buttons + list(self.skill_buttons.values()):
            button.update_layout()
        return

    def _draw_selectable_button(self, button: Button, selected: bool) -> None:
        if selected:
            ImageComponent.create_outline(image_component=button.surface, color=(255, 214, 90), thickness=4)
            button.surface.draw_outline()
            button.text_surface.draw()
            return
        button.surface.outline_image = None
        button.draw()

    def _draw_highlighted_image(self, image: ImageComponent, highlighted: bool) -> None:
        if highlighted:
            if not image.outline_image:
                ImageComponent.create_outline(image_component=image, color=(255, 214, 90), thickness=3)
            image.draw_outline()
            return
        image.draw()

    def draw_action_card_selector(self) -> None:
        self.opponent_label.draw()
        for card in self.opponent_hidden_cards:
            card.draw()
        self.action_card_selector_subtitle.draw()
        self.action_card_selector_title.draw()
        for index, button in enumerate(self.starting_hand_buttons):
            self._draw_selectable_button(button=button, selected=index in self.selected_card_indexes)
        return

    def draw_character_selector(self) -> None:
        self.opponent_character_label.draw()
        bot_active: int | None = self.other_battle_player.active_character_index if self.character_confirmed else None
        for index, image in enumerate(self.opponent_character_images):
            self._draw_highlighted_image(image=image, highlighted=index == bot_active)

        self.character_selector_title.draw()
        self.character_selector_subtitle.draw()
        for index, button in enumerate(self.character_buttons):
            self._draw_selectable_button(button=button, selected=index == self.selected_character_index)
        for label in self.character_name_labels + self.character_info_labels:
            label.draw()
        return

    def draw_first_player_flip(self) -> None:
        self.flip_title.draw()
        self.flip_subtitle.draw()

        player_first: bool = self.flip_finished and self.first_player is self.battle_player
        opponent_first: bool = self.flip_finished and self.first_player is self.other_battle_player
        if self.flip_player_character:
            self._draw_highlighted_image(image=self.flip_player_character, highlighted=player_first)
        if self.flip_opponent_character:
            self._draw_highlighted_image(image=self.flip_opponent_character, highlighted=opponent_first)
        self.flip_player_label.draw()
        self.flip_opponent_label.draw()

        self.coin_image.draw()
        if self.flip_finished:
            self.flip_result_text.draw()
        return

    def draw_roll_phase(self) -> None:
        self.roll_title.draw()
        self.roll_round_label.draw()
        self.roll_subtitle.draw()
        for index, button in enumerate(self.dice_buttons[:len(self.battle_player.dice)]):
            self._draw_selectable_button(button=button, selected=index in self.kept_dice_indexes)
        self.roll_opponent_label.draw()
        return

    def draw_battlefield(self) -> None:
        for image in self.board_opponent_hand:
            image.draw()
        bot_active: int | None = self.other_battle_player.active_character_index
        for index, image in enumerate(self.board_opponent_characters):
            self._draw_highlighted_image(image=image, highlighted=index == bot_active)

        targeting: bool = self.selected_hand_index is not None or self.choosing_new_active is self.battle_player
        for index, button in enumerate(self.board_player_character_buttons[:len(self.battle_player.list_of_characters)]):
            selected: bool = index == self.battle_player.active_character_index or targeting
            self._draw_selectable_button(button=button, selected=selected)

        if self.other_battle_player in self.declared_end:
            self.opponent_declared_label.draw()
        if self.battle_player in self.declared_end:
            self.player_declared_label.draw()

        self.board_dice_counter.draw()
        self.board_dice_count_text.draw()
        for image in self.board_dice:
            image.draw()
        self.status_line.draw()

        self.end_round_button.draw()
        self.turn_label.draw()
        for button in self.skill_buttons.values():
            button.draw()

        # Draw the hovered card last so it sits on top of its neighbours.
        hand_buttons: list[Button] = self.hand_slot_buttons[:len(self.battle_player.hand)]
        for index, button in enumerate(hand_buttons):
            if not button.focused and index != self.selected_hand_index:
                button.draw()
        for index, button in enumerate(hand_buttons):
            if button.focused or index == self.selected_hand_index:
                self._draw_selectable_button(button=button, selected=index == self.selected_hand_index)

        if pygame.time.get_ticks() < self.banner_until_ms and not self.battle_sub_events["game_over"]:
            self.banner_bg.draw()
            self.banner_text.draw()

        if self.battle_sub_events["game_over"]:
            self.quit_game_overlay_background.draw()
            self.banner_bg.draw()
            self.game_over_title.draw()
            self.game_over_subtitle.draw()
        return

    @override
    def draw(self) -> None:
        # If the action phase is open, show the battlefield and stop.
        if self.battle_sub_events["action"]:
            self.draw_battlefield()
            return

        self.quit_game_overlay_background.draw()
        if self.battle_sub_events["action_card_selector"]:
            self.draw_action_card_selector()
        elif self.battle_sub_events["character_selector"]:
            self.draw_character_selector()
        elif self.battle_sub_events["first_player_flip"]:
            self.draw_first_player_flip()
        elif self.battle_sub_events["roll"]:
            self.draw_roll_phase()
        else:
            return

        if self._confirm_is_active():
            self.confirm_hand_button.draw()
        return
