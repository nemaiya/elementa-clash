"""
Action card selector extract from pages/Battle.py.

Document this feature in the numbered order below.
This file is documentation only. Do not import it as a page.
"""

import pygame
from pygame.surface import Surface

from components.Button import Button, ImageOption
from components.Image import ImageComponent, TextImageComponent, TextOption
from util.Game.Card import ActionCard
from util.GlobalHolder import GlobalHolder
from CustomTypes import ActionFunction


# =============================================================================
# 1. Purpose
# =============================================================================
# First prepare step. Both sides are dealt 4 action cards. The player marks
# cards to put back and draw replacements. The bot does the same at random,
# but its cards stay face down so the player cannot see the new hand.


# =============================================================================
# 2. When this step is shown
# =============================================================================
# Prepare sequence starts on "action_card_selector".
# The selector stays on screen until the player has confirmed the hand
# (hand_confirmed == True) and then presses Confirm again to move on.

#   self.battle_sub_event: dict[str, bool] = {"prepare": True}
#   self.battle_sequence: dict[str, list[str]] = {
#       "prepare": ["action_card_selector", "character_selector", "first_player_flip"]
#   }
#   self.prepare_step_index: int = 0


def _current_prepare_step(self) -> str | None:
    steps: list[str] = self.battle_sequence.get("prepare", [])
    if self.prepare_step_index >= len(steps):
        return None
    return steps[self.prepare_step_index]


def in_prepare_step(self, step: str) -> bool:
    return self.battle_sub_event.get("prepare", False) and self._current_prepare_step() == step


def selector_is_open(self) -> bool:
    return self.in_prepare_step(step="action_card_selector") and not self.hand_confirmed


def _flip_is_spinning(self) -> bool:
    return self.in_prepare_step(step="first_player_flip") and not self.flip_finished


def _prepare_is_open(self) -> bool:
    return self.battle_sub_event.get("prepare", False) and self._current_prepare_step() is not None and not self._flip_is_spinning()


def _confirm_is_active(self) -> bool:
    return self._prepare_is_open() or (self._roll_phase_open() and not self._dice_are_rolling())


# =============================================================================
# 3. Data stored for this step
# =============================================================================
# Deal both opening hands before the page UI is built.
#
#   self.battle_player.draw_starting_hand(number_of_cards=4)
#   self.other_battle_player.draw_starting_hand(number_of_cards=4)
#
#   self.selected_card_indexes: set[int] = set()
#   self.hand_confirmed: bool = False
#
# selected_card_indexes = which of the 4 player cards are marked to switch.
# hand_confirmed        = True after the first Confirm, so cards cannot be
#                         toggled again. A second Confirm leaves this step.


# =============================================================================
# 4. Setup: labels, confirm button, then build the 4+4 cards
# =============================================================================

def init_action_card_selector(self) -> None:
    self.action_card_selector_title: TextImageComponent = TextImageComponent(text_option=TextOption(text="Starting Hand", size=32, align="center", bold=True, color=(255, 250, 250)), base_pos=(480, 108), anchor="center")
    self.action_card_selector_subtitle: TextImageComponent = TextImageComponent(text_option=TextOption(text="Select card(s) to switch", size=14, align="center", color=(230, 226, 216)), base_pos=(480, 140), anchor="center")
    self.opponent_label: TextImageComponent = TextImageComponent(text_option=TextOption(text="Opponent", size=14, align="center", color=(230, 226, 216)), base_pos=(270, 42), anchor="center")

    self.starting_hand_buttons: list[Button] = []
    self.opponent_hidden_cards: list[ImageComponent] = []
    self._build_starting_hand()

    self.confirm_hand_button: Button = Button(
        image_option=ImageOption(image=self.load_image(image_key="button1")),
        text_option=TextOption(text="Confirm", size=16),
        position=(480, 470),
        anchor="center",
    )
    self.confirm_hand_button.on_activate = self.on_confirm


# =============================================================================
# 5. How a card is drawn (player face-up, opponent face-down)
# =============================================================================

@staticmethod
def _fit_surface(surface: Surface, size: tuple[int, int]) -> Surface:
    # The Card draw helpers already apply the screen scale, so undo it here and let ImageComponent rescale.
    scale: float = GlobalHolder.scale or 1
    if scale != 1:
        base_size: tuple[int, int] = (
            max(1, round(surface.get_width() / scale)),
            max(1, round(surface.get_height() / scale)),
        )
        surface = pygame.transform.smoothscale(surface=surface, size=base_size)
    return pygame.transform.smoothscale(surface=surface, size=size)


