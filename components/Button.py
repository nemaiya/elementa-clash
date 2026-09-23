from typing import Literal, TypeAlias

from pygame.surface import Surface
from pygame.typing import ColorLike
from components.Image import Anchor, ImageComponent, TextImageComponent, TextOption
from util import EventListenerInputRule
from util.GlobalHolder import GlobalHolder
import pygame
from CustomTypes import ActionFunction, ConditionalFunction, PageType


ShapeType: TypeAlias = Literal["rect", "circle"]
class ImageOption():
    def __init__(self, image: Surface | None = None, colored_image: tuple[ColorLike, tuple[int, int]] = ("#7c5cfa", (100, 200)), round_edges: int = 0, shape: ShapeType = "rect") -> None:
        self.raw_image: Surface

        if image: 
            self.raw_image = image
        else: 
            #self.raw_image = Surface(size=colored_image[1])
            #_ = self.raw_image.fill(color= colored_image[0])
            # Create a surface with SRCALPHA so the background is transparent (invisible corners)
            self.raw_image = Surface(size=colored_image[1], flags=pygame.SRCALPHA)
            
            # Draw a rounded rectangle onto our transparent surface
            if shape == "rect":
                _ = pygame.draw.rect(surface=self.raw_image, color=colored_image[0], rect=self.raw_image.get_rect(), border_radius=round_edges)
            else:
                # Draw a circle instead 
                circle_radius: int = max(colored_image[1][0] // 2, colored_image[1][1] // 2)
                _ = pygame.draw.circle(surface=self.raw_image, color=colored_image[0], center=(circle_radius, circle_radius), radius=circle_radius)

        
class Button(GlobalHolder):

    def __init__(self, image_option: ImageOption, text_option: TextOption, key: int | None = None, position: tuple[int, int] = (0, 0), anchor: Anchor = "topleft", outline_color: tuple[int, int, int] = (195, 179, 147), outline_thickness: int = 3) -> None:
        #self._text: str = text
        #self._text_color: ColorLike = text_color
        #self._text_align: Align  = "center"

        self.outline_color: tuple[int, int, int] = outline_color
        self.outline_thickness: int = outline_thickness
        #Old: self._raw_surface: Surface = image_option.raw_image 

        # This line directly stores the surface inside the image component
        self.surface: ImageComponent = ImageComponent(image_option=image_option.raw_image, base_pos=position, anchor=anchor)

        print(f"{text_option.text}: {self.surface.rect.center}")
        self.text_surface: TextImageComponent = TextImageComponent(text_option=text_option, base_pos=self.surface.rect.center, anchor="center")

        # Store the optional keyboard key used to identify this button.
        self._key: int | None = key
        # Track both the current and original position for layout updates.
        #self._position: tuple[int, int] = position
        #self._raw_position: tuple[int, int] = position
        # Indicates whether this button currently has focus.
        self.active: bool = False
        self.focused: bool = False

        # Event's
        self.on_activate: ActionFunction = lambda: print(f"The button with the label '{self.text_surface.text_option.text}' as activated")

        # Initialize the display surface and release the temporary option object.
        self.init()
        self.update_layout()
        del image_option

    def update(self) -> None:
        return


    def init(self) -> None:
        # Start with the button's original image before any layout resizing.
        #self._image: Surface = self._raw_surface
        #self._image_rect: Rect = self._image.get_rect()
        return

    def enable_focus(self) -> None: 
        print(f"Toggled focus on")
        self.focused = True
    def disable_focus(self) -> None: 
        print("Toggled focus off")
        self.focused = False


    def add_event_listeners(self, page_state: PageType, condition: ConditionalFunction | None = None) -> None:
        if self._key: self.event_manager.add_event_listener(page_state=page_state, event_rule=EventListenerInputRule(action=self.on_activate, keys=[(self._key, "released")], condition=condition))

        self.event_manager.add_event_listener(page_state=page_state, event_rule=EventListenerInputRule(action=self.on_activate, hover_rect=self.surface.rect, mouse_action="clicked", condition=condition))

        self.event_manager.add_event_listener(page_state=page_state, event_rule=EventListenerInputRule(action=self.enable_focus, hover_rect=self.surface.rect, mouse_action="enter", condition=condition))
        self.event_manager.add_event_listener(page_state=page_state, event_rule=EventListenerInputRule(action=self.disable_focus, hover_rect=self.surface.rect, mouse_action="exit", condition=condition))

    
    def update_layout(self) -> None:
        self.surface.update_layout()
        self.text_surface.update_layout()
        print("Updated layout Buttons")
        # Bug
        # self._image = self.resize_image(image=self._image)

        # Always resize from the original surface so repeated layout updates, so the image always has a base size to resize from
        # self._image = self.resize_image(image=self._raw_surface)
        # Recalculate the position from its original coordinates for the same reason

        # Get the position from the resized image
        # Old : self._position = self._image.get_rect().topleft

        # Recalculate the position from its original coordinates for the same reason
        # self._position = self.resize_position(position=self._raw_position)

        # New code
        # image_rect: Rect = self._image.get_rect(topleft=self._position)
        # self._image_rect.update(image_rect)
        #print(f"The size of the image {self._image.get_size()} when the screen size is {self.screen_manager.current_size}")
        #print(f"The size of the position {self._image.get_size()} when the screen size is {self.screen_manager.current_size}")
        #print()

    def draw(self) -> None:
        # Draw the image into the screen by first checking the focused state of the button
        if self.focused:
            # When the button is focused the button will draw outline version of the button image
            if not self.surface.outline_image: self.surface.create_outline(image_component=self.surface, color=self.outline_color, thickness=self.outline_thickness)
            self.surface.draw_outline()
        else:
            # In normal circumstances the button is drawn normally
            self.surface.draw()

        # Draw the text
        self.text_surface.draw()


        #text_surface: Surface = self.resize_image(image=self.font_manager.render(text=self._text, size=15, color=self._text_color, align=self._text_align))
        #position_rect: Rect = text_surface.get_rect(center=self.surface.rect.center)
        #_ = self.screen_manager.blit(source=text_surface, dest=position_rect)

        # Check if the Button works with a key before rendering/drawing
        if self._key:
            self.draw_key_label(key=self._key, image_rect=self.surface.rect)
    
    def change_base_position(self, position: tuple[int, int]) ->  None:
        self.surface._raw_base_pos = position
        self.surface.rect.update(self.surface.image.get_rect(**{self.surface._anchor: position}))
        
        self.text_surface._raw_base_pos = self.surface.rect.center
        self.text_surface.rect.update(self.text_surface.image.get_rect(**{self.text_surface._anchor: self.text_surface._raw_base_pos}))

        self.surface.update_layout()
        self.text_surface.update_layout()