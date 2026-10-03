from pygame.rect import Rect

import pygame

from components.Button import ImageOption
from components.Image import Anchor, ImageComponent
from util import EventListenerInputRule
from util.GlobalHolder import GlobalHolder

from CustomTypes import ActionFunction, ConditionalFunction, PageType


class Slider(GlobalHolder):

    def __init__(self, track_option: ImageOption, knob_option: ImageOption, position: tuple[int, int] = (0, 0), anchor: Anchor = "topleft",min_value: float = 0.0, max_value: float = 1.0, value: float = 0.0, rate_of_change: float = 0.05, key_decrease: int | None = None, key_increase: int | None = None) -> None:
        # Slider upper and lower bounds and step size for value updates.
        self.min_value: float = min_value
        self.max_value: float = max_value
        self.rate_of_change: float = rate_of_change

        # The track & knob image component is created
        self.track: ImageComponent = ImageComponent(image_option=track_option.raw_image, base_pos=position, anchor=anchor)
        # The knob is always to be placed from the center axis
        self.knob: ImageComponent = ImageComponent(image_option=knob_option.raw_image, base_pos=position, anchor="center")

        # keyboard controls for adjusting the slider value.
        self._key_decrease: int | None = key_decrease
        self._key_increase: int | None = key_increase


        #self.active: bool = False
        # determines When the mouse is hovered into the rects 
        self.focused: bool = False
        # When the rect are being dragged
        self.dragging: bool = False
        # self.outline_on_focus: bool = True

        # Callback triggered whenever the slider value changes.
        self.on_change: ActionFunction = lambda: print(f"The slider value changed to '{self.value}'")

        # Clamp the initial value to the valid range and initialise layout.
        self.value: float = self._clamp(value=value)
        self.init()
        self.update_layout()

        # Remove references to the passed-in option objects after setup.
        del track_option
        del knob_option

    def update(self) -> None:
        return

    def init(self) -> None:
        return

    def enable_focus(self) -> None:
        print("Toggled focus on")
        self.focused = True

    def disable_focus(self) -> None:
        print("Toggled focus off")
        self.focused = False

    def _clamp(self, value: float) -> float:
        return (max(self.min_value, min(self.max_value, value)))
        #lowest: float = min(self.min_value, self.max_value)
        #highest: float = max(self.min_value, self.max_value)
        #return max(lowest, min(highest, value))

    def get_hit_rect(self) -> Rect:
        return self.track.rect.union(self.knob.rect)

    def set_value(self, value: float, call_change: bool = True) -> None:
        # Keep the value within the slider's range.
        clamped_value: float = self._clamp(value=value)
        # Record whether the value actually changed before updating the layout.
        value_changed: bool = (clamped_value != self.value)
        self.value = clamped_value

        # Move the knob to reflect the new value.
        self.knob_update_layout()

        if value_changed and call_change:
            # Notify listeners only when the slider value has changed.
            self.on_change()

    def set_value_from_mouse(self) -> None:
        # Find the width of the track
        track_width: int = self.track.rect.width
        if track_width <= 0:
            # Avoid division by zero when the track has no usable width.
            return

        # Calculate the mouse position as a ratio of the track width.
        mouse_x: int = pygame.mouse.get_pos()[0]
        percentage: float = (mouse_x - self.track.rect.left) / track_width

        # Keep the ratio within the track before converting it to the value range.
        percentage = max(0.0, min(1.0, percentage))
        self.set_value(value=self.min_value + percentage * (self.max_value - self.min_value))


    def decrease(self) -> None:
        self.set_value(value=self.value - self.rate_of_change)

    def increase(self) -> None:
        self.set_value(value=self.value + self.rate_of_change)

    def add_event_listeners(self, page_state: PageType, condition: ConditionalFunction | None = None) -> None:
        # Register keyboard controls for changing the slider value only if they exist
        if self._key_decrease: self.event_manager.add_event_listener(page_state=page_state, event_rule=EventListenerInputRule(action=self.decrease, keys=[(self._key_decrease, "holding")], hold_time_ms=50, condition=condition))
        if self._key_increase: self.event_manager.add_event_listener(page_state=page_state, event_rule=EventListenerInputRule(action=self.increase, keys=[(self._key_increase, "holding")], hold_time_ms=50, condition=condition))

        def begin_drag() -> None:
            self.dragging = True
            self.set_value_from_mouse()
        # Start & Register dragging when the pointer clicks on the track or knob
        self.event_manager.add_event_listener(page_state=page_state, event_rule=EventListenerInputRule(action=begin_drag, hover_rect=lambda: self.get_hit_rect(), mouse_action="clicked", condition=condition))#

        def drag() -> None:
            if self.dragging: self.set_value_from_mouse()
        # Continue updating the value while the pointer button is held down
        self.event_manager.add_event_listener(page_state=page_state, event_rule=EventListenerInputRule(action=drag, mouse_action="holding", condition=lambda: self.dragging and (condition() if condition is not None else True)))
        
        def end_drag() -> None:
            self.dragging = False
        # Stop dragging when the pointer button is released
        self.event_manager.add_event_listener(page_state=page_state, event_rule=EventListenerInputRule(action=end_drag, mouse_action="released", condition=lambda: self.dragging and (condition() if condition is not None else True)))

        # Track when the mouse enters and exits the 
        self.event_manager.add_event_listener(page_state=page_state, event_rule=EventListenerInputRule(action=self.enable_focus, hover_rect=self.track.rect, mouse_action="enter", condition=condition))
        self.event_manager.add_event_listener(page_state=page_state, event_rule=EventListenerInputRule(action=self.disable_focus, hover_rect=self.track.rect, mouse_action="exit", condition=condition))

    def knob_update_layout(self) -> None:
        # Find the current position of the knob as a percentage of the slider's range.
        value_length: float = self.max_value - self.min_value

        percentage = 0.0
        if value_length != 0: percentage = (self.value - self.min_value) / value_length
        if percentage < 0: percentage = 0.0
        percentage = max(0.0, min(1.0, 0.0 if value_length == 0 else (self.value - self.min_value) / value_length))

        # Place the knob horizontally along the track keeping it centered on the track's height
        knob_x: int = self.track.rect.left + round(number=percentage * self.track.rect.width)

        # Rebuild the knob image at its current scale and update the rect to match the new position.
        self.knob.image = GlobalHolder.resize_image(image=self.knob._raw_image)
        self.knob.rect.update(self.knob.image.get_rect(center=(knob_x, self.track.rect.centery)))
        self.knob.position = self.knob.rect.center

        # If the outline_image exist then create a new one, since its created when the focus is on
        if self.knob.outline_image: self.knob.create_outline(image_component=self.knob, color=self.knob.outline_color)

    def update_layout(self) -> None:
        # Use the update_layout method to calculate the 
        self.track.update_layout()
        self.knob_update_layout()

    def draw(self) -> None:
        # Outline both components while the slider is focused or being dragged.
        if self.focused or self.dragging:

            # Rebuild the outlines using the appropriate colour before drawing them.
            if not self.track.outline_image: self.track.create_outline(image_component=self.track, color=(0,0,0))
            if not self.knob.outline_image: self.knob.create_outline(image_component=self.knob, color=(255, 255, 255))
            self.track.draw_outline()
            self.knob.draw_outline()
        else:
            # Draw the track first so the knob appears on top of it.
            self.track.draw()
            self.knob.draw()
