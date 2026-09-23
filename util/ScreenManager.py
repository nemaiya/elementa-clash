from pygame.surface import Surface
from pathlib import Path
from typing import Any, TYPE_CHECKING
import pygame

# Trick static type checkers into seeing Surface methods without runtime side-effects
if TYPE_CHECKING:
    class _SurfaceProxy(Surface):
        pass
else:
    _SurfaceProxy = object

class ScreenManager(_SurfaceProxy):
    display_surface: Surface # This is the main display surface (aka screen) that is used to draw everything on the screen. This is the main surface that is used to draw everything on the screen.
    base_size: tuple[int, int] = (960, 540) # This is the base size of the screen, this is used to scale the screen when the window is resized
    current_size: tuple[int, int] = base_size # This is the current size of the screen, this is used to scale the screen when the window is resized
    is_maximized: bool = False # This is used to check if the window is maximized or not, this is used to scale the screen when the window is resized

    
    def __getattr__(self, name: str) -> Any: # pyright: ignore[reportAny, reportExplicitAny]
        return getattr(self.display_surface, name) # pyright: ignore[reportAny]
        

    def __init__(self, icon_path: Path) -> None: # pyright: ignore[reportMissingSuperCall]
        # Old: self.display_surface = pygame.display.set_mode(size=self.base_size)
        self.display_surface = pygame.display.set_mode(size=self.base_size, flags=pygame.RESIZABLE) # This is used to create the main display surface (aka screen) that is used to draw everything on the screen. This is the main surface that is used to draw everything on the screen.
        
        self.current_size = self.base_size
        self.center_points: tuple[int, int] = self.display_surface.get_rect().center

        # Set the game icon
        pygame.display.set_icon(pygame.image.load(file=str(icon_path)).convert_alpha())
        return

    def get_current_size(self) -> tuple[int, int]:
        return self.display_surface.get_size()

    def blur_screen(self, alpha: int = 128, size: tuple[int, int] | None = None) -> None:
        if size is None:
            size = self.display_surface.get_size()

        blur: Surface = pygame.Surface(
            size=size,
            flags = pygame.SRCALPHA
        )
        _ = blur.fill(color=(0, 0, 0, alpha))

        _ = self.display_surface.blit(source=blur, dest=(0 , 0))

    def set_caption(self, caption: str) -> None:
        pygame.display.set_caption(caption)
        return
