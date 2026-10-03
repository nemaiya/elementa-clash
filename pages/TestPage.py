from pygame.surface import Surface
import pygame
from typing import override

from pages.BasePage import BasePage
from components.Draggable import DraggableComponent

class TestPage(BasePage):
    def __init__(self) -> None:
        super().__init__()
        
        # Change to a unique page state so our event listeners register correctly
        self.change_page(new_state="test")
        
    @override
    def init(self) -> None:
        super().init()
        self.init_background(image_key="background_image1")

        # Create a simple Red Surface for testing
        red_surf = Surface((100, 150))
        red_surf.fill((200, 50, 50))
        pygame.draw.rect(red_surf, (255, 255, 255), red_surf.get_rect(), width=3)

        # Create a simple Blue Surface for testing
        blue_surf = Surface((100, 150))
        blue_surf.fill((50, 50, 200))
        pygame.draw.rect(blue_surf, (255, 255, 255), blue_surf.get_rect(), width=3)

        # Initialize the two draggable components
        self.red_card: DraggableComponent = DraggableComponent(image=red_surf, base_pos=(300, 300), data_key="Red Card") # pyright: ignore[reportUninitializedInstanceVariable]
        self.blue_card: DraggableComponent = DraggableComponent(image=blue_surf, base_pos=(660, 300), data_key="Blue Card") # pyright: ignore[reportUninitializedInstanceVariable]

        # Assign the drop callback so they know what to do when you let go of the mouse
        self.red_card.on_drop = self.handle_drop
        self.blue_card.on_drop = self.handle_drop

        # Keep a list of all draggables on the screen for easy collision checking
        self.all_draggables: list[DraggableComponent] = [self.red_card, self.blue_card] # pyright: ignore[reportUninitializedInstanceVariable]

    def handle_drop(self, dropped_comp: DraggableComponent) -> None:
        """Fires whenever a card is dropped. Checks for collisions and swaps positions."""
        # Check if the card we just dropped is touching any other card in our list
        target = dropped_comp.check_collision(self.all_draggables)

        if target:
            print(f"Collision! Swapping {dropped_comp.data_key} with {target.data_key}")
            
            # Swap their home positions
            temp_pos = dropped_comp.home_pos
            dropped_comp.set_home(target.home_pos)
            target.set_home(temp_pos)
            
            # Update the layout of the target so it snaps to its new home immediately
            target.update_layout()
        else:
            print(f"{dropped_comp.data_key} dropped in empty space.")

        # Always update the dropped card so it snaps to its home position (whether old or new)
        dropped_comp.update_layout()

    @override
    def add_events(self) -> None:
        super().add_events()
        # Register the drag events for both cards using our specific page state
        self.red_card.add_event_listeners(page_state="test")
        self.blue_card.add_event_listeners(page_state="test")

    @override
    def update_layout(self) -> None:
        super().update_layout()
        self.red_card.update_layout()
        self.blue_card.update_layout()

    @override
    def draw(self) -> None:
        super().draw()
        
        # To make sure the card you are currently dragging always renders on top,
        # draw the inactive cards first, and the dragging card last.
        for card in self.all_draggables:
            if not card.dragging:
                card.draw()
                
        for card in self.all_draggables:
            if card.dragging:
                card.draw()