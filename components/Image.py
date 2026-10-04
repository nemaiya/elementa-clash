from pygame.mask import Mask
import pygame
from pygame import Surface, Rect
from typing import TypeAlias, Literal, override
from typing import final

from pygame.typing import ColorLike

from util.FontManager import Align
from util.GlobalHolder import GlobalHolder

Anchor: TypeAlias = Literal["topleft", "topright", "center"]

class ImageComponent():
    def __init__(self, image_option: str | Surface, base_pos: tuple[int, int], anchor: Anchor = "topleft")-> None:
        # Store the original image so it can be resized during layout updates.
        self._raw_image: Surface

        # Resolve image keys through the global holder; otherwise use the supplied surface.
        if type(image_option) == str: self._raw_image = GlobalHolder.load_image(image_key=image_option)
        elif type(image_option) == Surface: self._raw_image = image_option

        # Keep the original position as the reference for responsive layout changes.
        self._raw_base_pos: tuple[int, int] = base_pos
        # Store the point on the image that is aligned to the position.
        self._anchor: Anchor = anchor
        # Used to hold the color of the outline
        self.outline_color: tuple[int, int, int] = (0, 0, 0)
        # Used to hold the thickness of the outline
        self.outline_thickness: int = 0
        # The final output image with outline
        self.outline_image: Surface | None = None

        # Initialise the displayed image and its drawing rectangle.
        self.image: Surface = self._raw_image
        self.position: tuple[int, int] = self._raw_base_pos
        self.rect: Rect = self.image.get_rect(**{self._anchor: self.position})
        return
    
    def cal_rect(self) -> None:
        self.rect: Rect = self.image.get_rect(**{self._anchor: self.position})

    def update_position_only(self, new_scaled_pos: tuple[int, int]) -> None:
        """Directly updates the scaled rect position without resizing the image (Best for dragging)."""
        self.position = new_scaled_pos
        self.rect.update(self.image.get_rect(**{self._anchor: self.position}))


    def update_layout(self) -> None:
        # Resizes the position
        self.position = GlobalHolder.resize_position(position=self._raw_base_pos)
        # Resizes the image
        self.image = GlobalHolder.resize_image(image=self._raw_image)
        # Updates the rect with the correct placement
        self.rect.update(self.image.get_rect(**{self._anchor: self.position}))

        # Only update the layout if the outline_image is created once
        if self.outline_image:
            self.outline_image = self.create_outline(image_component=self, color=self.outline_color, thickness=self.outline_thickness)
    
    def draw(self) -> None:
        # Drawing it in the right spot in the screen.
        _ = GlobalHolder.screen_manager.blit(source=self.image, dest=self.rect)
    
    def draw_outline(self) -> None:
        # Check if the outline is already created before rendering anything on the screen
        if not self.outline_image: return
        # Render the outlined image on the same positions
        _ = GlobalHolder.screen_manager.blit(source=self.outline_image, dest=self.outline_image.get_rect(**{self._anchor: self.position}))

    @staticmethod
    def create_outline(image_component: "ImageComponent", color: tuple[int, int, int], thickness: int = 2) -> None:
        # Copy the image so the original surface is not modified.
        outline_img: Surface = image_component.image.copy()

        # Preserve the source alpha channel while replacing visible pixels with the outline colour.
        _ = outline_img.fill(color=(0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)
        _ = outline_img.fill(color=(*color, 0), special_flags=pygame.BLEND_RGBA_ADD)

        # Make the outline surface larger to leave room around every edge of the image.
        size: tuple[int, int] = (image_component.rect.width + (thickness * 2), image_component.rect.height + (thickness * 2))
        outline_img = pygame.transform.smoothscale(surface=outline_img, size=size)

        # Draw the original image in the centre, covering the middle of the outline.
        _ = outline_img.blit(source=image_component.image, dest=(thickness, thickness))

        # Store the generated outline and its settings for drawing and layout updates.
        image_component.outline_image = outline_img
        image_component.outline_color = color
        image_component.outline_thickness = thickness
        return

    @staticmethod
    def create_outline2(image_component: "ImageComponent", color: tuple[int, int, int], thickness: int = 2) -> None:
        # Create a mask from the image (this automatically finds the non-transparent pixels)
        mask: Mask = pygame.mask.from_surface(surface=image_component.image)
        # setcolor is our outline color, unsetcolor is fully transparent invisible pixels
        background: Surface = mask.to_surface(setcolor=color, unsetcolor=(0, 0, 0, 0))

        # Create a new blank surface big enough to fit the original image + the outline
        size: tuple[int, int] = (image_component.rect.width + (thickness * 2), image_component.rect.height + (thickness * 2))
        outlined_image: Surface = pygame.Surface(size=size, flags=pygame.SRCALPHA)

        for dx in range(-thickness, thickness + 1):
            for dy in range(-thickness, thickness + 1):
                # Only draw if the x/y offset falls inside a circle (this prevents blocky, square corners)
                if (dx ** 2) + (dy ** 2) <= (thickness ** 2):
                    # Blit the silhouette offset by our circle coordinates
                    _ = outlined_image.blit(source=background, dest=(thickness + dx, thickness + dy))

        _ = outlined_image.blit(source=image_component.image, dest=(thickness, thickness))

        image_component.outline_image = outlined_image
        image_component.outline_color = color
        image_component.outline_thickness = thickness
        return


@final
class BackgroundImageComponent(ImageComponent):
    @override
    def update_layout(self) -> None:
        self.position = GlobalHolder.resize_position(position=self._raw_base_pos)

        self.image = GlobalHolder.resize_background(image=self._raw_image)

        self.rect.update(self.image.get_rect(**{self._anchor: self.position}))


class TextOption():
    text: str = ""
    color: ColorLike
    # Same parameters as the one in Font Manager "render" method
    def __init__(self, text: str, size: int, color: ColorLike = (0, 0, 0), max_width: int | None = None, align: Align = "left", 
        bold: bool = False, italic: bool = False, underline: bool = False, font_key: str | None = None) -> None:

        self.text = text
        self.size : int = size
        self.color= color
        # Buggy
        # self.max_width: int | None = None
        self.max_width: int | None = max_width
        self.align: Align = align

        self.bold: bool = bold
        self.italic: bool = italic
        self.underline: bool = underline

        self.font_key: str | None = font_key
    
    def set_text(self, text: str) -> None: self.text = text
    def set_color(self, color: ColorLike) -> None: self.color = color

@final
class TextImageComponent(ImageComponent):

    @override
    def __init__(
        self,
        text_option: TextOption,
        base_pos: tuple[int, int],
        anchor: Anchor = "topleft"
    ) -> None:
        self.text_option: TextOption = text_option
        rendered_image: Surface = self.render()
        super().__init__(image_option=rendered_image, base_pos=base_pos, anchor=anchor)
        return
    
    def render(self) -> Surface:
        #print("Text Rendered")
        #print(self.text_option.__dict__)
        #print(f"U4: {self.text_option.text}")
        return GlobalHolder.font_manager.render(
            text=self.text_option.text,
            size=self.text_option.size,
            color=self.text_option.color,
            max_width=self.text_option.max_width,
            align=self.text_option.align,
            bold=self.text_option.bold,
            italic=self.text_option.italic,
            underline=self.text_option.underline,
            font_key=self.text_option.font_key,
        )

    @override
    def update_layout(self) -> None:
        #print(f"U5 BEFORE THE UPDATE LAYOUT {self.text_option.text}")
        self._raw_image = self.render()
        
        return super().update_layout()
    
    def set_text(self, text: str) -> None:
        self.text_option.set_text(text=text)
        self._raw_image = self.render()
        self.update_layout()