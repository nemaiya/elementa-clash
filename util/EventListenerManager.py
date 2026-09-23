#from pygame.cursors import Cursor


from typing import Callable

from CustomTypes import ActionFunction, ConditionalFunction, GetRectFunction, PageType, KeyState, MouseAction
from pygame import Rect, Event
import pygame

from util.CursorManager import CursorManager
from .AssetManager import images
from .MusicManager import MusicManager



class EventListenerInputRule():
    def __init__(
        self, 
        action: ActionFunction, 
        keys: list[tuple[int, KeyState]] | None = None,
        hover_rect: Rect | GetRectFunction | None = None,
        mouse_action: MouseAction | None = None,
        hold_time_ms: int = 0,
        py_event: int | None = None,
        condition: ConditionalFunction | None = None
        
    ) -> None:
        self.action: ActionFunction = action # This is the function that will be called when the event is triggered
        self.keys: list[tuple[int, KeyState]] = keys if keys is not None else [] # This is a list of tuples that contains the key and the state of the key (pressed, holding, released) that will trigger the event
        self.hover_rect: Rect | GetRectFunction | None = hover_rect # This is the rectangle that will trigger the event when the mouse is doing an action over it
        self.mouse_action: MouseAction | None = mouse_action # This is the mouse action that will trigger the event
        self.hold_time_ms: int = hold_time_ms # This is the time in milliseconds that the key or mouse action needs to be held down for the event to be triggered
        self.py_event: int | None = py_event # This is the pygame event that will trigger the event (e.g. pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN, etc.)

        # Used to check the condition required for this rule to run
        self.condition: ConditionalFunction | None = condition


