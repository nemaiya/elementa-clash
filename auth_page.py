import pygame
import sys
import random

# --- Constants ---
WIDTH, HEIGHT = 960, 540
FPS = 60

# Colors
BG_COLOR = (210, 180, 160)       # Warm beige/brown background
OVERLAY_COLOR = (235, 230, 215)  # Light beige for forms
OVERLAY_BORDER = (200, 180, 150)
POPUP_COLOR = (240, 240, 245)    # Slightly blueish white for popup
DARK_TEXT = (20, 20, 20)
WHITE = (255, 255, 255)
BTN_HOVER = (230, 230, 230)
INPUT_ACTIVE = (255, 255, 255)
INPUT_INACTIVE = (235, 230, 215)

pygame.init()

# --- UI Classes ---
class Button:
    def __init__(self, x, y, width, height, text, font, action=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.action = action
        self.is_hovered = False

    def draw(self, surface):
        color = BTN_HOVER if self.is_hovered else WHITE
        pygame.draw.rect(surface, color, self.rect, border_radius=5)
        pygame.draw.rect(surface, OVERLAY_BORDER, self.rect, width=2, border_radius=5)
        
        text_surf = self.font.render(self.text, True, DARK_TEXT)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered and self.action:
                self.action()

class TextInput:
    def __init__(self, x, y, width, height, placeholder, font):
        self.rect = pygame.Rect(x, y, width, height)
        self.placeholder = placeholder
        self.text = ""
        self.font = font
        self.active = False

    def draw(self, surface):
        color = INPUT_ACTIVE if self.active else INPUT_INACTIVE
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, OVERLAY_BORDER, self.rect, width=2)
        
        display_text = self.text if self.text else self.placeholder
        text_color = DARK_TEXT if self.text else (150, 150, 150)
        
        text_surf = self.font.render(display_text, True, text_color)
        surface.blit(text_surf, (self.rect.x + 10, self.rect.y + 10))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        elif event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                if len(self.text) < 20: # Limit length
                    self.text += event.unicode


