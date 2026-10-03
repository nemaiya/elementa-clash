from CustomTypes import ActionFunction, ConditionalFunction, PageType
from util import EventListenerInputRule
from util.GlobalHolder import GlobalHolder
from components.Image import ImageComponent
from components.Button import Button

class Toggle(GlobalHolder):
    def __init__(self, components: list[Button | ImageComponent] | None = None, toggle_only_when_focused: bool = True) -> None:
        # Store the list of components (Buttons or ImageComponents) to cycle through
        self.components: list[Button | ImageComponent] = components if components is not None else []
        self.current_index: int = 0
        
        # Rule: Should we only allow toggling if the component is currently hovered/focused?
        self.toggle_only_when_focused: bool = toggle_only_when_focused
        
        # Tracks the focus state specifically for the Toggle (useful if holding standard ImageComponents)
        self.focused: bool = False
        
        # Callback you can overwrite to trigger logic when the toggle happens
        self.on_change: ActionFunction = lambda: print(f"Toggle switched to index {self.current_index}")

    @property
    def current_component(self) -> Button | ImageComponent | None:
        """Returns the currently active component."""
        if not self.components:
            return None
        return self.components[self.current_index]

    def cycle(self) -> None:
        """Moves to the next component in the list, wrapping back to 0 at the end."""
        if not self.components: 
            return
        
        # If the feature is enabled, verify the current component is actually focused
        if self.toggle_only_when_focused:
            comp = self.current_component
            
            # Buttons track their own focus natively. ImageComponents rely on the Toggle's focus state.
            comp_focused = getattr(comp, "focused", self.focused)
            if not comp_focused:
                return  # Abort the toggle because it's not being focused/hovered
                
        # Advance the index
        self.current_index = (self.current_index + 1) % len(self.components)
        self.on_change()

    def enable_focus(self) -> None:
        self.focused = True

    def disable_focus(self) -> None:
        self.focused = False

    def draw(self) -> None:
        """Draws ONLY the currently active component."""
        if self.current_component:
            self.current_component.draw()

    def update_layout(self) -> None:
        """Updates the layout for ALL components so they remain correctly sized in the background."""
        for comp in self.components:
            comp.update_layout()

    def add_event_listeners(self, page_state: PageType, condition: ConditionalFunction | None = None) -> None:
        """Binds the click and focus events dynamically for all components."""
        for i, comp in enumerate(self.components):
            
            # 1. Custom Condition: An event is ONLY allowed to trigger if this specific component is currently active
            def is_active(index=i, base_cond=condition) -> bool:
                active = (self.current_index == index)
                if base_cond is None:
                    return active
                return active and base_cond()

            # Safely grab the rect depending on if it's a Button or ImageComponent
            watch_rect = comp.surface.rect if isinstance(comp, Button) else comp.rect

            # 2. Add click event to cycle the toggle
            self.event_manager.add_event_listener(
                page_state=page_state, 
                event_rule=EventListenerInputRule(action=self.cycle, hover_rect=watch_rect, mouse_action="clicked", condition=is_active)
            )

            # 3. Handle specific Component logic
            if isinstance(comp, Button):
                # If it's a Button, initialize its own listeners (click sounds, focus outlines, etc.)
                # By passing 'is_active', inactive background buttons are completely ignored by the mouse!
                comp.add_event_listeners(page_state=page_state, condition=is_active)
            else:
                # If it's an ImageComponent, it doesn't track focus natively, so we track it for the Toggle manually
                self.event_manager.add_event_listener(
                    page_state=page_state, 
                    event_rule=EventListenerInputRule(action=self.enable_focus, hover_rect=watch_rect, mouse_action="enter", condition=is_active)
                )
                self.event_manager.add_event_listener(
                    page_state=page_state, 
                    event_rule=EventListenerInputRule(action=self.disable_focus, hover_rect=watch_rect, mouse_action="exit", condition=is_active)
                )