def _card_surface(self, card: ActionCard, size: tuple[int, int] = (100, 138)) -> Surface:
    die_needed: int = int(card.cost.get("unaligned", 0))
    surface: Surface = ActionCard.draw_action_card(card_key=card.image_key, die_needed=die_needed)
    return self._fit_surface(surface=surface, size=size)


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
        button.on_activate = self._make_card_toggle(index=index)
        self.starting_hand_buttons.append(button)

    self.opponent_hidden_cards.clear()
    for index in range(len(self.other_battle_player.hand)):
        if index >= len(opponent_positions):
            break
        self.opponent_hidden_cards.append(
            ImageComponent(image_option=hidden_surface.copy(), base_pos=opponent_positions[index], anchor="center")
        )


# =============================================================================
# 6. Player input: tap a card to mark / unmark it for switching
# =============================================================================

def _make_card_toggle(self, index: int) -> ActionFunction:
    def toggle() -> None:
        self._toggle_starting_card(index=index)
    return toggle


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


# =============================================================================
# 7. Confirm: swap the marked player cards, then the bot swaps in secret
# =============================================================================
# BattlePlayer.switch_cards(indexes):
#   Chosen cards go back into the deck. Replacements are drawn first so the
#   same card is not dealt straight back into that slot.
#
# OtherBattlePlayer.switch_random_cards():
#   Each bot card has a 50% chance to switch. The face-down backs do not change.


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


def _refresh_starting_hand(self) -> None:
    for button, card in zip(self.starting_hand_buttons, self.battle_player.hand):
        button.surface._raw_image = self._card_surface(card=card)
        button.surface.outline_image = None
        button.text_surface.text_option.set_text(text=card.name)
        button.surface.update_layout()
        button.text_surface.update_layout()


# =============================================================================
# 8. Leaving this step (second Confirm)
# =============================================================================
# First Confirm -> confirm_starting_hand().
# Second Confirm -> _next_prepare_step(), which opens character_selector.


def on_confirm(self) -> None:
    if self._roll_phase_open():
        self.advance_roll_phase()
    else:
        self.advance_prepare()


def advance_prepare(self) -> None:
    step: str | None = self._current_prepare_step()
    if step == "action_card_selector":
        if not self.hand_confirmed:
            self.confirm_starting_hand()
        else:
            self._next_prepare_step()
    elif step == "character_selector":
        if not self.character_confirmed:
            self.confirm_active_character()
        else:
            self._next_prepare_step()
    elif step == "first_player_flip" and self.flip_finished:
        self._next_prepare_step()


def _next_prepare_step(self) -> None:
    self.prepare_step_index += 1
    self.confirm_hand_button.text_surface.set_text("Confirm")
    step: str | None = self._current_prepare_step()
    if step is None:
        self.battle_sub_event["prepare"] = False
        self._start_roll_phase()
    elif step == "first_player_flip":
        self._start_first_player_flip()


# =============================================================================
# 9. Events (clicks only work while the selector is open)
# =============================================================================

def add_action_card_selector_events(self) -> None:
    self.confirm_hand_button.add_event_listeners(page_state="battle", condition=self._confirm_is_active)
    for button in self.starting_hand_buttons:
        button.add_event_listeners(page_state="battle", condition=self.selector_is_open)


# =============================================================================
# 10. Layout (window resize)
# =============================================================================

def update_action_card_selector_layout(self) -> None:
    self.action_card_selector_subtitle.update_layout()
    self.action_card_selector_title.update_layout()
    self.opponent_label.update_layout()
    self.confirm_hand_button.update_layout()
    for button in self.starting_hand_buttons:
        button.update_layout()
    for card in self.opponent_hidden_cards:
        card.update_layout()


# =============================================================================
# 11. Drawing
# =============================================================================
# BattlePage.draw() for this step:
#   dim the background, draw the selector, then draw Confirm if it is active.
#
#   if self.battle_sub_event.get("prepare"):
#       step = self._current_prepare_step()
#       self.quit_game_overlay_background.draw()
#       if step == "action_card_selector":
#           self._draw_action_card_selector()
#       if self._confirm_is_active():
#           self.confirm_hand_button.draw()


def _draw_selectable_button(self, button: Button, selected: bool) -> None:
    if selected:
        ImageComponent.create_outline(image_component=button.surface, color=(255, 214, 90), thickness=4)
        button.surface.draw_outline()
        button.text_surface.draw()
        return
    button.surface.outline_image = None
    button.draw()


def _draw_action_card_selector(self) -> None:
    self.opponent_label.draw()
    for card in self.opponent_hidden_cards:
        card.draw()
    self.action_card_selector_subtitle.draw()
    self.action_card_selector_title.draw()
    for index, button in enumerate(self.starting_hand_buttons):
        self._draw_selectable_button(button=button, selected=index in self.selected_card_indexes)
