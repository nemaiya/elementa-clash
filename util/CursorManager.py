from pygame.cursors import Cursor
import pygame
from typing import ClassVar
from .AssetManager import images

class CursorManager:
    pointer_cursor: ClassVar[Cursor]
    hand_cursor: ClassVar[Cursor]


    def __init__(self) -> None:
        # Pre-load the cursor images so they can be reused without reloading from disk.
        CursorManager.pointer_cursor = Cursor((0, 0), pygame.image.load(file=images["cursor_pointer"]).convert_alpha())
        CursorManager.hand_cursor = Cursor((0, 10), pygame.image.load(file=images["cursor_hand"]).convert_alpha())
        # Set the default pointer cursor when the class is defined.
        pygame.mouse.set_cursor(self.pointer_cursor)


    @staticmethod
    def set_pointer_cursor() -> None:
        # Switch back to the standard pointer cursor.
        pygame.mouse.set_cursor(CursorManager.pointer_cursor)

    @staticmethod
    def set_hand_cursor() -> None:
        # Switch to the interactive hand cursor for clickable elements.
        pygame.mouse.set_cursor(CursorManager.hand_cursor)