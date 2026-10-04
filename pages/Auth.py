import random
from util.GlobalHolder import GlobalHolder
from util.DataBase.Database import Response

from typing import override, final, TypeAlias, Literal
from pygame import Surface
from components.Button import Button, ImageOption
from components.Image import BackgroundImageComponent, ImageComponent, TextImageComponent, TextOption
from components.TextInput import TextInput
from util.Game.Player import DeckData, Player, UserInfo
from .BasePage import BasePage
import pygame 
from util.Game.Card import ACTION_DB

AuthSubEvents: TypeAlias = Literal["main", "sign_in", "sign_up", "security_overlay"]

class Auth(BasePage):
    @final
    def __init__(self) -> None:
        super().__init__()
        # Change the current_page to 'authenticate' 
        self.change_page(new_state="authenticate")
        # Add the subvent so that the page can be categorized into different sections
        self.auth_sub_events: dict[AuthSubEvents, bool] = {"main": True, "sign_in": False, "sign_up": False, "security_overlay": False}
        # Keep the generated security code for the registration flow.
        self.security_code_value: int = 0
        #self.init()

    @override
    def init(self) -> None:
        super().init()

        # Change the background of the game
        self.init_background(image_key="background_image2") 
        # Add the text_surface so it can guide them
        self.text_surface: TextImageComponent = TextImageComponent(text_option=TextOption(text="Welcome to Elementa Clash", size=36, bold=True, align="center", max_width=int(self.screen_manager.current_size[0] * 0.8)), base_pos=(480, 108), anchor="center") # pyright: ignore[reportUninitializedInstanceVariable]
        # Sign In button redirects to the sign in part.
        self.sign_in_button: Button = Button(image_option=ImageOption(image=self.load_image(image_key="button1")), text_option=TextOption(text="Sign In", size=16), position=(480 , 270), anchor="center") # pyright: ignore[reportUninitializedInstanceVariable]
        # Sign Up Button redirects to the sign up part.
        self.sign_up_button: Button = Button(image_option=ImageOption(image=self.load_image(image_key="button1")), text_option=TextOption(text="Sign Up", size=16), position=(480 , 324), anchor="center") # pyright: ignore[reportUninitializedInstanceVariable]

        self.overlay_background: ImageComponent = ImageComponent(image_option="confirmation_overlay", base_pos=(480, 324), anchor="center") # pyright: ignore[reportUninitializedInstanceVariable]

        # Security Overlay Components
        self.security_code_overlay: ImageComponent = ImageComponent(image_option="overlay2", base_pos=self.screen_manager.center_points, anchor="center") # pyright: ignore[reportUninitializedInstanceVariable]
        
        self.security_title_text: TextImageComponent = TextImageComponent(text_option=TextOption(text="Security Code!!", size=24, bold=True), base_pos=(480, 200), anchor="center") # pyright: ignore[reportUninitializedInstanceVariable]
        self.security_code_text: TextImageComponent = TextImageComponent(text_option=TextOption(text="", size=18, bold=True), base_pos=(480, 260), anchor="center") # pyright: ignore[reportUninitializedInstanceVariable]
        
        self.new_code_button: Button = Button(image_option=ImageOption(image=self.load_image(image_key="button3")), text_option=TextOption(text="New Code", size=13), position=(360, 380), anchor="center") # pyright: ignore[reportUninitializedInstanceVariable]
        self.confirm_security_code: Button = Button(image_option=ImageOption(image=self.load_image(image_key="button3")), text_option=TextOption(text="Register", size=13), position=(600, 380), anchor="center") # pyright: ignore[reportUninitializedInstanceVariable]
        
        def constrains(text: str, allowed: str="abcdefghijklmnopqrstuvwxyz0123456789_.") -> bool:
            # Check if the text contains only the allowed characters
            for character in text:
                # Check if the character is not in the allowed characters
                if character not in allowed: return False
            # Return True if the text contains only the allowed characters
            return True
        
        def length_check(text: str, min: int= 5, max: int= 10) -> bool:
            # Check if the text length is between the minimum and maximum length
            text_length: int = len(text)
            if text_length < min or text_length > max:
                # Return False if the text length is not between the minimum and maximum length
                return False
            # Return True if the text length is between the minimum and maximum length
            return True
        
        # The username input is initialised with the placeholder of Username and position at the centered axis with the maximum character of 10
        self.username_input: TextInput = TextInput(image_option=ImageOption(image=self.load_image(image_key="text_input1")), text_option=TextOption(text="", size=16, color=(128, 103, 89)), placeholder="Username", position=(480, 274), anchor="center", max_length=10) # pyright: ignore[reportUninitializedInstanceVariable]
        # Set the validations for the username input
        self.username_input.validations = [( lambda text: constrains(text) , "The username can only contain a-z, 0-9 and . _"), (length_check, "The username must be between 5-10 characters")]
        
        self.password_input: TextInput = TextInput(image_option=ImageOption(image=self.load_image(image_key="text_input1")), text_option=TextOption(text="", size=16, color=(128, 103, 89)), placeholder="Password", position=(480, 354), anchor="center", password=True) # pyright: ignore[reportUninitializedInstanceVariable]
        # Set the validations for the password input
        self.password_input.validations = [(lambda text: length_check(text=text, min=8, max=15), "The password should be between 8-15 chars long"), (lambda text: text != self.username_input.text, "Password cannot be the same as the username")]

        # Create the confirm password input
        self.confirm_password_input: TextInput = TextInput(image_option=ImageOption(image=self.load_image(image_key="text_input1")), text_option=TextOption(text="", size=14, color=(128, 103, 89)), placeholder="Confirm Password", position=(480, 434), anchor="center", password=True) # pyright: ignore[reportUninitializedInstanceVariable]
        # Set the validations for the confirm password input
        self.confirm_password_input.validations = [(lambda text: length_check(text=text, min=8, max=15), "The password should be between 8-15 chars long"), (lambda text: text != self.username_input.text, "Password cannot be the same as the username"), (lambda text: text == self.password_input.text, "Passwords do not match!")]

        # Create a smaller button surface for the submit buttons
        smaller_btn_surface: Surface = self.resize_image(image=self.load_image(image_key="button1"), size=(120, 30))
        # Create the submit sign in button
        self.submit_sign_in: Button = Button(image_option=ImageOption(image=smaller_btn_surface), text_option=TextOption(text="Sign In", size=12), position=(480, 420), anchor="center") # pyright: ignore[reportUninitializedInstanceVariable]
        # Create the submit sign up button
        self.submit_sign_up: Button = Button(image_option=ImageOption(image=smaller_btn_surface), text_option=TextOption(text="Sign Up", size=12), position=(480, 490), anchor="center") # pyright: ignore[reportUninitializedInstanceVariable]
        # Load the eye open and closed images
        self.eye_open_image: Surface = self.load_image(image_key="eye_open")
        self.eye_closed_image: Surface = self.load_image(image_key="eye_closed")
        # Initialize the toggle password button with the eye open image
        self.toggle_password: Button = Button(image_option=ImageOption(image=self.eye_open_image), text_option=TextOption(text="", size=0), key=pygame.K_v, position=(int(self.password_input.surface.rect.centerx + self.password_input.surface.rect.width * 0.6), self.password_input.surface.rect.centery), anchor="center") # pyright: ignore[reportUninitializedInstanceVariable]
        # Initialize the go back button with the go back image
        self.go_back_button: Button = Button(image_option=ImageOption(image=self.load_image(image_key="go_back")), text_option=TextOption(text="", size=0), key=pygame.K_b, position=(690, 430) ) # pyright: ignore[reportUninitializedInstanceVariable]
        return

    @final
    @override
    def update(self) -> None:
        super().update()
        # Check if the response queue is empty
        if self.db.response_queue.empty():
            return

        res: Response = self.db.response_queue.get_nowait() # Get the response from the response queue
        if res.action == "sign_in": # Check if the action is sign in
            if res.success: # Check if the sign in is successful
                print("Sign in")
                user_data = res.user_data["user_data"]
                user_info = res.user_data["user_info"]
                deck_data = res.user_data["deck_data"]
                GlobalHolder.player = Player(uid=user_data["id"], username=user_data["username"], user_info=user_info, user_decks=deck_data)
                self.next_page = "main_menu"
                self.change_page(new_state="main_menu") 
            else: # Print the error message if the sign in is not successful
                self.username_input.errors.append(res.message) # Add the error message to the username input
                self.username_input.validate_text(text=self.username_input.text) # Validate the username input
        elif res.action == "sign_up": # Check if the action is sign up
            if res.success: # Check if the sign up is successful
                print("Created")

                # From Deck Phase
                user_id: str = res.user_data["id"]
                deck1 = DeckData(user_id=user_id, uid=self.db.generate_uid(), name="Mixed Race", characters=["jean", "amber", "kaeya"], action_cards=[action_card_id for action_card_id in list(ACTION_DB.keys())[:10]])
                deck2 = DeckData(user_id=user_id, uid=self.db.generate_uid(), name="Deck 2", characters=[], action_cards=[])
                deck3 = DeckData(user_id=user_id, uid=self.db.generate_uid(), name="Deck 3", characters=[], action_cards=[])
                deck4 = DeckData(user_id=user_id, uid=self.db.generate_uid(), name="Deck 4", characters=[], action_cards=[])
                deck_data = [deck1, deck2, deck3, deck4]

                user_info = UserInfo(uid=user_id, xp=0, battle_wins=0, total_battles=0, active_deck_uid=deck1["uid"], deck_list_uid=[deck1["uid"], deck2["uid"], deck3["uid"], deck4["uid"]])

                self.db.create_new_user_info(user_info=user_info)
                self.db.create_new_deck(user_id=user_id, deck_data=deck_data)


                self.set_sign_in(clear=True)
                self.text_surface.text_option.set_text(text="Your Account has been created! Please Sign In")
                self.text_surface.update_layout()
            else:
                self.username_input.errors.append(res.message)
                self.username_input.validate_text(text=self.username_input.text)
        elif res.action == "check_username":
            if not res.success: 
                self.show_security_overlay()
            else:
                self.username_input.errors.append(res.message)
                self.username_input.validate_text(text=self.username_input.text)


    def set_main(self) -> None:
        # Set the main section as true and disable all other auth sections.
        self.auth_sub_events["main"] = True
        self.auth_sub_events["sign_in"] = False # Set the sign in section as false
        self.auth_sub_events["sign_up"] = False # Set the sign up section as false
        self.auth_sub_events["security_overlay"] = False  # Set the security overlay section as false

        self.text_surface.text_option.set_text(text="Welcome to Elementa Clash") # Set the text of the text surface to "Welcome to Elementa Clash"
        self.update_layout() # Update the layout of the page

    def set_sign_in(self, clear: bool=False) -> None: 
        # Set the sign_in section as true and disable all other auth sections.
        self.auth_sub_events["main"] = False
        self.auth_sub_events["sign_in"] = True


        self.auth_sub_events["sign_up"] = False
        self.auth_sub_events["security_overlay"] = False

        # Update the page title for the sign-in screen.
        self.text_surface.text_option.set_text(text="Welcome Back Player")

        # Reset the input positions to the standard sign-in layout.
        self.username_input.change_base_position(position=(480, 274)) # Change the base position of the username input to the standard sign-in layout
        self.password_input.change_base_position(position=(480, 354)) # Change the base position of the password input to the standard sign-in layout
        self.toggle_password.change_base_position(position=(int(self.password_input.surface.rect.centerx + self.password_input.surface.rect.width * 0.6), 354)) # Change the base position of the toggle password button to the standard sign-in layout

        # Clear any previously entered sign-in values when requested.
        if clear:
            self.username_input.clear_text() # Clear the text from the username input
            self.password_input.clear_text() # Clear the text from the password input
            
        # Refresh the UI to apply the updated auth state and layout.
        self.update_layout() # Update the layout of the page
    
    def set_sign_up(self, clear: bool=False) -> None: 
        # Activate the sign-up section and hide the other authentication sections.
        self.auth_sub_events["main"] = False
        self.auth_sub_events["sign_in"] = False
        self.auth_sub_events["sign_up"] = True
        self.auth_sub_events["security_overlay"] = False

        # Update the heading so that i can guide the users
        self.text_surface.text_option.set_text(text="Register to Elementa Clash")

        # Shift positions up to accommodate the confirm password field
        self.username_input.change_base_position(position=(480, 234))
        self.password_input.change_base_position(position=(480, 314))
        self.confirm_password_input.change_base_position(position=(480, 394))
        self.toggle_password.change_base_position(position=(int(self.password_input.surface.rect.centerx + self.password_input.surface.rect.width * 0.6), 314))

        if clear:
            # Clear the text from the input fields
            self.username_input.clear_text()
            self.password_input.clear_text()
            self.confirm_password_input.clear_text()
        self.update_layout() # Update the layout of the page

    def generate_security_code(self) -> None:
        self.security_code_value = random.randint(100000, 999999)
        self.security_code_text.text_option.set_text(text=f"Remember the security code \"{self.security_code_value}\"")
        self.security_code_text.update_layout()

    def show_security_overlay(self) -> None:
        self.auth_sub_events["security_overlay"] = True
        self.generate_security_code()
        
    def confirm_registration(self) -> None:
        username: str = self.username_input.text
        password: str = self.password_input.text
        self.db.sign_up(username, password, self.security_code_value)

    def submit_sign_in_form(self) -> None:
        # Get the username and password from the input fields
        username: str = self.username_input.text
        password: str = self.password_input.text

        if username and password: # Check if the username and password are not empty
            print("Validating the sign in info")
            # Validate the sign in info
            self.db.sign_in(username, password)
        else: # Print the error message if the username or password is empty
            print("Please enter both")
        return

    def submit_sign_up_form(self) -> None:
        username: str = self.username_input.text
        password: str = self.password_input.text
        confirm_password: str = self.confirm_password_input.text

        if username and password and confirm_password:
            print("Validating the sign up info")
            self.db.username_exists(username)
        else:
            print("Please fill out all fields")
        return

    @override
    def add_events(self) -> None:
        super().add_events()

        # Input fields (Blocked if overlay is active)
        active_form_condition = lambda: (self.auth_sub_events["sign_in"] or self.auth_sub_events["sign_up"]) and not self.auth_sub_events["security_overlay"]
        # Add all the event listeners for the input fields
        self.username_input.add_event_listeners(page_state=self.current_page, condition=active_form_condition)
        # Add all the event listeners for the password input field
        self.password_input.add_event_listeners(page_state=self.current_page, condition=active_form_condition)
        # Add all the event listeners for the confirm password input field
        self.confirm_password_input.add_event_listeners(page_state=self.current_page, condition=lambda: self.auth_sub_events["sign_up"] and not self.auth_sub_events["security_overlay"])
        
        # Add the on_activate callback so that when its clicked the toggle_view_password callback is run
        def toggle_view_password() -> None:
            # Toggle the password visibility
            self.password_input.type_password = not self.password_input.type_password
            self.confirm_password_input.type_password = not self.confirm_password_input.type_password
            # Change the image of the toggle password button
            self.toggle_password.change_image(image=self.eye_open_image if self.password_input.type_password else self.eye_closed_image)
            # Update the text display of the password and confirm password input fields
            self.password_input._update_text_display()
            self.confirm_password_input._update_text_display()
            return

        # Add the on_activate callback so that when its clicked the toggle_view_password callback is run
        self.toggle_password.on_activate = lambda: toggle_view_password()
        # Add the event listeners for the toggle password button
        self.toggle_password.add_event_listeners(page_state=self.current_page, condition=active_form_condition)

        # Add the on_active callback so that when its clicked the set_sign_in callback is run
        self.sign_in_button.on_activate = lambda: self.set_sign_in(clear=True)
        # Add the listers for the sign_in button
        self.sign_in_button.add_event_listeners(page_state=self.current_page, condition=lambda: self.auth_sub_events["main"])

        # Add the on_active callback so that when its clicked the set_sign_up callback is run
        self.sign_up_button.on_activate = lambda: self.set_sign_up(clear=True)
        # Add the listers for the sign_up button
        self.sign_up_button.add_event_listeners(page_state=self.current_page, condition=lambda: self.auth_sub_events["main"])

        # Sub Page Controls
        # Add the on_activate callback so that when its clicked the set_main callback is run
        self.go_back_button.on_activate = self.set_main
        # Add the listers for the go back button
        self.go_back_button.add_event_listeners(page_state=self.current_page, condition=active_form_condition)

        # Add the on_activate callback so that when its clicked the submit_sign_in_form callback is run
        self.submit_sign_in.on_activate = self.submit_sign_in_form
        # Add the listers for the submit_sign_in button
        self.submit_sign_in.add_event_listeners(page_state=self.current_page, condition=lambda: active_form_condition() and self.username_input.valid and self.password_input.valid and not self.auth_sub_events["sign_up"])

        # Add the on_activate callback so that when its clicked the submit_sign_up_form callback is run
        self.submit_sign_up.on_activate = self.submit_sign_up_form
        # Add the listers for the submit_sign_up button
        self.submit_sign_up.add_event_listeners(page_state=self.current_page, condition=lambda: self.auth_sub_events["sign_up"] and not self.auth_sub_events["security_overlay"] and self.username_input.valid and self.password_input.valid and self.confirm_password_input.valid)

        # Overlay Controls
        # Add the on_activate callback so that when its clicked the generate_security_code callback is run
        self.new_code_button.on_activate = self.generate_security_code
        self.new_code_button.add_event_listeners(page_state=self.current_page, condition=lambda: self.auth_sub_events["security_overlay"])

        # Add the on_activate callback so that when its clicked the confirm_registration callback is run
        self.confirm_security_code.on_activate = self.confirm_registration
        # Add the listers for the confirm_security_code button
        self.confirm_security_code.add_event_listeners(page_state=self.current_page, condition=lambda: self.auth_sub_events["security_overlay"])

    @override
    def update_layout(self) -> None:
        # Refresh the shared page layout, so the UI can match the window size
        super().update_layout()

        # Update the main page text and authentication redirect buttons.
        self.text_surface.update_layout()
        self.sign_in_button.update_layout()
        self.sign_up_button.update_layout()

        # Update the authentication form, overlay, and security-code controls.
        self.overlay_background.update_layout()
        self.username_input.update_layout()
        self.password_input.update_layout()
        self.confirm_password_input.update_layout()
        self.toggle_password.update_layout()
        self.go_back_button.update_layout()

        self.submit_sign_in.update_layout()
        self.submit_sign_up.update_layout()
        
        self.security_code_overlay.update_layout()
        self.security_title_text.update_layout()
        self.security_code_text.update_layout()
        self.new_code_button.update_layout()
        self.confirm_security_code.update_layout()
        return
    
    def draw_redirect(self) -> None:
        # Draw the sign in button
        self.sign_in_button.draw()
        # Draw the sign up component
        self.sign_up_button.draw()
        return
    
    def draw_sign_in(self) -> None:
        # Draw the sign-in form fields and actions.
        self.username_input.draw()
        self.password_input.draw()
        # Draw the toggle password button
        self.toggle_password.draw()
        # Draw the submit sign in button
        self.submit_sign_in.draw()
        self.go_back_button.draw()

    def draw_sign_up(self) -> None:
        # Draw the sign-up form fields and actions.
        self.username_input.draw() # Draw the username input
        self.password_input.draw() # Draw the password input
        self.confirm_password_input.draw() # Draw the confirm password input
        self.toggle_password.draw() # Draw the toggle password button

        self.go_back_button.draw() # Draw the go back button
        return
        self.submit_sign_up.draw() # Draw the submit sign up button

    def draw_security_overlay(self) -> None:
        # Draw the security-code verification overlay and its controls.
        self.security_code_overlay.draw()
        self.security_title_text.draw()
        self.security_code_text.draw()
        self.new_code_button.draw()
        self.confirm_security_code.draw()

    @override
    def draw(self) -> None:
        # Always draw the background and page title text.
        self.quit_game_overlay_background.draw()
        self.text_surface.draw()

        # If the auth screen is on the main redirect page, show only the redirect options.
        if self.auth_sub_events["main"]:
            self.draw_redirect()
            return

        # Otherwise, draw the selected auth form and any security overlay.
        self.overlay_background.draw()
        if self.auth_sub_events["sign_in"]:
            # Draw the sign in form
            self.draw_sign_in()
        elif self.auth_sub_events["sign_up"]:
            # Draw the sign up form
            self.draw_sign_up()

        if self.auth_sub_events["security_overlay"]:
            self.draw_security_overlay()
        return