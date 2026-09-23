import pygame
import sys
import math

# Initialize Pygame
pygame.init()

# Screen dimensions updated to 960x540
WIDTH, HEIGHT = 960, 540
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Welcome to Elementa Clash")

# Colors
COLOR_BG_START = (15, 15, 15)
COLOR_BG_END = (110, 110, 110)
COLOR_PANEL = (95, 112, 135)
COLOR_TRACK = (180, 180, 180)
COLOR_KNOB = (0, 0, 0)
COLOR_TEXT_BLACK = (20, 20, 20)
COLOR_TEXT_WHITE = (245, 245, 245)
COLOR_ARROW = (215, 185, 145)
COLOR_DROPDOWN_BG = (255, 255, 255)
COLOR_ITEM_BG = (230, 235, 240)
COLOR_GEAR_BG = (200, 200, 200)

# Fonts
font_main = pygame.font.SysFont("segoeui", 20, bold=True)
font_small = pygame.font.SysFont("segoeui", 14, bold=True)


def draw_gradient_background(surface, color1, color2):
    rect = surface.get_rect()
    for x in range(rect.width):
        blend = x / rect.width
        r = int(color1[0] + (color2[0] - color1[0]) * blend)
        g = int(color1[1] + (color2[1] - color1[1]) * blend)
        b = int(color1[2] + (color2[2] - color1[2]) * blend)
        pygame.draw.line(surface, color=(r, g, b), start_pos=(x, 0), end_pos=(x, rect.height))


def draw_gear_icon(surface, x, y, radius):
    pygame.draw.circle(surface, COLOR_GEAR_BG, (x, y), radius)
    pygame.draw.circle(surface, COLOR_ARROW, (x, y), radius - 4)
    for angle in range(0, 360, 45):
        rad = math.radians(angle)
        start_x = x + (radius - 8) * math.cos(rad)
        start_y = y + (radius - 8) * math.sin(rad)
        end_x = x + (radius - 2) * math.cos(rad)
        end_y = y + (radius - 2) * math.sin(rad)
        pygame.draw.line(surface, COLOR_ARROW, (start_x, start_y), (end_x, end_y), 4)
    pygame.draw.circle(surface, COLOR_GEAR_BG, (x, y), radius - 8)


def draw_reset_icon(surface, x, y):
    pygame.draw.rect(surface, COLOR_DROPDOWN_BG, (x, y, 16, 16), border_radius=3)
    # Draw simple curved arrow representation
    pygame.draw.arc(surface, COLOR_PANEL, (x+3, y+3, 10, 10), math.pi, math.pi*2.5, 2)
    pygame.draw.polygon(surface, COLOR_PANEL, [(x+2, y+8), (x+6, y+8), (x+4, y+12)])


class Label:
    def __init__(self, x, y, width, height, text, text_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.text_color = text_color

    def draw(self, surface):
        pygame.draw.rect(surface, COLOR_PANEL, self.rect, border_radius=12)
        text_surf = font_main.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)


