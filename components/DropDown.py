from pygame.rect import Rect

from pygame.rect import Rect
from pygame.surface import Surface
from pygame.typing import ColorLike
import pygame

from components.Button import Button, ImageOption
from components.Image import Anchor, ImageComponent, TextOption
from util import EventListenerInputRule
from util.GlobalHolder import GlobalHolder

from CustomTypes import ActionFunction, ConditionalFunction, PageType

class DropDown(GlobalHolder):
    def __init__(self, items: list[str], dropdown_surface: ImageComponent, item_sizes: tuple[int, int], menu_position: tuple[int, int], menu_anchor: Anchor = "topleft",
        item_spacing: int = 4, item_image: Surface | None = None, item_selected_image: Surface | None = None, item_color: ColorLike = (230, 235, 240), item_selected_color: ColorLike = (160, 170, 180)  ) -> None:
        
        # Store the information to an attribute
        self._labels: list[str] = list[str](items)
        self._item_sizes: tuple[int, int] = item_sizes
        self._menu_position: tuple[int, int] = menu_position
        self._menu_anchor: Anchor = menu_anchor
        self._item_spacing: int = item_spacing
        
        # Store image variations
        self._item_image: Surface | None = item_image
        self._item_selected_image: Surface | None = item_selected_image
        
        # Fallback colors if images aren't provided
        self._item_color: ColorLike = item_color
        self._item_selected_color: ColorLike = item_selected_color

        # The icon component
        self.dropdown_surface: ImageComponent = dropdown_surface
        self.temp_dropdown_surface: Surface = pygame.transform.rotate(surface=dropdown_surface._raw_image, angle=180)
        self.focus_on_dropdown: bool = False

        self.dropdown_background_surface: ImageComponent

        
        # Track whether the options menu is visible and which item is selected.
        self.is_open: bool = False
        self.selected_index: int | None = None
        self.selected_item: str | None = None

        # Callback function, whenever the selected item changes.
        self.on_change: ActionFunction = lambda: print(f"The dropdown selected '{self.selected_item}'")

        # Buttons are created during initialization from the supplied labels.
        self.items: list[Button] = []

        # Buttons lists are initialised
        self.init()
        self.update_layout()
    
    def init(self) -> None:
        #self.dropdown_background_surface = ImageComponent(image_option=ImageOption(colored_image=( (255, 255, 255) , (int(self._item_sizes[0] * 1.1), int((self._item_sizes[1] * len(self.items))*1.1) )), round_edges=5 ).raw_image, base_pos=self._menu_position, anchor="topright")
                
        # Create a colored surface with smooth edge when the _item_image is not there
        if self._item_image is None: self._item_image = ImageOption(colored_image=(self._item_color, self._item_sizes), round_edges=round(number=3 * self.scale)).raw_image
        # Ensure custom images match the given size
        self._item_image = pygame.transform.smoothscale(surface=self._item_image, size=self._item_sizes)

        # Create a colored surface with smooth edge when the _item_image is not there for the selected items
        if self._item_selected_image is None: self._item_selected_image = ImageOption(colored_image=(self._item_selected_color, self._item_sizes), round_edges=round(number=3 * self.scale)).raw_image
        # Ensure the image match the given size
        self._item_selected_image = pygame.transform.smoothscale(surface=self._item_selected_image, size=self._item_sizes)

        for i, label in enumerate(self._labels):
            # Calculate y offset including the item height AND the spacing
            y_offset: int = i * (self._item_sizes[1] + self._item_spacing)
            item_position: tuple[int, int] = (self._menu_position[0], self._menu_position[1] + y_offset)
            
            # Apply base image or fallback color

            item_button: Button = Button(image_option=ImageOption(image=self._item_image), text_option=TextOption(text=label, size=10, color=(70, 80, 95)), position=item_position, anchor=self._menu_anchor, outline_thickness=2)
            item_button.on_activate = self._make_select_action(index=i)
            self.items.append(item_button)
        
        # Use the first and last item rectangles to determine the full menu length and width.
        first_rect: Rect = self.items[0].surface.rect
        last_rect: Rect = self.items[-1].surface.rect
        #menu_bg_rect = Rect(first_rect.x, first_rect.y, first_rect.width * 1.02, (last_rect.bottom - first_rect.top)*1.02)
        # Centre the background around all items and add a small padding margin.
        self.dropdown_background_surface = ImageComponent(image_option=ImageOption(colored_image=( (255, 255, 255) , (int(first_rect.width * 1.1), int((last_rect.bottom - first_rect.top)*1.1) )), round_edges=5 ).raw_image, base_pos=(first_rect.centerx, (first_rect.top + last_rect.bottom) // 2), anchor="center")
        

    def _make_select_action(self, index: int) -> ActionFunction:
        def select_item() -> None:
            self.select_item(index=index)
        return select_item

    def _focus_on_dropdown(self) -> None: self.focus_on_dropdown = True
    
    def _unfocus_on_dropdown(self) -> None: self.focus_on_dropdown = False

    def update(self) -> None:
        return

    def toggle(self) -> None:
        if self.is_open:
            self.close()
        else:
            self.open_menu()
    
    def change_dropdown(self) -> None:
        temp: Surface = self.dropdown_surface._raw_image
        self.dropdown_surface._raw_image = self.temp_dropdown_surface
        self.temp_dropdown_surface = temp
        self.update_layout()

    def open_menu(self) -> None:
        self.is_open = True
        self.change_dropdown()

    def close(self) -> None:
        self.is_open = False
        self.change_dropdown()
        for item_button in self.items:
            item_button.disable_focus()

    def select_item(self, index: int) -> None:
        if index < 0 or index >= len(self._labels):
            return

        self.selected_index = index
        self.selected_item = self._labels[index]
        
        # Swap images/colors to highlight the active selection
        assert self._item_image is not None
        assert self._item_selected_image is not None
        item_image: Surface = self._item_image
        selected_image: Surface = self._item_selected_image

        for i, item_button in enumerate[Button](self.items):
            if i == self.selected_index:
                item_button.surface._raw_image = selected_image
            else:
                item_button.surface._raw_image = item_image
        
        self.change_dropdown()
        #self.update_layout()
        self.close()
        self.on_change()

    def add_event_listeners(self, page_state: PageType, condition: ConditionalFunction | None = None) -> None:
        self.event_manager.add_event_listener(page_state=page_state, event_rule=EventListenerInputRule(action=self._focus_on_dropdown, hover_rect=self.dropdown_surface.rect, mouse_action="enter", condition=condition))
        self.event_manager.add_event_listener(page_state=page_state, event_rule=EventListenerInputRule(action=self._unfocus_on_dropdown, hover_rect=self.dropdown_surface.rect, mouse_action="exit", condition=condition))
        self.event_manager.add_event_listener(page_state=page_state, event_rule=EventListenerInputRule(action=self.toggle, hover_rect=lambda: self.dropdown_surface.rect, mouse_action="clicked", condition=condition))

        for item_button in self.items:
            item_button.add_event_listeners(page_state=page_state, condition=lambda: self.is_open and (condition() if condition is not None else True))

    def update_layout(self) -> None:
        self.dropdown_surface.update_layout()
        self.dropdown_background_surface.update_layout()
        for item_button in self.items:
            item_button.update_layout()


    def draw(self) -> None:
        # 1. Draw the Icon, rotating it 180 degrees if the dropdown is open
        self.dropdown_surface.draw()

        # 2. Draw the Dropdown Options
        if self.is_open and len(self.items) > 0:
            self.dropdown_background_surface.draw()

            # Draw buttons and their hover outlines
            for item_button in self.items:
                item_button.draw()