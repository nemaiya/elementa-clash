import pygame # Importing the pygame module from the pygame library, to use its functions and classes for creating games
_ = pygame.init() # Initializing all imported pygame modules, which is necessary before using any other pygame functions

clock = pygame.time.Clock()

#from pages.BasePage import BasePage
from pages.BasePage import BasePage
from pages.MainMenu import MainMenu
from pages.Auth     import Auth

from .CustomTypes import PageType

class GameManager():
    current_page: "BasePage"  # This holds the current page that is being displayed on the screen.

    pages_map: dict[PageType, type[BasePage]] = {
        "authenticate": Auth,
        "main_menu": MainMenu
    }

    def __init__(self) -> None:
        self.current_page = Auth() # This is used to create a new instance of the BasePage Class, which is used to display the main menu of the game.

        self.run()
        pass

    def run(self) -> None: # This is used to run the game, and is called every frame. This is called by the main.py file to run the game.
        while self.current_page.running: # This is used to check if the game is running or not, this is used to stop the game when the user closes the window

            self.current_page.run() # This is used to run the current page, and is called every frame. This is called by the GameManager Class to run the page.


if __name__ == "__main__":
    game_manager = GameManager() # This is used to create a new instance of the GameManager Class, which is used to run the game.