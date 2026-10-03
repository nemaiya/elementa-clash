from typing import final, override, Literal, TypeAlias
from pygame import Surface
import pygame

from components.Button import Button, ImageOption
from components.Image import ImageComponent, TextImageComponent, TextOption
from .BasePage import BasePage

Anchor: TypeAlias = Literal["topleft", "topright", "center"]

class MainMenu(BasePage):
    @final
    def __init__(self) -> None:
        super().__init__()
        self.change_page(new_state="main_menu")
        # self.init() - Assuming BasePage handles this or you call it explicitly elsewhere like in Auth

    @override
    def init(self) -> None:
        super().init()

        self.init_background(image_key="background_image2")
        
        # Converted to the new TextImageComponent using TextOption
        self.text_image: TextImageComponent = TextImageComponent(text_option=TextOption(text="Main Menu", size=32, color=(0, 0, 0), bold=True), base_pos=(480, 100), anchor="center") # pyright: ignore[reportUninitializedInstanceVariable]

        # Converted all buttons to use TextOption instead of the raw text string, and centered them horizontally at 480 to match your Auth layout
        self.play_online_button: Button = Button(image_option=ImageOption(image=self.load_image(image_key="button1")), text_option=TextOption(text="Play Online", size=16), key=pygame.K_o, position=(480, 200), anchor="center") # pyright: ignore[reportUninitializedInstanceVariable]

        self.play_button: Button = Button(image_option=ImageOption(image=self.load_image(image_key="button1")), text_option=TextOption(text="Play", size=16), key=pygame.K_p, position=(480, 260), anchor="center") # pyright: ignore[reportUninitializedInstanceVariable]

        self.deck_setup_button: Button = Button(image_option=ImageOption(image=self.load_image(image_key="button1")), text_option=TextOption(text="Deck Setup", size=16), key=pygame.K_d, position=(480, 320), anchor="center") # pyright: ignore[reportUninitializedInstanceVariable]

        self.leaderboard_button: Button = Button(image_option=ImageOption(image=self.load_image(image_key="button1")), text_option=TextOption(text="Leaderboard", size=16), key=pygame.K_l, position=(480, 380), anchor="center") # pyright: ignore[reportUninitializedInstanceVariable]

        self.tutorial_button: Button = Button(image_option=ImageOption(image=self.load_image(image_key="button1")), text_option=TextOption(text="Tutorial", size=16), key=pygame.K_t, position=(480, 440), anchor="center") # pyright: ignore[reportUninitializedInstanceVariable]
        return

    @override
    def add_events(self) -> None:
        super().add_events()

        # Added event listeners for all buttons, not just play_button
        condition= lambda: not (self.sub_events["quit_confirmation"] or self.sub_events["setting_menu"])
        self.play_online_button.add_event_listeners(page_state="main_menu", condition=condition)
        self.play_button.add_event_listeners(page_state="main_menu", condition=condition)

        self.deck_setup_button.on_activate = lambda: self.change_page(new_state="deck_menu")
        self.deck_setup_button.add_event_listeners(page_state="main_menu", condition=condition)
        self.leaderboard_button.add_event_listeners(page_state="main_menu", condition=condition)
        self.tutorial_button.add_event_listeners(page_state="main_menu", condition=condition)
        return

    @override
    def update_layout(self) -> None:
        super().update_layout()

        self.text_image.update_layout()
        self.play_online_button.update_layout()
        self.play_button.update_layout()
        self.deck_setup_button.update_layout()
        self.leaderboard_button.update_layout()
        self.tutorial_button.update_layout()
        return

    @override
    def draw(self) -> None:
        # Base class draw for background if applicable, otherwise just draw components
        self.text_image.draw()
        
        self.play_online_button.draw()
        self.play_button.draw()
        self.deck_setup_button.draw()
        self.leaderboard_button.draw()
        self.tutorial_button.draw()
        return