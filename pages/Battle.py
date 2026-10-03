




from typing import ClassVar, override

from components.Button import Button, ImageOption
from components.Image import TextImageComponent, TextOption
from pages.BasePage import BasePage
from util.Game.Player import DeckData, Player, UserInfo


class BattlePage(BasePage):

    def __init__(self) -> None:
        super().__init__()
        self.player: Player = Player(uid="123", username="nemaiya", user_info=UserInfo(xp=200, level=2, active_deck_uid="1"), user_decks=[
            DeckData(uid="1", name="Zhongli's Ass", characters=["jean", "amber", "fishcl"], action_cards=[])
        ])
        self.change_page(new_state="battle")
        self.init_background(image_key="battle_bg1")

        self.battle_sub_event: dict[ str, bool ] = {"prepare": True}
        self.battle_sequence: dict[str, list[str] ] =  {"prepare": ["action_card_selector"]}

    @override
    def init(self) -> None:
        super().init()
        self.action_card_selector_title: TextImageComponent = TextImageComponent(text_option=TextOption(text="Starting Hand", size=32, align="center", bold=True, color=(255, 250, 250)), base_pos=(480, 108), anchor="center") # pyright: ignore[reportUninitializedInstanceVariable]
        self.action_card_selector_subtitle: TextImageComponent = TextImageComponent(text_option=TextOption(text="Select card(s) to switch", size=12, align="center"), base_pos=(480,130), anchor="center") # pyright: ignore[reportUninitializedInstanceVariable]
        self.end_round_button: Button =  Button(image_option=ImageOption(image=self.load_image(image_key="end_of_turn")), text_option=TextOption(text="", size=0), position=(10, 256)) # pyright: ignore[reportUninitializedInstanceVariable]

    @override
    def update_layout(self) -> None:
        super().update_layout()
        self.action_card_selector_subtitle.update_layout()
        self.action_card_selector_title.update_layout()
        self.end_round_button.update_layout()
    
    @override
    def add_events(self) -> None:
        #super().add_events()
        self.end_round_button.add_event_listeners(page_state="battle")

    @override
    def draw(self) -> None:
        if self.battle_sub_event.get("prepare"):
            self.quit_game_overlay_background.draw()
            self.action_card_selector_subtitle.draw()
            self.action_card_selector_title.draw()

    
