import pygame
import sys

# 1. Standard Pygame Setup
pygame.init()
screen = pygame.display.set_mode((800, 400))
pygame.display.set_caption("Uneven Shape Outline Test 🚀")
clock = pygame.time.Clock()

# 2. Load your specific image
# Make sure "button_type1.png" is in the exact same directory!
try:
    my_button = pygame.image.load("C:\\Project\\PyGame\\NEA\\src_main\\assets\\images\\button_type1.png").convert_alpha()
except FileNotFoundError:
    print("Oops! Couldn't find 'button_type1.png'. Make sure it's in the same folder.")
    sys.exit()

def draw_outlined_image(image, surface, x, y, color=(255, 215, 0), thickness=2):
    """Draws an image with a solid outline based on its transparent pixels."""
    # Create a mask of the image (ignores transparent pixels)
    mask = pygame.mask.from_surface(image)
    
    # Create a solid color silhouette from the mask
    outline_surface = mask.to_surface(setcolor=color, unsetcolor=(0,0,0,0))
    
    # Blit the silhouette offset in 8 directions to create the outline thickness
    for dx in [-thickness, 0, thickness]:
        for dy in [-thickness, 0, thickness]:
            if dx == 0 and dy == 0:
                continue # Skip the exact center
            surface.blit(outline_surface, (x + dx, y + dy))
            
    # Blit the original image directly over the center
    surface.blit(image, (x, y))


def get_just_the_outline(image, color=(255, 215, 0), thickness=2):
    """Returns a surface containing ONLY the expanded outline silhouette."""
    mask = pygame.mask.from_surface(image)
    outline_surface = mask.to_surface(setcolor=color, unsetcolor=(0,0,0,0))
    
    new_width = image.get_width() + (thickness * 2)
    new_height = image.get_height() + (thickness * 2)
    new_surface = pygame.Surface((new_width, new_height), pygame.SRCALPHA)
    
    # Blit the silhouette offset in 8 directions to make it thick
    for dx in [-thickness, 0, thickness]:
        for dy in [-thickness, 0, thickness]:
            if dx == 0 and dy == 0:
                continue 
            new_surface.blit(outline_surface, (thickness + dx, thickness + dy))
            
    # We stop here! We DO NOT draw the original image on top.
    return new_surface

new_surface = get_just_the_outline(image=my_button, color=(255, 255, 255), thickness=5)
pygame.image.save(surface=new_surface, file="button_type1_outline.png")

# 3. Main Game Loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Fill background with a dark color so the outline pops!
    screen.fill((30, 30, 40)) 

    # 4. Draw your button with an outline!
    # I set the outline to a gold/yellow color (255, 215, 0) and thickness to 2
    draw_outlined_image(my_button, screen, 150, 100, color=(255, 255, 255), thickness=2)

    #outlined_surface: Surface = 
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()