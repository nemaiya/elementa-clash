from pygame.surface import Surface
import pygame

from util import ScreenManager, EventListenerManager, MusicManager, FontManager, images
from pathlib import Path

from .DataBase.Database import MasterDatabase
from util.CursorManager import CursorManager
from util.Game.Player import Player, UserInfo

class GlobalHolder:
    FPS: int | None = 60
    running: bool = True  # This is used to check if the game is running or not, this is used to stop the game when the user closes the window
    screen_manager: ScreenManager = ScreenManager(icon_path=images["game_icon_64_64"])  # This is the main screen manager that holds the methods created by the Screen Manager Class
    cursor_manager: CursorManager = CursorManager()
    music_manager: MusicManager = MusicManager()  # This is the main music manager that loads, loops, and controls music and sfx volume
    event_manager: EventListenerManager = EventListenerManager(music_manager=music_manager)# This is the main event manager that holds the methods created by the Event Listener Manager Class
    font_manager: FontManager = FontManager()
    loaded_images: dict[str, Surface] = {} # Used to store raw images

    db: MasterDatabase = MasterDatabase() # This is the main database manager that holds the methods created by the Database Class

    scale: float = 1.00

    player: Player | None = None

    # Undocumented
    def determine_scale(self) -> None:
        GlobalHolder.scale =  min( 
            ( self.screen_manager.current_size[0] / self.screen_manager.base_size[0] ),
            ( self.screen_manager.current_size[1] / self.screen_manager.base_size[1] )
        )
    # Undocumented
    # Old way: def resize_image(self, image: Surface, size: tuple[int, int] | None) -> Surface:
    @staticmethod
    def resize_image(image: Surface, size: tuple[int, int] | None = None) -> Surface:
        size = size if size is not None else image.get_size()
        # scaled_size= self.scale(size=size)
        # New
        scaled_size: tuple[int, int] = (
            round(number=size[0] * GlobalHolder.scale),
            round(number=size[1] * GlobalHolder.scale)
        )
        return pygame.transform.smoothscale(surface=image, size=scaled_size)
    
    #Old way: def resize_position(self, position: tuple[int, int]) -> tuple[int, int]:
    @staticmethod
    def resize_position2(position: tuple[int, int]) -> tuple[int, int]:
        return (
            # Old way: round(number=position[0] * self.scale),
            round(number=position[0] * GlobalHolder.scale),
            # Old way: round(number=position[0] * self.scale),
            round(number=position[1] * GlobalHolder.scale)
        )

    @staticmethod
    def resize_position(position: tuple[int, int]) -> tuple[int, int]:
        # Calculate the size of the base resolution when scaled up
        scaled_base_w: float = GlobalHolder.screen_manager.base_size[0] * GlobalHolder.scale
        scaled_base_h: float = GlobalHolder.screen_manager.base_size[1] * GlobalHolder.scale
        
        # Calculate the leftover space and split it in half to center the elements
        offset_x: float = (GlobalHolder.screen_manager.current_size[0] - scaled_base_w) / 2
        offset_y: float = (GlobalHolder.screen_manager.current_size[1] - scaled_base_h) / 2

        return (
            round(number=(position[0] * GlobalHolder.scale) + offset_x),
            round(number=(position[1] * GlobalHolder.scale) + offset_y)
        )

    @staticmethod
    def resize_background(image: Surface) -> Surface:
        image_size: tuple[int, int] = image.get_size()

        scaled_size: tuple[int, int] = (
            int(image_size[0] / GlobalHolder.screen_manager.base_size[0] * GlobalHolder.screen_manager.current_size[0] ),
            int(image_size[1] / GlobalHolder.screen_manager.base_size[1] * GlobalHolder.screen_manager.current_size[1] )
        )
        return pygame.transform.smoothscale(surface=image, size=scaled_size)
    
    # Old Code: def load_image(self, image_key: str) -> Surface:
    @staticmethod
    def load_image(image_key: str) -> Surface:
        image_path: Path = images[image_key]

        if GlobalHolder.loaded_images.get(image_key):
            return GlobalHolder.loaded_images[image_key]

        GlobalHolder.loaded_images[image_key] = pygame.image.load(file=image_path).convert_alpha()
        return GlobalHolder.loaded_images[image_key]
    
    

    def draw_key_label2(self, key: int, surface: Surface) -> None:
        top_right_dimension: tuple[int, int] = surface.get_rect().topright
        text_surface: Surface = self.font_manager.render(text=pygame.key.name(key=key),size=9)
        width, height = text_surface.get_size()
        padding = 2
        image: Surface = Surface(size=(width + padding * 2, height + padding * 2), masks="##fffaf0")
        _= image.blit(source=text_surface, dest=(padding, padding))
        label_surface: Surface = self.resize_image(image=image)
        _ = self.screen_manager.blit(source=label_surface,dest=top_right_dimension)
        
    def draw_key_label(self, key: int, image_rect: pygame.Rect) -> None:
        # 1. Render the text
        text_surface: Surface = self.font_manager.render(text=pygame.key.name(key=key).upper(), size=10, color="#000000")
        ts_w, ts_h = text_surface.get_size()
        padding = 4

        # 2. Create the badge background surface with transparency
        background_surface: Surface = Surface(size=(ts_w + padding * 2, ts_h + padding * 2), flags=pygame.SRCALPHA)

        # 3. Draw a rounded rectangle onto the badge surface
        badge_rect = background_surface.get_rect()
        _ = pygame.draw.rect(surface=background_surface,color=(255, 250, 240),rect=badge_rect,border_radius=4,)

        # 4. Center and blit the text onto the badge
        text_rect = text_surface.get_rect(center=badge_rect.center)
        _ = background_surface.blit(source=text_surface, dest=text_rect)

        # 5. Scale the finished badge using your resolution-independent scaler
        scaled_badge: Surface = self.resize_image(image=background_surface)

        # 6. Position using center alignment on the target rect's topright, then blit
        position_rect = scaled_badge.get_rect(center=image_rect.topright)
        _ = self.screen_manager.blit(source=scaled_badge, dest=position_rect)