class Button:
    def __init__(self, x, y, width, height, text, text_color, icon_type=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.text_color = text_color
        self.icon_type = icon_type

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False

    def draw(self, surface):
        pygame.draw.rect(surface, COLOR_PANEL, self.rect, border_radius=12)
        text_surf = font_main.render(self.text, True, self.text_color)
        
        if self.icon_type == "reset":
            text_rect = text_surf.get_rect(center=(self.rect.centerx + 10, self.rect.centery))
            draw_reset_icon(surface, self.rect.x + 15, self.rect.centery - 8)
        else:
            text_rect = text_surf.get_rect(center=self.rect.center)
            
        surface.blit(text_surf, text_rect)


class IconButton:
    def __init__(self, x, y, radius, icon_type):
        self.x = x
        self.y = y
        self.radius = radius
        self.icon_type = icon_type
        self.rect = pygame.Rect(x - radius, y - radius, radius * 2, radius * 2)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False

    def draw(self, surface):
        if self.icon_type == "gear":
            draw_gear_icon(surface, self.x, self.y, self.radius)


class Slider:
    def __init__(self, x, y, width, height, min_val, max_val, initial_val):
        self.rect = pygame.Rect(x, y, width, height)
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial_val
        self.knob_radius = 15
        self.is_dragging = False

    def get_knob_x(self):
        percentage = (self.value - self.min_val) / (self.max_val - self.min_val)
        return int(self.rect.left + percentage * self.rect.width)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            knob_x = self.get_knob_x()
            distance = ((event.pos[0] - knob_x)**2 + (event.pos[1] - self.rect.centery)**2)**0.5
            if distance <= self.knob_radius or self.rect.collidepoint(event.pos):
                self.is_dragging = True
                self.update_value_from_pos(event.pos[0])
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.is_dragging = False
        elif event.type == pygame.MOUSEMOTION and self.is_dragging:
            self.update_value_from_pos(event.pos[0])

    def update_value_from_pos(self, x_pos):
        relative_x = max(0, min(x_pos - self.rect.left, self.rect.width))
        percentage = relative_x / self.rect.width
        self.value = self.min_val + percentage * (self.max_val - self.min_val)

    def draw(self, surface):
        pygame.draw.rect(surface, COLOR_TRACK, self.rect, border_radius=self.rect.height//2)
        pygame.draw.circle(surface, COLOR_KNOB, (self.get_knob_x(), self.rect.centery), self.knob_radius)


class Dropdown:
    def __init__(self, x, y, width, height, text, options, is_open=False):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.options = options
        self.is_open = is_open
        self.selected_option = None

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.is_open = not self.is_open
            elif self.is_open:
                for i, option in enumerate(self.options):
                    option_rect = pygame.Rect(self.rect.x + 10, self.rect.bottom + 5 + (i * 25), self.rect.width - 20, 20)
                    if option_rect.collidepoint(event.pos):
                        self.selected_option = option
                        self.is_open = False

    def draw(self, surface):
        pygame.draw.rect(surface, COLOR_PANEL, self.rect, border_radius=12)
        text_surf = font_main.render(self.text, True, COLOR_TEXT_WHITE)
        surface.blit(text_surf, (self.rect.x + 20, self.rect.y + 10))
        
        arrow_x, arrow_y = self.rect.right - 25, self.rect.centery - 5
        pygame.draw.polygon(surface, COLOR_ARROW, [(arrow_x, arrow_y), (arrow_x + 16, arrow_y), (arrow_x + 8, arrow_y + 12)])

        if self.is_open:
            menu_rect = pygame.Rect(self.rect.x + 20, self.rect.bottom, self.rect.width - 40, len(self.options) * 25 + 10)
            pygame.draw.rect(surface, COLOR_DROPDOWN_BG, menu_rect)
            for i, option in enumerate(self.options):
                item_rect = pygame.Rect(menu_rect.x + 5, menu_rect.y + 5 + (i * 25), menu_rect.width - 10, 22)
                pygame.draw.rect(surface, COLOR_ITEM_BG, item_rect)
                opt_surf = font_small.render(option, True, (80, 90, 100))
                surface.blit(opt_surf, (item_rect.x + 5, item_rect.y + 2))


def main():
    clock = pygame.time.Clock()
    bg_surface = pygame.Surface((WIDTH, HEIGHT))
    draw_gradient_background(bg_surface, COLOR_BG_START, COLOR_BG_END)

    # Top elements
    settings_btn = IconButton(935, 25, 18, "gear")
    
    # Core settings elements
    audio_label = Label(60, 50, 200, 45, "Audio", COLOR_TEXT_WHITE)
    sfx_label = Label(60, 115, 200, 45, "SFX Audio", COLOR_TEXT_WHITE)
    audio_slider = Slider(380, 65, 400, 14, 0, 100, 0)  
    sfx_slider = Slider(380, 130, 400, 14, 0, 100, 0)
    font_dropdown = Dropdown(60, 240, 210, 45, "Change Font", ["Your paragraph text", "Your paragraph text"], is_open=True)
    fps_dropdown = Dropdown(330, 240, 210, 45, "Change FPS", ["30 FPS", "60 FPS"], is_open=False)

    # Bottom Buttons
    reset_btn = Button(30, HEIGHT - 70, 200, 45, "Reset Setting", COLOR_TEXT_WHITE, icon_type="reset")
    save_btn = Button(WIDTH - 230, HEIGHT - 70, 200, 45, "Save Changes", COLOR_TEXT_WHITE)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            audio_slider.handle_event(event)
            sfx_slider.handle_event(event)
            font_dropdown.handle_event(event)
            fps_dropdown.handle_event(event)
            
            if reset_btn.handle_event(event):
                print("Reset Settings Clicked")
            if save_btn.handle_event(event):
                print("Save Changes Clicked")
            if settings_btn.handle_event(event):
                print("Settings Gear Clicked")

        screen.blit(bg_surface, (0, 0))

        settings_btn.draw(screen)
        audio_label.draw(screen)
        sfx_label.draw(screen)
        audio_slider.draw(screen)
        sfx_slider.draw(screen)
        reset_btn.draw(screen)
        save_btn.draw(screen)
        
        # Draw dropdowns last to ensure menus overlap other elements
        fps_dropdown.draw(screen)
        font_dropdown.draw(screen)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()