from pygame.rect import Rect
from pygame.surface import Surface
import pygame
from typing import Any, Callable

from components.Image import ImageComponent, Anchor
from components.Button import ImageOption
from util import EventListenerInputRule
from util.GlobalHolder import GlobalHolder
from CustomTypes import PageType


class DraggableComponent(GlobalHolder):
    def __init__(self, image: Surface | str, base_pos: tuple[int, int], data_key: str | None = None, anchor: Anchor = "center") -> None:
        # The underlying visual image
        self.surface: ImageComponent = ImageComponent(image_option=image, base_pos=base_pos, anchor=anchor)
        
        # The data this card represents (e.g., "jean", "sword")
        self.data_key: str | None = data_key
        
        # Dragging state variables
        self.dragging: bool = False
        self.drag_offset: tuple[int, int] = (0, 0)
        
        # Where the card should snap back to if dropped in an invalid spot
        self.home_pos: tuple[int, int] = base_pos
        
        # Callback triggered when the player releases the mouse
        # Passes itself so the Page can check collisions and swap data
        self.on_drop: Callable[["DraggableComponent"], None] = lambda comp: None
        
        self.update_layout()

    def add_event_listeners(self, page_state: PageType, condition: Callable[[], bool] | None = None) -> None:
        
        def begin_drag() -> None:
            self.dragging = True
            mouse_pos = pygame.mouse.get_pos()
            
            # Calculate exactly where on the card we clicked
            self.drag_offset = (self.surface.rect.x - mouse_pos[0], self.surface.rect.y - mouse_pos[1])
            
            # Play grab sound if you want
            # self.music_manager.play_sfx("card_grab")

        def drag() -> None:
            pass # Keep event active; visual update happens in draw()

        def end_drag() -> None:
            if self.dragging:
                self.dragging = False
                self.on_drop(self) # Tell the DeckPage we dropped it!

        # 1. Click to grab
        self.event_manager.add_event_listener(
            page_state=page_state, 
            event_rule=EventListenerInputRule(action=begin_drag, hover_rect=lambda: self.surface.rect, mouse_action="clicked", condition=condition)
        )
        
        # 2. Hold to drag
        self.event_manager.add_event_listener(
            page_state=page_state, 
            event_rule=EventListenerInputRule(action=drag, mouse_action="holding", condition=lambda: self.dragging and (condition() if condition else True))
        )
        
        # 3. Release to drop
        self.event_manager.add_event_listener(
            page_state=page_state, 
            event_rule=EventListenerInputRule(action=end_drag, mouse_action="released", condition=lambda: self.dragging and (condition() if condition else True))
        )

    def check_collision(self, others: list["DraggableComponent"]) -> "DraggableComponent | None":
        """Checks if this component's rect is overlapping with any other component in the provided list."""
        for other in others:
            if other is not self and self.surface.rect.colliderect(other.surface.rect):
                return other
        return None

    def set_home(self, new_pos: tuple[int, int]) -> None:
        """Updates the rest position of the card."""
        self.home_pos = new_pos
        self.surface._raw_base_pos = new_pos
        self.update_layout()

    def update_layout(self) -> None:
        # Only snap back to home position if we aren't currently dragging it
        if not self.dragging:
            self.surface._raw_base_pos = self.home_pos
            self.surface.update_layout()

    def draw(self) -> None:
        if self.dragging:
            print(f"Dragging {self.data_key} at {self.surface.rect.topleft} with offset {self.drag_offset}")
            # Dynamically move the rect to follow the mouse using the offset
            mouse_pos = pygame.mouse.get_pos()
            new_x = mouse_pos[0] + self.drag_offset[0]
            new_y = mouse_pos[1] + self.drag_offset[1]
            
            self.surface.rect.topleft = (new_x, new_y)
            self.surface.position = getattr(self.surface.rect, self.surface._anchor)
            # Draw a white outline around the card while dragging
            if not self.surface.outline_image:
                self.surface.create_outline(image_component=self.surface, color=(255, 255, 255), thickness=3)
            self.surface.draw_outline()
        else:
            self.surface.draw()