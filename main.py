from pygame.time import Clock


import pygame # Importing the pygame module from the pygame library, to use its functions and classes for creating games
_ = pygame.init() # Initializing all imported pygame modules, which is necessary before using any other pygame functions

clock = pygame.time.Clock()

#from pages.BasePage import BasePage
from pages.BasePage import BasePage
from pages.MainMenu import MainMenu
from pages.Auth     import Auth
from pages.Deck     import DeckPage as Deck
from pages.Battle   import BattlePage
from pages.TestPage import TestPage
from CustomTypes import PageType

class GameManager():
    # Tracks the active page instance currently being displayed and updated.
    current_page: "BasePage" 

    # Maps each page name to its corresponding class so the game can switch pages.
    pages_map: dict[PageType, type[BasePage]] = {
        "global": BasePage,
        "authenticate": Auth,
        "main_menu": MainMenu,
        "deck_menu": Deck,
        "battle": BattlePage,
        "test": TestPage
    }

    def __init__(self) -> None:
        # Start on the battle page when the game manager is created.
        self.current_page = BattlePage() 
        # Begin the main game loop immediately.
        self.run()

    def run(self) -> None: 
        # Controls whether the whole game loop should keep running.
        app_running = True
        # Keeps track of the page that was previously active.
        current_page: PageType = self.current_page.current_page

        while app_running:
            # 1. Run the current page loop (blocks here until the page's running flag is False)
            self.current_page.run() 
            
            # 2. Check which page the current page wants to switch to.
            # Each page stores its next target in current_page.
            temp_page: PageType = self.current_page.current_page
            
            # 3. If the target page is different from the current one, create and switch to it.
            if temp_page != current_page:
                print(f"Switching to page: {temp_page}")
                self.current_page = self.pages_map[temp_page]()
                current_page = temp_page

            # Stop the game loop if the current page is no longer running.
            if not self.current_page.running: app_running = False

            # Limit the frame rate for the active page if it has an FPS value.
            if self.current_page.FPS:
                _ = clock.tick(self.current_page.FPS)
                
        # Clean up pygame resources once the loop finishes.
        pygame.quit()

if __name__ == "__main__":
    game_manager = GameManager() # This is used to create a new instance of the GameManager Class, which is used to run the game.