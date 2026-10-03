from pygame.surface import Surface
from typing import Callable, Literal, TypeAlias
import pygame

from components.Image import BackgroundImageComponent, ImageComponent, TextImageComponent, TextOption
from components.Slider import Slider
from util import EventListenerInputRule
from CustomTypes import PageType
from util.GlobalHolder import GlobalHolder
from util.AssetManager import fonts, images

from components import Button, DropDown, ImageOption

FpsOption: TypeAlias = Literal["30", "60", "90", "120", "Uncapped"]



SubEvents: TypeAlias = Literal["quit_confirmation", "setting_menu"]
class BasePage(GlobalHolder):

    def __init__(self) ->  None:  # This is used to initialise the page, and is called when the page is created. 
        #self.background_image_key: str = "background_image1"
        self.current_page: PageType = "global"  # This is used to hold the current page that is being displayed on the screen, this is used to check if the page is being displayed or not

        self.next_page: PageType |  None = None
        self.sub_events: dict[SubEvents, bool] = {
            "quit_confirmation": False,
            "setting_menu": False
        }

        self.screen_manager.set_caption(caption="Base Page")

        # A previous setting dict to store the settings before the change
        self.previous_setting: dict[str, float | int | str] = {"music_vol": 0.7, "sfx_vol": 0.7, "fps": "60", "font": "poppins"}
        # A current setting dict to store the current setting 
        self.current_setting: dict[str, float | int | str] = self.previous_setting.copy()
        # A flag to show whether the settings has changed or not
        self.setting_changed: bool= False

        self.load_saved_settings()

        self.init()  # This is used to initialise the page components (e.g buttons, labels, textboxes, etc.), and is called when the page is created.
        self.update_layout()
        self.add_events()  # This is used to add the events to the event manager, and is called when the page is created.

        pass



    def init_background(self, image_key: str) -> None:
        #self.background_image_key = image_key
        # old code: self.background_image = BackgroundImageComponent(image_option=image_key, base_pos=(0,0))
        self.background_image = BackgroundImageComponent(image_option=image_key, base_pos=self.screen_manager.center_points, anchor="center")
        self.background_image.update_layout()
    
    def settings_change(self, key: str, value: float | str) -> None:
        # Mark the settings as changed when user modifies the setting
        if not self.setting_changed:
            self.setting_changed = True

            # Display the controls for saving or discarding the changes.
            self.change_save_setting_button_ui()

        # Keep the latest value so it can be saved or reverted later.
        self.current_setting[key] = value
        pass

    def change_volume(self, value: float) -> None:
        # The settings_change method is called to update the current setting and mark that a change has occurred.
        self.settings_change(key="music_vol", value=value)
        # The music is set in the music_manager to the new volume level
        self.music_manager.set_music_volume(volume=value)
    
    def change_sfx(self, value: float) -> None:
        # The settings_change method is called to update the current setting and mark that a change has occurred.
        self.settings_change(key="sfx_vol", value=value)
        # The sfx is set in the music_manager to the new volume level
        self.music_manager.set_sfx_volume(volume=value)
    
    def change_fps(self, value: str) -> None:
        # Checks if the setting is being changed and the current setting is updated
        self.settings_change(key="fps", value=value)
        # The fps is normalised into numbers or None if uncapped
        fps: int | None = None if value == "Uncapped" else int(value)
        # The fps is updated in the GlobalHolder class
        GlobalHolder.FPS = fps
    
    def change_font(self, value: str) -> None:
        # The font is changed in the current setting and the settings are marked as changed
        self.settings_change(key="font", value=value)
        # The font is changed in the font manager and the layout is updated to reflect the new font
        self.font_manager.set_font(font_key=value)
        # The layout of the components is updated to reflect the new font
        self.update_layout()

    def change_save_setting_button_ui(self) -> None:
        # Make the text color of the save button white if there are unsaved changes, otherwise make it gray to indicate that there are no unsaved changes.
        if self.setting_changed: self.save_setting_changes_button.text_surface.text_option.set_color(color=(255, 255,255))
        else: self.save_setting_changes_button.text_surface.text_option.set_color(color=(166,166,166))

        self.save_setting_changes_button.update_layout()
    
    def save_setting_changes(self) -> None:
        # Mark the current settings as saved.
        self.setting_changed = False
        # Refresh the save button to show that there are no unsaved changes.
        self.change_save_setting_button_ui()


    def init(self) -> None:  # This is used to initialise the page components (e.g buttons, labels, text boxes, etc.), and is called when the page is created.
        # self.background_image: Surface = self.load(image_key=self.background_image_key)
                # The game's background is initialise  with the image_key of "background_image1" placed at top-left corner of the screen starting from the point 0,0
        self.background_image: BackgroundImageComponent = BackgroundImageComponent(image_option="background_image1", base_pos=self.screen_manager.center_points, anchor="center")

        # This codes is for the background covering the screen, it acts as a transparent layer so the overlay is more focused on
        empty_surface: Surface = Surface(size=self.screen_manager.current_size, flags=pygame.SRCALPHA)
        _ = empty_surface.fill(color=(0, 0, 0, 128))

        self.quit_game_overlay_background: BackgroundImageComponent = BackgroundImageComponent(image_option=empty_surface, base_pos=(0, 0))
        # This is the overlay panel, used to display the text and buttons
        self.quit_game_overlay: ImageComponent = ImageComponent(image_option="confirmation_overlay", base_pos=(480, 243), anchor="center")

        # Overlay text
        self.overlay_quit_game_text: TextImageComponent = TextImageComponent(text_option=TextOption(text="Are you sure you wish to close the game?", size=24, max_width=int(self.quit_game_overlay.rect.width * 0.9), align="center"), base_pos=(self.quit_game_overlay.rect.centerx, int(self.quit_game_overlay.rect.centery * 0.7)), anchor="center")

        # Overlay Buttons
        # Creates a Button for confirm quit Game
        self.confirm_quit_game_button: Button = Button(image_option=ImageOption(image=self.load_image(image_key="button1")), text_option=TextOption(text="Confirm", size=16), key=pygame.K_o, position=(348, 326), anchor="center")
        # When the button is activated the quit game button is fired
        self.confirm_quit_game_button.on_activate = self.quit_game

        # Creates a Button for Cancel quit Game
        self.cancel_quit_game_button: Button = Button(image_option=ImageOption(image=self.load_image(image_key="button1")), text_option=TextOption(text="Cancel", size=16), key=pygame.K_x, position=(612, 326), anchor="center")
        # This will disable the sub event to draw it on the screen
        def cancel_quit_game() -> None: self.sub_events["quit_confirmation"] = False
        # When the button is activated the cancel_quit_game is executed, preventing the game from closing and resuming where left off
        self.cancel_quit_game_button.on_activate = cancel_quit_game


        # This part is used to render the setting!
        # Initialise the setting menu button
        self.setting_menu_button: Button = Button(image_option=ImageOption(image=self.load_image(image_key="setting1")), text_option=TextOption(text="", size=0), key=pygame.K_s, position=(934, 26), anchor="center")
        # Create a background for the setting with a bit of transparency
        bg: Surface = self.load_image(image_key="setting_bg")
        bg.set_alpha(247)
        self.setting_menu_bg: BackgroundImageComponent = BackgroundImageComponent(image_option=bg, base_pos=self.screen_manager.center_points, anchor="center")
        # Now draw a text label at the top center of the screen
        self.setting_text_surface: TextImageComponent = TextImageComponent(
            text_option=TextOption(text="Setting Menu", size=36, color=(244, 239, 235), bold=True, underline=True), 
            base_pos=(480, 48), anchor="center"
            )

        # Setting Components
        self.volume_button: Button = Button(image_option=ImageOption(colored_image=( (82 , 100, 121) , (235, 50 ) ), round_edges=15), text_option=TextOption(text="Audio", size=25, color=(244, 239, 235)), position=(70, 90))
        # Initialise the slider for the volume
        self.volume_slider: Slider = Slider(track_option=ImageOption(colored_image=( (180, 180, 180) , (410, 18 ) ), round_edges= 9), knob_option=ImageOption(colored_image=( (0,0,0), (35, 35) ), shape="circle" ),position=(690, 115), anchor="center", value=float(self.current_setting["music_vol"]), key_increase=pygame.K_RIGHT, key_decrease=pygame.K_LEFT)

        # Initialise the sfx button
        self.sfx_button: Button = Button(image_option=ImageOption(colored_image=( (82 , 100, 121) , (235, 50 ) ), round_edges=15), text_option=TextOption(text="Sfx", size=25, color=(244, 239, 235)), position=(70, 150))

        # Then initlaise the slider 
        self.sfx_slider: Slider = Slider(track_option=ImageOption(colored_image=( (180, 180, 180) , (410, 18 ) ), round_edges= 9), knob_option=ImageOption(colored_image=( (0,0,0), (35, 35) ), shape="circle" ),position=(690, 175), anchor="center", value=float(self.current_setting["sfx_vol"]), key_increase=pygame.K_UP, key_decrease=pygame.K_DOWN)
        
        # Now start with the drop down fps changer button
        self.fps_button: Button =  Button(image_option=ImageOption(image=self.load_image(image_key="button2")), text_option=TextOption(text="Change FPS   ", size=23, color=(244, 239, 235)), position=(70, 240))

        # The drop down menu is created with the the items 
        self.fps_dropdown: DropDown = DropDown(items= ["30", "60", "90", "120", "Uncapped"], default_item=str(self.current_setting.get("fps")), dropdown_surface=ImageComponent(image_option=self.load_image(image_key="dropdown_icon"), base_pos=(self.fps_button.surface.rect.x + int(self.fps_button.surface.rect.w * 0.89), 265), anchor="center"), item_sizes=(100, 20), menu_position=(self.fps_button.surface.rect.x + self.fps_button.surface.rect.width, self.fps_button.surface.rect.y + self.fps_button.surface.rect.height), menu_anchor="topright")
        
        # The font button is created
        self.font_button: Button = Button(image_option=ImageOption(image=self.load_image(image_key="button2")), text_option=TextOption(text="Change Font   ", size=23, color=(244, 239, 235)), position=(400, 240))
        
        # The drop down for the font is also created 
        self.font_dropdown: DropDown = DropDown(items=[font for font in fonts.keys()], dropdown_surface=ImageComponent(image_option=self.load_image(image_key="dropdown_icon"), base_pos=(self.font_button.surface.rect.x + int(self.font_button.surface.rect.w * 0.89), 265), anchor="center"), item_sizes=(150, 20), menu_position=(self.font_button.surface.rect.x + self.font_button.surface.rect.width, self.font_button.surface.rect.y + self.font_button.surface.rect.height), menu_anchor="topright", default_item=str(self.current_setting["font"]))

        # The save setting changes button is created, which will be used to save the changes made in the setting menu
        self.save_setting_changes_button: Button = Button(image_option=ImageOption(colored_image=( (82 , 100, 121) , (235, 50 ) ), round_edges=15), text_option=TextOption(text="Save Changes", color=(166, 166, 166), size=23), position=(940, 461), anchor="topright")
        self.default_settings: Button = Button(image_option=ImageOption(colored_image=( (82 , 100, 121) , (235, 50 ) ), round_edges=15), text_option=TextOption(text="Default Settings", color=(166, 166, 166), size=23), position=(20, 461))
        self.default_settings.on_activate = lambda: self.apply_default_settings()
        pass

    def draw_setting_menu(self) -> None:
        if self.sub_events.get("setting_menu", False):
            self.setting_menu_bg.draw()
            self.setting_text_surface.draw()
            # Draw the volume button on the display
            self.volume_button.draw()
            self.volume_slider.draw()
            # Draw the sfx button on the display
            self.sfx_button.draw()
            self.sfx_slider.draw()

            # Draw the fps changing components
            self.fps_button.draw()
            self.fps_dropdown.draw()
            # Draw the font changing components
            self.font_button.draw()
            self.font_dropdown.draw()
            # Draw the save setting changes button
            self.save_setting_changes_button.draw()
            #self.default_settings.draw()
        self.setting_menu_button.draw()
        return


    def draw_quit_confirm(self) -> None:
        # Draw the darkened background overlay to dim the page behind the quit confirmation.
        self.quit_game_overlay_background.draw()

        #_ = self.screen_manager.blit(source=self.quit_game_overlay, dest=self.quit_game_overlay.get_rect(center=self.quit_game_overlay_center_position))
        self.quit_game_overlay.draw()

        # Draw the text on the overlay
        self.overlay_quit_game_text.draw()
        # Used to draw the Confirm Button
        self.confirm_quit_game_button.draw()
        # used to draw the cancel button
        self.cancel_quit_game_button.draw()

    def draw(self)-> None:
        return


    def draw_main(self) -> None:  # This is used to draw the page components (e.g buttons, labels, textboxes, etc.), and is called every frame.
        _ = self.screen_manager.fill(color=(0, 0, 0))
        # Old Code: _ = self.screen_manager.blit(source=self.background_image, dest=self.background_image.get_rect(center=self.screen_manager.center_points))
        self.background_image.draw()

        
        self.draw()

        self.draw_setting_menu()

        # Handle the sub events in a order, where the least priority one is drawn first and the most important priority one is handled last
        if self.sub_events["quit_confirmation"]:
            self.draw_quit_confirm()
        return



    def update_layout(self) -> None:  # This is used to update the size of the components when the window is resized, this is called when the window is resized
        # Undocumented
        self.determine_scale()
        # self.background_image = self.resize_background(image=self.load_image(image_key=self.background_image_key))
        self.background_image.update_layout()

        # Old : self.quit_game_overlay_background = self.resize_image(image=self.quit_game_overlay_background_raw)
        self.quit_game_overlay_background.update_layout()
        # Old self.quit_game_overlay = self.resize_image(image=self.load_image(image_key=self.quit_game_overlay_key))
        # Old self.quit_game_overlay_center_position = self.resize_position(position=self.quit_game_overlay_center_position_raw)
        
        # Update the Quit Confirm Components
        self.overlay_quit_game_text.update_layout()
        self.quit_game_overlay.update_layout()
        self.confirm_quit_game_button.update_layout()
        self.cancel_quit_game_button.update_layout()

        #self.setting_option = self.resize_image(image=self.setting_option_raw)
        #self.setting_option_position = self.resize_position(position=self.setting_option_position_raw)
        # Update the setting's components
        self.setting_menu_bg.update_layout()
        self.setting_menu_button.update_layout()
        # Update the layout of the text surface when the window is resized 
        self.setting_text_surface.update_layout()
        # Update the layout of the volume button when the window is resized 
        self.volume_button.update_layout()
        # Update the UI of the volume slider
        self.volume_slider.update_layout()
        # Update the UI of the sfx button and slider
        self.sfx_button.update_layout()
        self.sfx_slider.update_layout()
        # Update the UI components of the fps changing.
        self.fps_button.update_layout()
        # Update the layout of the components in the fps drop down (& menu)
        self.fps_dropdown.update_layout()

        # Update the layout of the font button
        self.font_button.update_layout()#
        # Update the layout of the components in the font drop down (& menu)
        self.font_dropdown.update_layout()
        # Update the layout of the setting save button
        self.save_setting_changes_button.update_layout()
        self.default_settings.update_layout()
        pass



    def update(self) -> None:  # This is used to update the page components (e.g buttons, labels, textboxes, etc.), and is called every frame.
        pass

    def mute(self) -> None:
        # Set the volume of the music and sfx to zero first
        self.music_manager.set_music_volume(volume=0)
        self.music_manager.set_sfx_volume(volume=0)

        # Then update the components by setting the value to 0 so the knob moves all the way back
        self.sfx_slider.set_value(value=0)
        self.volume_slider.set_value(value=0)

        # then update the ui
        self.sfx_slider.update_layout()
        self.volume_slider.update_layout()



    def add_events(self) -> None:
        def take_screenshot() -> None:
            display: Surface = self.screen_manager.copy()
            pygame.image.save(surface=display, file="screenshot.png")
        self.event_manager.add_event_listener(page_state="global", event_rule=EventListenerInputRule(action=take_screenshot, keys=[(pygame.K_LCTRL, "holding"), (pygame.K_LSHIFT, "holding"), (pygame.K_s, "pressed")]))

        # This both is used to execute the resize_display method when the window is resized
        self.event_manager.add_event_listener(page_state="global", event_rule=EventListenerInputRule(action=self.resize_display, py_event=pygame.VIDEORESIZE))
        # I will document this part as well.
        #self.event_manager.add_event_listener(page_state="global",event_rule=EventListenerInputRule(action=self.resize_display, keys=[(pygame.K_ESCAPE, "pressed")]))

        # This will be used to directly shut down the game
        self.event_manager.add_event_listener(page_state="global", event_rule=EventListenerInputRule(action=self.quit_game, keys=[(pygame.K_ESCAPE, "holding")], hold_time_ms=2000  ))

        # Used to handle confirm shut down of the game
        def confirm_quit_game()-> None: self.sub_events["quit_confirmation"] = True
        self.event_manager.add_event_listener(page_state="global", event_rule=EventListenerInputRule(action=confirm_quit_game, py_event=pygame.QUIT))
        self.event_manager.add_event_listener(page_state="global",event_rule=EventListenerInputRule(action=confirm_quit_game, keys=[(pygame.K_ESCAPE, "pressed")]))

        self.confirm_quit_game_button.add_event_listeners(page_state="global", condition=lambda: self.sub_events.get("quit_confirmation", False))
        self.cancel_quit_game_button.add_event_listeners(page_state="global", condition=lambda: self.sub_events.get("quit_confirmation", False))

        # Add event listeners for the settings
        def toggle_setting_menu() -> None:
            if self.sub_events.get("setting_menu", False):
                if self.setting_changed:
                    # Revert the settings to the previous values if the user cancels the changes
                    self.volume_slider.set_value(value=float(self.previous_setting["music_vol"]))
                    self.sfx_slider.set_value(value=float(self.previous_setting["sfx_vol"]))
                    self.fps_dropdown.select_item(index=self.fps_dropdown._labels.index(str(self.previous_setting["fps"])))
                    self.font_dropdown.select_item(index=self.font_dropdown._labels.index(str(self.previous_setting["font"])))

                    self.setting_changed = False

                    self.change_save_setting_button_ui()
                    self.update_layout()
                self.sub_events["setting_menu"] = False
            else:
                # When the setting menu is opened, the current settings are stored in the previous_setting dictionary to allow for reverting changes if needed.
                self.previous_setting["music_vol"] = self.volume_slider.value
                self.previous_setting["sfx_vol"] = self.sfx_slider.value
                self.previous_setting["font"] = self.font_manager._font_key or "Poppins"
                self.previous_setting["fps"] = self.fps_dropdown.selected_item or "60"
                print(f"When settings opened {self.previous_setting}")
                self.sub_events["setting_menu"] = True


        self.setting_menu_button.on_activate = toggle_setting_menu
        self.setting_menu_button.add_event_listeners(page_state="global")

        # Change the volume as the slider moves
        #self.volume_slider.on_change = self.music_manager.set_music_volume(volume=self.volume_slider.value)
        self.volume_slider.on_change = lambda: self.change_volume(value=self.volume_slider.value)
        # Add all the events for the volume slider
        self.volume_slider.add_event_listeners(page_state="global", condition=lambda: self.sub_events.get("setting_menu", False) )

        # When the value of the slider changes the sfx volume is adjusted instantly
        self.sfx_slider.on_change = lambda: self.change_sfx(value=self.sfx_slider.value)
        self.sfx_slider.add_event_listeners(page_state="global", condition=lambda: self.sub_events.get("setting_menu", False) )

        
        
        self.event_manager.add_event_listener(page_state="global", event_rule=EventListenerInputRule(action=self.mute, keys=[(pygame.K_m, "released")]))

        # Add the on change callback for the fps drop down
        self.fps_dropdown.on_change = lambda: self.change_fps(value=self.fps_dropdown.selected_item) # pyright: ignore
        # Add all the events from the drop down to the event listener manager
        self.fps_dropdown.add_event_listeners(page_state="global", condition=lambda: self.sub_events.get("setting_menu", False) )
        # The callback function for the font drop down is added, so when the player changes the font the font of the UI is changed
        self.font_dropdown.on_change = lambda: self.change_font(value=self.font_dropdown.selected_item) # pyright: ignore
        # All the events listeners for the font dropdown is added to the event listener manager
        self.font_dropdown.add_event_listeners(page_state="global", condition=lambda: self.sub_events.get("setting_menu", False) )

        self.save_setting_changes_button.on_activate = lambda: self.save_setting_changes()
        self.save_setting_changes_button.add_event_listeners(page_state="global", condition=lambda: self.sub_events.get("setting_menu", False) and self.setting_changed)
        self.default_settings.add_event_listeners(page_state="global", condition=lambda: self.sub_events.get("setting_menu", False))
        return

    def handle_event(self) -> None:  # This is used to handle events (e.g button clicks, text input, etc.), and is called every frame.
        events: list[pygame.event.Event] = pygame.event.get()  # This is used to get the events that are currently in the event queue, this is called every frame
        self.event_manager.handle_events(current_page=self.current_page, events=events)  # This is used to handle the events that are currently in the event queue, this is called every frame
        pass

    def run(self) -> None:  # This is used to run the page, and is called every frame. This is called by the GameManager Class to run the page.
        # self.update_layout()
        self.handle_event()
        self.update()
        self.music_manager.update()
        # Undocumented
        self.draw_main()

        # FIX: Now pygame renders the objects 
        pygame.display.flip()
        return

    # Other methods to handle the pages throughout
    def change_page(self, new_state: PageType)-> None: self.current_page = new_state
    
    def resize_display(self) -> None:
        resize_size: tuple[int, int] = self.screen_manager.get_size() # Get the current size of the display after resized

        # Checks if the resize_size is same as the current_size then it tries to full screen
        if resize_size == self.screen_manager.current_size:
            resize_size = (0, 0)
    
        # Changes the screen size to the new resized_size
        self.screen_manager.display_surface = pygame.display.set_mode(
            size=resize_size, flags=pygame.RESIZABLE
        )
        # FIX 5: Query real window size after set_mode instead of storing (0, 0)
        self.screen_manager.current_size = self.screen_manager.get_size()
        # Stores a new attribute called center_points which is used to align objects at the centre of the screen.
        self.screen_manager.center_points = self.screen_manager.get_rect().center
        # Updates the layout of the whole page, so it matches with the current size of the display.
        self.update_layout()

    def apply_default_settings(self) -> None:
        #self.change_sfx(value=0.7)
        #self.change_fps(value="60")
        #self.change_font(value="Poppins")
        # 
        self.volume_slider.set_value(value=0.7)
        self.sfx_slider.set_value(value=0.7)
        self.font_dropdown.select_item(index=self.font_dropdown._labels.index("Poppins"))
        self.fps_dropdown.select_item(index=self.fps_dropdown._labels.index("60"))

    def load_saved_settings(self) -> None:
        # Fetch settings from your DB. (Assumes this returns a dictionary or similar key-value mapping)
        saved_data = self.db.get_settings() 
        if not saved_data: saved_data = {}
        
        # # Update the current_setting dictionaries
        self.current_setting["music_vol"] = saved_data.get("music_vol", 0.7)
        self.current_setting["sfx_vol"] = saved_data.get("sfx_vol", 0.7)
        self.current_setting["fps"] = saved_data.get("fps", "60")
        self.current_setting["font"] = saved_data.get("font", "Poppins")
        self.previous_setting = self.current_setting.copy()

        # Make changes to the specifed classes itself that handles the corresponding settings
        self.music_manager.set_music_volume(volume=float(self.current_setting["music_vol"]))
        self.music_manager.set_sfx_volume(volume=float(self.current_setting["sfx_vol"]))
        
        fps_val = str(self.current_setting["fps"])
        GlobalHolder.FPS = None if fps_val == "Uncapped" else int(fps_val)
        
        self.font_manager.set_font(font_key=str(self.current_setting["font"]))
        #self.change_save_setting_ui()

    def quit_game(self) -> None:
        # Save the confirmed settings to the local database before shutting down
        self.db.save_settings(
            music_vol=float(self.current_setting["music_vol"]),
            sfx_vol=float(self.current_setting["sfx_vol"]),
            fps=str(self.current_setting["fps"]),
            font=str(self.current_setting["font"])
        )
        
        # After save set the running flag to False to exit the main loop and close the game
        GlobalHolder.running = False