# --- Main Application State Manager ---
class GameApp:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Auth Page")
        self.clock = pygame.time.Clock()
        
        # Fonts
        self.title_font = pygame.font.SysFont(name="arial", size=48, bold=True)
        self.font = pygame.font.SysFont(name="arial", size=20, bold=True)
        
        self.state = "MAIN_MENU"
        self.security_code = [str(random.randint(0, 9))]
        self.init_ui()

    def init_ui(self):
        # Center coordinates
        cx = WIDTH // 2

        # Main Menu UI
        self.btn_main_signin = Button(cx - 100, 240, 200, 40, "Sign Up", self.font, lambda: self.set_state("SIGN_IN"))
        self.btn_main_register = Button(cx - 100, 310, 200, 40, "Register", self.font, lambda: self.set_state("REGISTER"))

        # Sign In UI
        self.input_si_user = TextInput(cx - 125, 200, 250, 40, "Username", self.font)
        self.input_si_pass = TextInput(cx - 125, 270, 250, 40, "Password", self.font)
        self.btn_si_submit = Button(cx - 60, 370, 120, 35, "Sign In", self.font, lambda: print(f"Login: {self.input_si_user.text}"))
        self.btn_si_back = Button(720, 420, 40, 40, "<", self.font, lambda: self.set_state("MAIN_MENU"))

        # Register UI
        self.input_reg_user = TextInput(cx - 125, 180, 250, 40, "Username", self.font)
        self.input_reg_pass = TextInput(cx - 125, 250, 250, 40, "Password", self.font)
        self.input_reg_conf = TextInput(cx - 125, 320, 250, 40, "Confirm Pass", self.font)
        self.btn_reg_submit = Button(cx - 60, 400, 120, 35, "Register", self.font, lambda: self.set_state("SECURITY_POPUP"))
        self.btn_reg_back = Button(720, 440, 40, 40, "<", self.font, lambda: self.set_state("MAIN_MENU"))

        # Security Popup UI
        self.btn_sec_new = Button(cx - 150, 350, 140, 40, "New Code", self.font, self.generate_new_code)
        self.btn_sec_conf = Button(cx + 10, 350, 140, 40, "Confirm", self.font, lambda: self.set_state("MAIN_MENU"))

    def set_state(self, new_state):
        self.state = new_state

    def generate_new_code(self):
        self.security_code = str(random.randint(100000, 999999))

    def run(self):
        while True:
            self.handle_events()
            self.draw()
            pygame.display.flip()
            self.clock.tick(FPS)

    def handle_events(self):
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # Route events based on state
            if self.state == "MAIN_MENU":
                self.btn_main_signin.handle_event(event)
                self.btn_main_register.handle_event(event)
            elif self.state == "SIGN_IN":
                self.input_si_user.handle_event(event)
                self.input_si_pass.handle_event(event)
                self.btn_si_submit.handle_event(event)
                self.btn_si_back.handle_event(event)
            elif self.state == "REGISTER":
                self.input_reg_user.handle_event(event)
                self.input_reg_pass.handle_event(event)
                self.input_reg_conf.handle_event(event)
                self.btn_reg_submit.handle_event(event)
                self.btn_reg_back.handle_event(event)
            elif self.state == "SECURITY_POPUP":
                self.btn_sec_new.handle_event(event)
                self.btn_sec_conf.handle_event(event)

    def draw_text(self, text, y_pos):
        text_surf = self.title_font.render(text, True, DARK_TEXT)
        text_rect = text_surf.get_rect(center=(WIDTH // 2, y_pos))
        self.screen.blit(text_surf, text_rect)

    def draw_overlay_panel(self, width, height, y_offset=0):
        panel_rect = pygame.Rect(0, 0, width, height)
        panel_rect.center = (WIDTH // 2, HEIGHT // 2 + y_offset)
        pygame.draw.rect(self.screen, OVERLAY_COLOR, panel_rect)
        pygame.draw.rect(self.screen, OVERLAY_BORDER, panel_rect, width=4)
        return panel_rect

    def draw(self):
        self.screen.fill(BG_COLOR)

        if self.state == "MAIN_MENU":
            self.draw_text("Welcome to Elementa Clash", 120)
            self.btn_main_signin.draw(self.screen)
            self.btn_main_register.draw(self.screen)

        elif self.state == "SIGN_IN":
            self.draw_text("Welcome Back Player", 100)
            self.draw_overlay_panel(600, 320, y_offset=30)
            self.input_si_user.draw(self.screen)
            self.input_si_pass.draw(self.screen)
            self.btn_si_submit.draw(self.screen)
            self.btn_si_back.draw(self.screen)

        elif self.state in ["REGISTER", "SECURITY_POPUP"]:
            # Register screen is drawn for both states
            self.draw_text("Lets Get Registered", 80)
            self.draw_overlay_panel(600, 360, y_offset=40)
            self.input_reg_user.draw(self.screen)
            self.input_reg_pass.draw(self.screen)
            self.input_reg_conf.draw(self.screen)
            self.btn_reg_submit.draw(self.screen)
            self.btn_reg_back.draw(self.screen)

            if self.state == "SECURITY_POPUP":
                # Draw dimming effect
                dim = pygame.Surface((WIDTH, HEIGHT))
                dim.set_alpha(128)
                dim.fill((0, 0, 0))
                self.screen.blit(dim, (0, 0))
                
                # Draw Popup
                popup_rect = pygame.Rect(0, 0, 500, 250)
                popup_rect.center = (WIDTH // 2, HEIGHT // 2)
                pygame.draw.rect(self.screen, POPUP_COLOR, popup_rect, border_radius=10)
                
                # Popup Header
                pygame.draw.line(self.screen, DARK_TEXT, (popup_rect.left + 20, popup_rect.top + 50), (popup_rect.right - 20, popup_rect.top + 50), 2)
                header = self.title_font.render("Security Code!!", True, DARK_TEXT)
                self.screen.blit(header, header.get_rect(center=(WIDTH // 2, popup_rect.top + 25)))
                
                # Popup Text
                info = self.font.render(f"Remember the security code \"{self.security_code}\"", True, DARK_TEXT)
                self.screen.blit(info, info.get_rect(center=(WIDTH // 2, popup_rect.centery)))
                
                # Bottom Dark Bar (mimicking the image)
                bottom_bar = pygame.Rect(popup_rect.left, popup_rect.bottom - 70, popup_rect.width, 70)
                pygame.draw.rect(self.screen, (60, 60, 70), bottom_bar, border_bottom_left_radius=10, border_bottom_right_radius=10)
                
                self.btn_sec_new.draw(self.screen)
                self.btn_sec_conf.draw(self.screen)

if __name__ == "__main__":
    app = GameApp()
    app.run()