class EventListenerManager():
    event_listeners: dict[PageType, list[EventListenerInputRule]] = {} # This is a dictionary that holds the event listeners for each page state, where the key is the page state and the value is a list of event listener input rules that will be triggered when the event is triggered on that page state.
    text_input_active: bool = False
    text_input_callback: Callable[..., None] | None = None

    hashed_events: set[int] = set[int]()
    BLOCKED_KEY_PRESSES_WHILST_TYPING: list[int] = [pygame.K_a + i for i in range(26)] + [pygame.K_0 + i for i in range(10)]
    
    def __init__(self) -> None:
        self._tracked_keys: set[int] = set[int]() # This is a set that holds the keys that are being tracked for the event listeners, this is used to check if the key is being held down or not
        self.current_keys: pygame.key.ScancodeWrapper | None = None # This is the current state of the keys
        self.previous_keys: pygame.key.ScancodeWrapper | None = None # This is the previous state of the keys
        self.key_press_timestamp: dict[int, int] = {} # This is a dictionary that holds the timestamp of when the key was pressed down, where the key is the key and the value is the timestamp in milliseconds, this is used to check if the key is being held down for the required amount of time
        # Undocumented
        # Holds the current mouse state which mouse buttons were being pressed
        # index1 holds left click, index 2 represents right click, index 3 represents scroll button click
        self.current_mouse: tuple[bool, bool, bool] = (False, False, False)
        # Holds the mouse state from the previous frame
        self.previous_mouse: tuple[bool, bool, bool] = (False, False, False)

        # This is used to track what button was mouse was at previous frame
        self.button_tracker: int | None = None
        #self.events: list[Event] = []
        return
    

    def add_event_listener(self, page_state: PageType, event_rule: EventListenerInputRule) -> None:
        if page_state not in self.event_listeners: # This is used to check if the page state is already in the event listener dict, if its not then it will create a new list for that page so that it doesn't run into an error and can then be safely be added 
            self.event_listeners[page_state] = []
        
        hashed_event = hash((event_rule, page_state))
        if hashed_event in self.hashed_events:
            print("Already added skip")
            return
        
        self.event_listeners[page_state].append(event_rule) # The event listener input rule is added to the list of the page state event listeners

        for key, _ in event_rule.keys:
            self._tracked_keys.add(key) # The keys are added to the tracked keys so that they can be checked really fast
        return

    
    
    

    def handle_events(self, current_page: PageType, events: list[Event]) -> None:
        #self.events = events # Store the event so they can be accessible throughout the class

        self.previous_keys, self.current_keys = self.current_keys, pygame.key.get_pressed() # This is used to get the current state of the keys and the previous state of the keys so that it can be checked if the key is being held down or not   

        # The previous_mouse is assigned to the current_mouse from the last frame and for current mouse a new data is received through the method "get_pressed"
        self.previous_mouse, self.current_mouse = self.current_mouse, pygame.mouse.get_pressed()
        mouse_pos: tuple[int, int] = pygame.mouse.get_pos()
        time_now: int = pygame.time.get_ticks() # This is used to get the current time in milliseconds so that it can be checked if the key or mouse action is being held down for the required amount of time


        if self.previous_keys is not None and self.current_keys: # This is used to check if the previous keys and current keys are not None so that it can be checked if the key is being held down or not
            for k in self._tracked_keys: # Iterates through the known keys, to manipulate the key press timestamp dict
                
                if self.current_keys[k] and not self.previous_keys[k]: # this is used to check if the key is being pressed down and not being held down
                    self.key_press_timestamp[k] = time_now # It adds the key to key press timestamp dict with the current time so that it can be checked if the key is being held down for the required amount of time
                
                elif not self.current_keys[k]: # This is used to check if the key is not being pressed down so thus it could be removed from the key press timestamp dict,
                    _ = self.key_press_timestamp.pop(k, None)
        

        # Bug Fix: Where the event listeners are duplicated if the current_page is "global"
        all_events: list[EventListenerInputRule] = list(self.event_listeners.get(current_page, []))
        if current_page != "global":
            all_events.extend(self.event_listeners.get("global", []) )
        
        # This is used to iterate through the event listeners for the current page and the global page, and check if the event is triggered by the event rule, if it is then it will call the action function of the event rule
        for event_rule in all_events:

            # Skips the event rule if theres a condition and when the condition function returns false
            if event_rule.condition is not None and not event_rule.condition():
                continue

            # Check for pygame events
            if event_rule.py_event is not None:
                # Check if the event is in the events list and if it is then call the action function of the event rule
                for event in events:
                    # Check if the event type is the same as the event rule's pygame event type
                    if (event.type == event_rule.py_event) and (event_rule.py_event == pygame.TEXTINPUT) and self.text_input_callback:
                        _ = self.text_input_callback(event)
                        event_rule.action()
                    elif event.type == event_rule.py_event:
                        # DEBUG: print(f"Event Triggered: {pygame.event.event_name(event.type)}")

                        event_rule.action() # Call the action function of the event rule
                        break
            
            if event_rule.keys: # Check for key events
                for key, state in event_rule.keys:

                    if self.text_input_active and key in self.BLOCKED_KEY_PRESSES_WHILST_TYPING:
                        continue
                    # Check if the key is in the current keys and if it is then check the state of the key and call the action function of the event rule
                    if state == "pressed" and (self.current_keys and self.current_keys[key]) and (self.previous_keys is None or not self.previous_keys[key]):
                        MusicManager.play_sfx(sfx_key="keypress_click1")
                        print(f"Key Pressed: {pygame.key.name(key)}")
                        event_rule.action()
                        break
                    # Check if the key is being held down and if it is then check the time that the key has been held down for and call the action function of the event rule
                    elif state == "holding" and self.current_keys and self.current_keys[key] and (self.previous_keys is not None and self.previous_keys[key]):
                        if time_now - self.key_press_timestamp.get(key, 0) >= event_rule.hold_time_ms:
                            print(f"Key Held: {pygame.key.name(key)} for {time_now - self.key_press_timestamp.get(key, 0)}")
                            self.key_press_timestamp[key] = time_now # Update the timestamp so that it can be checked if the key is being held down for the required amount of time
                            event_rule.action()
                            break
                    # Check if the key is released and if it is then call the action function of the event rule
                    elif state == "released" and (self.previous_keys is not None and self.previous_keys[key]) and (self.current_keys is None or not self.current_keys[key]):
                        #print(f"Key Released: {pygame.key.name(key)}")
                        MusicManager.play_sfx(sfx_key="keypress_click1")
                        event_rule.action()
                        break
            
            if event_rule.mouse_action is not None:
                # Resolve the hover area, allowing it to be either a fixed rectangle
                # or a function that returns the rectangle's current position.
                # When no hover rect is given, the mouse action can run anywhere on the screen.
                mouse_over: bool = True
                unique_id: int | None = None

                if event_rule.hover_rect is not None:
                    hover_rect: Rect = event_rule.hover_rect if isinstance(event_rule.hover_rect, Rect) else event_rule.hover_rect()
                    mouse_over = hover_rect.collidepoint(mouse_pos)
                    unique_id = id(event_rule.hover_rect)

                    # entered: When the mouse first visits the rect
                    if event_rule.mouse_action == "enter" and mouse_over and unique_id != self.button_tracker:
                        print(f"Entered a new button with id {unique_id}")
                        CursorManager.set_hand_cursor()
                        self.button_tracker = unique_id
                        event_rule.action()

                    # exit: When the mouse is no longer over the rect, and the unique id matches with the button_tracker
                    if event_rule.mouse_action == "exit" and not mouse_over and (self.button_tracker == unique_id):
                        print(f"Moved away from the button with id {unique_id}")
                        CursorManager.set_pointer_cursor()
                        self.button_tracker = None
                        event_rule.action()

                    # clicked: When the button was not pressed last frame but is pressed this frame over the rect
                    if event_rule.mouse_action == "clicked" and mouse_over and self.current_mouse[0] and not self.previous_mouse[0]:
                        MusicManager.play_sfx(sfx_key="mouse_click2")
                        event_rule.action()

                    if event_rule.mouse_action == "unclick" and not mouse_over and self.current_mouse[0] and not self.previous_mouse[0]:
                        #MusicManager.play_sfx(sfx_key="mouse_click2")
                        print("Unclick ")
                        event_rule.action()

                # holding: The left mouse button has stayed down since the previous frame
                if event_rule.mouse_action == "holding" and mouse_over and self.current_mouse[0] and self.previous_mouse[0]:
                    event_rule.action()

                # released: The left mouse button was down last frame and is up this frame
                if event_rule.mouse_action == "released" and mouse_over and self.previous_mouse[0] and not self.current_mouse[0]:
                    event_rule.action()

        return