from typing import TypeAlias, Literal, override, final, cast

import pygame
from pygame.surface import Surface

from components.Button import Button, ImageOption
from components.Image import ImageComponent, TextImageComponent, TextOption
from pages.BasePage import BasePage
from util.DataBase.Database import Response
from util.Game.Player import LeaderboardEntry
from util.GlobalHolder import GlobalHolder


LeaderboardType: TypeAlias = Literal["xp", "wins", "battles"]


class LeaderboardPage(BasePage):
    TOP_SLOTS: int = 10
    ROW_WIDTH: int = 720
    ROW_HEIGHT: int = 28
    ROW_START_Y: int = 124
    ROW_SPACING: int = 28
    PLAYER_ROW_Y: int = 416
    PLAYER_ROW_HEIGHT: int = 36
    REVEAL_STAGGER_MS: int = 70
    REVEAL_DURATION_MS: int = 280
    SLIDE_PX: int = 22

    TYPE_LABELS: dict[LeaderboardType, str] = {
        "xp": "XP",
        "wins": "Wins",
        "battles": "Battles",
    }
    VALUE_LABELS: dict[LeaderboardType, str] = {
        "xp": "XP",
        "wins": "Wins",
        "battles": "Battles",
    }

    @final
    def __init__(self) -> None:
        if not GlobalHolder.player:
            raise ValueError("Player not found")

        self.board_type: LeaderboardType = "xp"
        self.entries: list[LeaderboardEntry] = []
        self.loading: bool = True
        self.reveal_start_ms: int | None = None
        super().__init__()
        self.change_page(new_state="leaderboard")
        self.db.get_leaderboard()

    @override
    def init(self) -> None:
        super().init()
        self.init_background(image_key="background_image2")

        self.title: TextImageComponent = TextImageComponent(
            text_option=TextOption(text="XP Leaderboard", size=30, align="center", bold=True, color=(255, 250, 250)),
            base_pos=(480, 26),
            anchor="center",
        )
        self.status_text: TextImageComponent = TextImageComponent(
            text_option=TextOption(text="Fetching ranks...", size=12, align="center", color=(214, 208, 196)),
            base_pos=(480, 46),
            anchor="center",
        )

        self.type_buttons: dict[LeaderboardType, Button] = {}
        for board_type, label, x in (("xp", "XP", 330), ("wins", "Wins", 480), ("battles", "Battles", 630)):
            button: Button = Button(
                image_option=ImageOption(image=self.resize_image(image=self.load_image(image_key="button3"), size=(110, 28))),
                text_option=TextOption(text=label, size=12, bold=True, color=(230, 226, 216)),
                position=(x, 72),
                anchor="center",
            )
            button.on_activate = lambda board_type=board_type: self.set_board_type(board_type=board_type)
            self.type_buttons[board_type] = button

        self.header_rank: TextImageComponent = TextImageComponent(text_option=TextOption(text="#", size=12, bold=True, color=(196, 168, 110)), base_pos=(186, 104), anchor="center")
        self.header_name: TextImageComponent = TextImageComponent(text_option=TextOption(text="Username", size=12, bold=True, color=(196, 168, 110)), base_pos=(400, 104), anchor="center")
        self.header_value: TextImageComponent = TextImageComponent(text_option=TextOption(text="XP", size=12, bold=True, color=(196, 168, 110)), base_pos=(700, 104), anchor="center")

        self.row_backgrounds: list[ImageComponent] = []
        self.row_ranks: list[TextImageComponent] = []
        self.row_names: list[TextImageComponent] = []
        self.row_values: list[TextImageComponent] = []
        for index in range(self.TOP_SLOTS):
            y: int = self.ROW_START_Y + index * self.ROW_SPACING
            self.row_backgrounds.append(ImageComponent(image_option=self._row_surface(highlighted=False, empty=True), base_pos=(480, y), anchor="center"))
            self.row_ranks.append(TextImageComponent(text_option=TextOption(text="", size=13, align="center", color=(230, 226, 216)), base_pos=(186, y), anchor="center"))
            self.row_names.append(TextImageComponent(text_option=TextOption(text="", size=13, align="center", color=(255, 250, 250)), base_pos=(400, y), anchor="center"))
            self.row_values.append(TextImageComponent(text_option=TextOption(text="", size=13, align="center", color=(230, 226, 216)), base_pos=(700, y), anchor="center"))

        self.player_background: ImageComponent = ImageComponent(image_option=self._row_surface(highlighted=True, empty=False, height=self.PLAYER_ROW_HEIGHT), base_pos=(480, self.PLAYER_ROW_Y), anchor="center")
        self.player_rank: TextImageComponent = TextImageComponent(text_option=TextOption(text="-", size=15, align="center", bold=True, color=(255, 214, 90)), base_pos=(186, self.PLAYER_ROW_Y), anchor="center")
        self.player_name: TextImageComponent = TextImageComponent(text_option=TextOption(text=GlobalHolder.player.username if GlobalHolder.player else "", size=15, align="center", bold=True, color=(255, 250, 240)), base_pos=(400, self.PLAYER_ROW_Y), anchor="center")
        self.player_value: TextImageComponent = TextImageComponent(text_option=TextOption(text="0", size=15, align="center", bold=True, color=(255, 214, 90)), base_pos=(700, self.PLAYER_ROW_Y), anchor="center")
        self.player_tag: TextImageComponent = TextImageComponent(text_option=TextOption(text="You", size=10, align="center", bold=True, color=(255, 214, 90)), base_pos=(800, self.PLAYER_ROW_Y), anchor="center")

        self.go_back_button: Button = Button(
            image_option=ImageOption(image=self.load_image(image_key="go_back")),
            text_option=TextOption(text="", size=0),
            key=pygame.K_b,
            position=(480, 508),
            anchor="center",
        )
        self.go_back_button.on_activate = lambda: self.change_page(new_state="main_menu")
        self._refresh_type_buttons()
        self._apply_entries()
        return

    def _row_surface(self, highlighted: bool, empty: bool, height: int | None = None) -> Surface:
        surface: Surface = pygame.Surface(size=(self.ROW_WIDTH, height or self.ROW_HEIGHT), flags=pygame.SRCALPHA)
        rect = surface.get_rect()
        if highlighted:
            fill = (48, 40, 22, 230)
            border = (255, 214, 90)
            width = 3
        elif empty:
            fill = (20, 24, 38, 90)
            border = (70, 76, 96)
            width = 1
        else:
            fill = (20, 24, 38, 190)
            border = (90, 96, 118)
            width = 2
        _ = pygame.draw.rect(surface=surface, color=fill, rect=rect, border_radius=8)
        _ = pygame.draw.rect(surface=surface, color=border, rect=rect, width=width, border_radius=8)
        return surface

    def _page_is_open(self) -> bool:
        return not (self.sub_events["quit_confirmation"] or self.sub_events["setting_menu"])

    def set_board_type(self, board_type: LeaderboardType) -> None:
        if self.board_type == board_type:
            return
        self.board_type = board_type
        self.title.set_text(text=f"{self.TYPE_LABELS[board_type]} Leaderboard")
        self.header_value.set_text(text=self.VALUE_LABELS[board_type])
        self._refresh_type_buttons()
        self._apply_entries(animate=True)

    def _refresh_type_buttons(self) -> None:
        for board_type, button in self.type_buttons.items():
            selected: bool = board_type == self.board_type
            button.text_surface.text_option.set_color(color=(255, 214, 90) if selected else (230, 226, 216))
            button.text_surface.update_layout()

    def _local_entry(self) -> LeaderboardEntry | None:
        player = GlobalHolder.player
        if player is None:
            return None
        return LeaderboardEntry(
            uid=player.uid,
            username=player.username,
            xp=int(player.user_info.get("xp", 0)),
            battle_wins=int(player.user_info.get("battle_wins", 0)),
            total_battles=int(player.user_info.get("total_battles", 0)),
        )

    def _merged_entries(self) -> list[LeaderboardEntry]:
        local: LeaderboardEntry | None = self._local_entry()
        merged: list[LeaderboardEntry] = []
        found: bool = False
        for entry in self.entries:
            if local is not None and entry["uid"] == local["uid"]:
                merged.append(local)
                found = True
            else:
                merged.append(entry)
        if local is not None and not found:
            merged.append(local)
        return merged

    def _entry_value(self, entry: LeaderboardEntry) -> int:
        if self.board_type == "xp":
            return int(entry["xp"])
        if self.board_type == "wins":
            return int(entry["battle_wins"])
        return int(entry["total_battles"])

    def _sorted_entries(self) -> list[LeaderboardEntry]:
        return sorted(self._merged_entries(), key=self._entry_value, reverse=True)

    def _apply_entries(self, animate: bool = False) -> None:
        ranked: list[LeaderboardEntry] = self._sorted_entries()
        for index in range(self.TOP_SLOTS):
            empty: bool = index >= len(ranked)
            entry: LeaderboardEntry | None = None if empty else ranked[index]
            self.row_backgrounds[index]._raw_image = self._row_surface(highlighted=False, empty=empty)
            self.row_backgrounds[index].update_layout()
            if entry is None:
                self.row_ranks[index].set_text(text="")
                self.row_names[index].set_text(text="")
                self.row_values[index].set_text(text="")
            else:
                self.row_ranks[index].set_text(text=str(index + 1))
                self.row_names[index].set_text(text=entry["username"])
                self.row_values[index].set_text(text=str(self._entry_value(entry=entry)))

        local: LeaderboardEntry | None = self._local_entry()
        rank_text: str = "-"
        value_text: str = "0"
        name_text: str = local["username"] if local else ""
        if local is not None:
            value_text = str(self._entry_value(entry=local))
            for index, entry in enumerate(ranked):
                if entry["uid"] == local["uid"]:
                    rank_text = str(index + 1)
                    break
        self.player_rank.set_text(text=rank_text)
        self.player_name.set_text(text=name_text)
        self.player_value.set_text(text=value_text)
        if animate or self.reveal_start_ms is None:
            self.reveal_start_ms = pygame.time.get_ticks()

    def _row_progress(self, index: int) -> float:
        if self.reveal_start_ms is None:
            return 1.0
        elapsed: int = pygame.time.get_ticks() - self.reveal_start_ms - index * self.REVEAL_STAGGER_MS
        progress: float = max(0.0, min(1.0, elapsed / self.REVEAL_DURATION_MS))
        return 1.0 - (1.0 - progress) ** 3

    def _draw_fading_image(self, image: ImageComponent, progress: float, rest_y: int) -> None:
        if progress <= 0:
            return
        slide: int = round((1.0 - progress) * self.SLIDE_PX)
        surface: Surface = image.image.copy()
        surface.set_alpha(int(255 * progress))
        rect = surface.get_rect(center=GlobalHolder.resize_position(position=(480, rest_y + slide)))
        # Keep the row's own x so rank/name/value stay in their columns.
        rect.centerx = image.rect.centerx
        rect.centery = GlobalHolder.resize_position(position=(480, rest_y + slide))[1]
        _ = self.screen_manager.blit(source=surface, dest=rect)

    def _draw_fading_text(self, text: TextImageComponent, progress: float, rest_y: int) -> None:
        if progress <= 0 or not text.text_option.text:
            return
        slide: int = round((1.0 - progress) * self.SLIDE_PX)
        surface: Surface = text.image.copy()
        surface.set_alpha(int(255 * progress))
        position: tuple[int, int] = GlobalHolder.resize_position(position=(text._raw_base_pos[0], rest_y + slide))
        rect = surface.get_rect(center=position)
        _ = self.screen_manager.blit(source=surface, dest=rect)

    @override
    def update(self) -> None:
        super().update()
        if self.db.response_queue.empty():
            return
        res: Response = self.db.response_queue.get_nowait()
        if res.action != "get_leaderboard":
            return
        self.loading = False
        if res.success and isinstance(res.user_data, list):
            self.entries = cast(list[LeaderboardEntry], res.user_data)
            self.status_text.set_text(text="")
        else:
            self.status_text.set_text(text=res.message or "Could not load leaderboard")
        self._apply_entries(animate=True)

    @override
    def add_events(self) -> None:
        super().add_events()
        self.go_back_button.add_event_listeners(page_state="leaderboard", condition=self._page_is_open)
        for button in self.type_buttons.values():
            button.add_event_listeners(page_state="leaderboard", condition=self._page_is_open)

    @override
    def update_layout(self) -> None:
        super().update_layout()
        self.title.update_layout()
        self.status_text.update_layout()
        self.header_rank.update_layout()
        self.header_name.update_layout()
        self.header_value.update_layout()
        for button in self.type_buttons.values():
            button.update_layout()
        for image in self.row_backgrounds:
            image.update_layout()
        for text in self.row_ranks + self.row_names + self.row_values:
            text.update_layout()
        self.player_background.update_layout()
        self.player_rank.update_layout()
        self.player_name.update_layout()
        self.player_value.update_layout()
        self.player_tag.update_layout()
        self.go_back_button.update_layout()

    @override
    def draw(self) -> None:
        self.quit_game_overlay_background.draw()
        self.title.draw()
        self.status_text.draw()
        for button in self.type_buttons.values():
            button.draw()
        self.header_rank.draw()
        self.header_name.draw()
        self.header_value.draw()

        for index in range(self.TOP_SLOTS):
            y: int = self.ROW_START_Y + index * self.ROW_SPACING
            progress: float = self._row_progress(index=index)
            self._draw_fading_image(image=self.row_backgrounds[index], progress=progress, rest_y=y)
            self._draw_fading_text(text=self.row_ranks[index], progress=progress, rest_y=y)
            self._draw_fading_text(text=self.row_names[index], progress=progress, rest_y=y)
            self._draw_fading_text(text=self.row_values[index], progress=progress, rest_y=y)

        player_progress: float = self._row_progress(index=self.TOP_SLOTS)
        self._draw_fading_image(image=self.player_background, progress=player_progress, rest_y=self.PLAYER_ROW_Y)
        self._draw_fading_text(text=self.player_rank, progress=player_progress, rest_y=self.PLAYER_ROW_Y)
        self._draw_fading_text(text=self.player_name, progress=player_progress, rest_y=self.PLAYER_ROW_Y)
        self._draw_fading_text(text=self.player_value, progress=player_progress, rest_y=self.PLAYER_ROW_Y)
        self._draw_fading_text(text=self.player_tag, progress=player_progress, rest_y=self.PLAYER_ROW_Y)
        self.go_back_button.draw()
