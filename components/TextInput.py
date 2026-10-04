from pygame.typing import ColorLike
from typing import Callable, final, override
from CustomTypes import PageType, ConditionalFunction
from util.EventListenerManager import EventListenerInputRule
from .Button import Button, ImageOption
from .Image import TextImageComponent, TextOption, Anchor
import pygame
from typing import TypeAlias

Validations: TypeAlias = tuple[Callable[[str], bool], str]

@final
class TextInput(Button):
    def __init__(self, image_option: ImageOption, text_option: TextOption, placeholder: str = "", key: int | None = None, position: tuple[int, int] = (0, 0), anchor: Anchor = "topleft", max_length: int = 15, password: bool = False, outline_color: tuple[int, int, int] = (195, 179, 147), outline_thickness: int = 3, validations: list[Validations] = []) -> None:
        
        self.placeholder: str = placeholder
        self.placeholder_text_color: tuple[int, int, int] = (78, 78, 78)
        self.type_password: bool = password
        self.max_length: int = max_length

        self.text: str = "" 
        self.text_color: ColorLike = text_option.color

        self.validations: list[Validations] = validations
        self.valid: bool = False

        text_option.set_text(text=self.placeholder)
        text_option.set_color(color=self.placeholder_text_color)

        self.active_typing: bool = False

        super().__init__(image_option, text_option, key, position, anchor, outline_color, outline_thickness)
        self.validations_text_surface: TextImageComponent = TextImageComponent(text_option=TextOption(text="", size=11, color=(194, 24, 7), max_width=int(self.surface.rect.width * 1.5), align="center"), base_pos=(self.surface.rect.centerx, int(self.surface.rect.y + self.surface.rect.height * 1.1)), anchor="center")
        self.on_activate = self._enable_typing

        self.errors: list[str] = []

    def _enable_typing(self) -> None:
        print("U6: Enabled Typing")
        self.active_typing = True
        self.event_manager.text_input_active = True
        
        # Link the manager's built-in callback directly to our handler
        self.event_manager.text_input_callback = self._handle_text_input
        
        pygame.key.start_text_input()
        self._update_text_display()

    def _disable_typing(self) -> None:
        print("U7: Disabled Typing")
        # Only run if we are actually typing, to prevent unnecessary updates
        if not self.active_typing:
            return 
            
        self.active_typing = False
        self.event_manager.text_input_active = False

        if id(self.event_manager.text_input_callback) == id(self._handle_text_input):
            self.event_manager.text_input_callback = None
        
        pygame.key.stop_text_input()
        self._update_text_display()

    def _update_text_display(self) -> None:
        if not self.active_typing and not bool(self.text):
            #print(f"U20: This placeholder is being called!")
            self.text_surface.text_option.set_text(text=self.placeholder)
            self.text_surface.text_option.set_color(color=self.placeholder_text_color)
        else:
            # Bug #2 Fixed: Only apply the | cursor if we are actively focused
            display_text = len(self.text) * "*" if self.type_password else self.text
            if self.active_typing:
                display_text += "|"

            self.text_surface.text_option.set_text(text=display_text)
            self.text_surface.text_option.set_color(color=self.text_color)
        
        # Bug #1 Fixed: You must trigger update_layout on the TEXT surface so it regenerates the image!
        #print(f"U1: {self.text_surface.text_option.text}")
        self.update_layout()
        #print(f"U2: {self.text_surface.text_option.text}")
        #pygame.image.save(surface=self.text_surface.image, file="test.png")
    
    # Produces errpr
    def validate_text2(self, text: str) -> None:
        for validate, err_text in self.validations:
            if validate(text): continue
            
            if self.validations_text_surface.text_option.text:
                self.validations_text_surface.text_option.text += f" & {err_text}"
            else:
                self.validations_text_surface.text_option.set_text(text=err_text)
    
    def validate_text(self, text: str) -> None:
        # Collect all current errors
        self.valid = True
        for validate, err_text in self.validations:
            if not validate(text):
                self.errors.append(err_text)
        
        # Join errors together, or clear the text if there are no errors
        if self.errors:
            self.valid = False
            self.validations_text_surface.text_option.set_text(text=" & ".join(self.errors))
        else:
            self.validations_text_surface.text_option.set_text(text="")
        
        self.errors = []
        # You MUST update the layout so the image surface regenerates with the new text!
        self.validations_text_surface.update_layout()
            

    def _handle_text_input(self, event: pygame.Event) -> None:
        """Triggered via EventListenerManager's text_input_callback"""
        typed_text: str = getattr(event, "text", "")

        if len(self.text) < self.max_length:
            self.text += typed_text
            self.validate_text(self.text)
            self._update_text_display()
            
    def _handle_backspace(self) -> None:
        """Triggered by EventListenerManager's key tracking"""
        if self.active_typing and self.text:
            self.text = self.text[:-1]
            self.validate_text(self.text)
            self._update_text_display()
    

    @override
    def add_event_listeners(self, page_state: PageType, condition: ConditionalFunction | None = None) -> None:
        super().add_event_listeners(page_state, condition)
        
        # Helper function to prevent Python late-binding closure bugs
        active_condition = lambda c=condition: self.active_typing and (c() if c else True)

        # 1. Clicking outside the box disables typing
        # (Note: Changed self.surface.rect to self.rect to match your ImageComponent attributes)
        self.event_manager.add_event_listener(page_state=page_state, event_rule=EventListenerInputRule(
            action=self._disable_typing, hover_rect=self.surface.rect, mouse_action="unclick", condition=active_condition 
        ))

        # 2. Text input trigger 
        # Bug #3 Fixed: This MUST use active_condition so background textboxes don't steal keystrokes
        self.event_manager.add_event_listener(page_state=page_state, event_rule=EventListenerInputRule(
            action=lambda: None, 
            py_event=pygame.TEXTINPUT, 
            condition=active_condition
        ))
        
        # 3. Handle Backspace using your manager's native key tracking system!
        self.event_manager.add_event_listener(page_state=page_state, event_rule=EventListenerInputRule(
            action=self._handle_backspace, 
            keys=[(pygame.K_BACKSPACE, "holding"), (pygame.K_BACKSPACE, "pressed")], 
            hold_time_ms=75,
            condition=active_condition
        ))
        
        # 4. Handle Enter / Escape using your manager's native key tracking system!
        self.event_manager.add_event_listener(page_state=page_state, event_rule=EventListenerInputRule(
            action=self._disable_typing, 
            keys=[(pygame.K_RETURN, "pressed"), (pygame.K_KP_ENTER, "pressed"), (pygame.K_ESCAPE, "pressed")], 
            condition=active_condition
        ))
    
    @override
    def draw(self) -> None:
        super().draw()
        
        if self.validations_text_surface.text_option.text:
            self.validations_text_surface.draw()
    
    @override
    def update_layout(self) -> None:
        super().update_layout()
        if hasattr(self, 'validations_text_surface') and self.validations_text_surface.text_option.text:
            self.validations_text_surface.update_layout()

    def clear_text(self) -> None:
        self.text = ""
        #self.validate_text(self.text)
        self._update_text_display()
    
    def set_text(self, text: str) -> None:
        self.text = text
        self.validate_text(self.text)
        self._update_text_display()

    @override
    def change_base_position(self, position: tuple[int, int]) -> None:
        super().change_base_position(position)

        self.validations_text_surface._raw_base_pos = (self.surface.rect.centerx, int(self.surface.rect.y + self.surface.rect.height * 1.1))
        self.validations_text_surface.rect.update(self.validations_text_surface.image.get_rect(**{self.validations_text_surface._anchor: self.validations_text_surface._raw_base_pos}))