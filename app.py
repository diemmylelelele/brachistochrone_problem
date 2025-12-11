import pygame
import numpy as np
from scipy.optimize import fsolve
import sys
import math

# Size of the window
SCREEN_WIDTH = 1100
SCREEN_HEIGHT = 700
G = 9.81 * 100  # Gravity (pixels/s^2). Scale 1m = 100px

# Define the reset button
BUTTON_WIDTH = 150
BUTTON_HEIGHT = 50

# Colors
COLOR_BG = (255, 255, 255)       # White
COLOR_LINE = (0, 100, 255)      # Blue
COLOR_CYCLOID = (220, 50, 30)   # Red
COLOR_TEXT = (10, 10, 10)       # Black
COLOR_POINT = pygame.Color("#add7ec")       # Point color
COLOR_TITLE = pygame.Color("#3eb7f3")  # Title color
COLOR_BUTTON_BG = pygame.Color("#7ac8ee") # Button background color
COLOR_BUTTON_TEXT = pygame.Color("#ffffff") # White text for button
COLOR_CLICK_BORDER = pygame.Color("#bde1f3")  # Border color for the click-area rectangle


def world_to_screen(world_pos, zoom, offset):
    """Converts world coordinates to screen coordinates."""
    screen_x = int((world_pos[0] * zoom) + offset[0])
    screen_y = int((world_pos[1] * zoom) + offset[1])
    return (screen_x, screen_y)

def screen_to_world(screen_pos, zoom, offset):
    """Converts screen coordinates to world coordinates."""
    world_x = (screen_pos[0] - offset[0]) / zoom
    world_y = (screen_pos[1] - offset[1]) / zoom
    return (world_x, world_y)

def calculate_paths(A, B):
    '''
    This function calculates time for both straight line and cycloid paths
    between points A and B under gravity G.
        Inputs:
            A: tuple (xA, yA) - starting point
            B: tuple (xB, yB) - ending point (must be below A)
        Outputs:
            A dictionary with keys:
                "A", "B", "dx", "dy", "line_L", "line_a",
                "line_t", "line_points", "cycloid_r",
                "cycloid_theta_b", "cycloid_t",
                "cycloid_points"
    
    '''
    xa, ya = A
    xb, yb = B
    dx = xb - xa
    dy = yb - ya
    
    if dy <= 0: return None   # B must be below A, y-axis downwards
    L = math.sqrt(dx**2 + dy**2)   # Length of straight line

    if abs(dx) < 1.0:  # if points are almost vertically aligned - or if the path is straight down
        a_line = G
        t_line = math.sqrt(2 * L / a_line)  # time to fall a distance L under gravity G
        t_cycloid = t_line  # time for cycloid is same as line in this case
        r_cycloid = float('inf')  # a straight line with infinite radius of curvature
        theta_b_cycloid = 0
    else:  # if not vertically aligned - other cases
        a_line = G * dy / L  # acceleration along the line a = g sin(theta) = g * (dy / L)
        t_line = math.sqrt(2 * L / a_line)   # time to fall distance L under acceleration a_line follow the straightline ( d = 0.5*a*t^2 )
        
        # Use the absolute horizontal distance for the ratio calculation
        abs_dx = abs(dx)
        ratio = abs_dx / dy

        try:   # find time for the cycloid path
            theta_b_cycloid = fsolve(
                lambda th: (th - math.sin(th)) - ratio * (1 - math.cos(th)),
                math.pi
            )[0]
            r_cycloid = dy / (1 - math.cos(theta_b_cycloid))  # radius of the cycloid
            t_cycloid = theta_b_cycloid * math.sqrt(r_cycloid / G)  # time for cycloid ( time to travel from 0 to theta_b )
        except (RuntimeError, ValueError):
            return None

    line_points = [A, B]
    if np.isinf(r_cycloid):  # check if the r_cycloid is infinite (almost vertical line)
        cycloid_points = line_points  
    else:  # cycloid case
        # Get the direction (+1 for right, -1 for left)
        direction = np.sign(dx)
        thetas = np.linspace(0, theta_b_cycloid, 100) # parameter theta along the cycloid
        # Apply the direction to the x-component
        cycloid_x = xa + direction * r_cycloid * (thetas - np.sin(thetas))
        cycloid_y = ya + r_cycloid * (1 - np.cos(thetas))
        cycloid_points = list(zip(cycloid_x, cycloid_y))
        
    return {
        "A": A, "B": B, "dx": dx, "dy": dy, "line_L": L, "line_a": a_line,
        "line_t": t_line, "line_points": line_points, "cycloid_r": r_cycloid,
        "cycloid_theta_b": theta_b_cycloid, "cycloid_t": t_cycloid,
        "cycloid_points": cycloid_points,
    }

def draw_text_centered(surface, text, font, color, rect):
    '''
    Helper function to draw centered text in a given rectangle.
    '''
    text_obj = font.render(text, True, color)
    text_rect = text_obj.get_rect(center=rect.center)
    surface.blit(text_obj, text_rect)

# --- Main Application ---
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("Brachistochrone Problem Simulation")
    # Try to request the OS "maximized" window state (keeps title bar and taskbar visible).
    # This uses the pygame 2 SDL2 window API when available. If not available, we silently continue.
    try:
        from pygame._sdl2 import Window
        try:
            win = Window.from_display_module()
            win.maximize()
        except Exception:
            # If maximizing via SDL2 fails, ignore and continue with normal windowed mode
            # Try a Windows-specific fallback (ShowWindow) if we're on Windows and have a window handle
            try:
                import ctypes
                wm_info = pygame.display.get_wm_info()
                hwnd = wm_info.get('window') or wm_info.get('hwnd')
                if hwnd:
                    SW_MAXIMIZE = 3
                    ctypes.windll.user32.ShowWindow(hwnd, SW_MAXIMIZE)
            except Exception:
                pass
    except Exception:
        # pygame._sdl2 not available (older pygame) — try a Windows ShowWindow fallback
        try:
            import ctypes
            wm_info = pygame.display.get_wm_info()
            hwnd = wm_info.get('window') or wm_info.get('hwnd')
            if hwnd:
                SW_MAXIMIZE = 3
                ctypes.windll.user32.ShowWindow(hwnd, SW_MAXIMIZE)
        except Exception:
            pass
    clock = pygame.time.Clock()
    
    # Fonts
    font_title = pygame.font.SysFont("Times New Roman", 40, bold=True)
    font_subtitle = pygame.font.SysFont("Times New Roman", 17)
    font_main = pygame.font.SysFont("Times New Roman", 18)
    font_small = pygame.font.SysFont("Times New Roman", 17)
    font_button = pygame.font.SysFont("Times New Roman", 20, bold=True)
    font_winner = pygame.font.SysFont("Times New Roman", 60, bold=True)

    # --- App and Camera State ---
    state = 'pick_a'
    point_a_world = None # Points are now stored in "world" space
    point_b_world = None
    sim_data = None
    
    # Camera
    zoom = 1.0
    offset = [0, 0]
    panning = False
    
    # Sim variables
    sim_time = 0.0
    line_finished = False
    cycloid_finished = False
    pos_line_world = None
    pos_cycloid_world = None
    
    running = True
    while running:
        # Get current window size and compute UI rects so they respond to resizing
        screen_width, screen_height = screen.get_size()
        RESET_BUTTON_RECT = pygame.Rect(
            (screen_width - BUTTON_WIDTH) // 2,
            screen_height - BUTTON_HEIGHT - 30,
            BUTTON_WIDTH,
            BUTTON_HEIGHT
        )
        # Define the allowed click area (centered between the subtitle and the reset button)
        # Width will match the pixel width of the subtitle text so the rect aligns with the subtitle.
        subtitle_str = (
            "Given two points A and B in a vertical plane, what is the curve traced out by a point acted on only by gravity, "
            "which starts at A and reaches B in the shortest time."
        )
        subtitle_w, subtitle_h = font_subtitle.size(subtitle_str)
        # Use the subtitle width as the click area width (optionally add a little horizontal padding)
        horiz_padding = 20
        click_area_w = subtitle_w 
        # compute available vertical space between subtitle (y ~= 80) and top of reset button
        available_h = max(150, RESET_BUTTON_RECT.top - 120)
        # and a bit taller (use 0.9 of available vertical space)
        click_area_h = int(available_h * 0.9)
        click_area_top = int((80 + RESET_BUTTON_RECT.top) / 2 - click_area_h / 2)
        click_area_rect = pygame.Rect(
            (screen_width - click_area_w) // 2,
            click_area_top,
            click_area_w,
            click_area_h,
        )
        # --- Event Handling ---
        mouse_pos_screen = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # Check for mouse button events
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 3:  # if right-click
                    panning = True
                elif event.button == 1: # Left-click
                    # Reset button takes precedence
                    if RESET_BUTTON_RECT.collidepoint(mouse_pos_screen):
                        # Reset the simulation state
                        state = 'pick_a'
                        point_a_world = None
                        point_b_world = None
                        sim_data = None
                        zoom = 1.0
                        offset = [0, 0]
                    else:
                        # Only accept simulation clicks when they fall inside the designated click area
                        if not click_area_rect.collidepoint(mouse_pos_screen):
                            # ignore clicks outside the allowed region
                            # (this prevents clicking the title, subtitle, or other UI elements)
                            continue

                        # --- Sim Click (convert to world coordinates) ---
                        click_pos_world = screen_to_world(mouse_pos_screen, zoom, offset)

                        if state == 'pick_a':
                            point_a_world = click_pos_world
                            state = 'pick_b'

                        elif state == 'pick_b':
                            point_b_world = click_pos_world

                            if point_b_world[1] <= point_a_world[1]:
                                print("Error: Point B must be below Point A.")
                                point_b_world = None
                            else:
                                sim_data = calculate_paths(point_a_world, point_b_world)
                                if sim_data:
                                    state = 'simulate'
                                    sim_time = 0.0
                                    line_finished = False
                                    cycloid_finished = False
                                    pos_line_world = point_a_world
                                    pos_cycloid_world = point_a_world
                                else:
                                    print("Error: Could not solve.")
                                    point_b_world = None

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 3: # Right-click
                    panning = False
                    
            elif event.type == pygame.MOUSEMOTION:
                if panning:
                    offset[0] += event.rel[0]
                    offset[1] += event.rel[1]
            
            # --- Camera: Zooming ---
            elif event.type == pygame.MOUSEWHEEL:
                world_pos_before_zoom = screen_to_world(mouse_pos_screen, zoom, offset)
                
                if event.y > 0:
                    zoom *= 1.1 # Zoom in
                else:
                    zoom *= 0.9 # Zoom out
                zoom = max(0.1, zoom) # Don't zoom out too far
                
                screen_pos_after_zoom = world_to_screen(world_pos_before_zoom, zoom, offset)
                
                # Adjust offset to keep mouse position fixed
                offset[0] += mouse_pos_screen[0] - screen_pos_after_zoom[0]
                offset[1] += mouse_pos_screen[1] - screen_pos_after_zoom[1]
            
            # --- Keyboard Controls: exit, zoom, reset ---
            elif event.type == pygame.KEYDOWN:
                # Exit with Escape or 'q'
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                    running = False

                # Reset view with 0
                elif event.key == pygame.K_0:
                    zoom = 1.0
                    offset = [0, 0]

                else:
                    # Attempt to use unicode for '+' and '-' (handles shifted '=' key too)
                    ch = getattr(event, 'unicode', '')
                    # Zoom in with +, = or keypad +
                    if ch == '+' or ch == '=' or event.key == pygame.K_KP_PLUS:
                        world_pos_before_zoom = screen_to_world(mouse_pos_screen, zoom, offset)
                        zoom *= 1.1
                        zoom = max(0.1, zoom)
                        screen_pos_after_zoom = world_to_screen(world_pos_before_zoom, zoom, offset)
                        offset[0] += mouse_pos_screen[0] - screen_pos_after_zoom[0]
                        offset[1] += mouse_pos_screen[1] - screen_pos_after_zoom[1]

                    # Zoom out with - or keypad -
                    elif ch == '-' or event.key == pygame.K_KP_MINUS:
                        world_pos_before_zoom = screen_to_world(mouse_pos_screen, zoom, offset)
                        zoom *= 0.9
                        zoom = max(0.1, zoom)
                        screen_pos_after_zoom = world_to_screen(world_pos_before_zoom, zoom, offset)
                        offset[0] += mouse_pos_screen[0] - screen_pos_after_zoom[0]
                        offset[1] += mouse_pos_screen[1] - screen_pos_after_zoom[1]

            # Window resize event
            elif event.type == pygame.VIDEORESIZE:
                # Recreate the screen surface at the new size and keep RESIZABLE
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                screen_width, screen_height = event.w, event.h

        # Simulation Update ---
        if state == 'simulate':
            dt = clock.get_time() / 1000.0
            sim_time += dt

            # Update Line Bead
            if not line_finished:
                t = sim_data['line_t']
                if sim_time < t:
                    dist = 0.5 * sim_data['line_a'] * sim_time**2
                    frac = dist / sim_data['line_L']
                    pos_line_world = (
                        point_a_world[0] + frac * sim_data['dx'],
                        point_a_world[1] + frac * sim_data['dy']
                    )
                else:
                    pos_line_world = point_b_world
                    line_finished = True

            # Update Cycloid Bead
            if not cycloid_finished:
                t = sim_data['cycloid_t']
                if sim_time < t:
                    if np.isinf(sim_data['cycloid_r']):
                        dist = 0.5 * G * sim_time**2
                        frac = dist / sim_data['dy']
                        pos_cycloid_world = (point_a_world[0], point_a_world[1] + frac * sim_data['dy'])
                    else:
                        r = sim_data['cycloid_r']
                        theta_t = sim_time / math.sqrt(r / G)
                        
                        # --- MODIFICATION FOR LEFT/RIGHT ---
                        # Get direction from stored dx
                        direction = np.sign(sim_data['dx'])
                        pos_cycloid_world = (
                            # Apply the direction to the x-component
                            point_a_world[0] + direction * r * (theta_t - math.sin(theta_t)),
                            point_a_world[1] + r * (1 - math.cos(theta_t))
                        )
                        # --- END MODIFICATION ---
                else:
                    pos_cycloid_world = point_b_world
                    cycloid_finished = True

            if line_finished and cycloid_finished:
                state = 'results'

        # --- 3. Drawing ---
        screen.fill(COLOR_BG)

        # --- Draw Simulation (in World Space) ---
        if point_a_world:
            pos_a_screen = world_to_screen(point_a_world, zoom, offset)
            pygame.draw.circle(screen, COLOR_POINT, pos_a_screen, 10)
            screen.blit(font_small.render("A", True, COLOR_TEXT), (pos_a_screen[0] - 25, pos_a_screen[1] - 10))

        if state == 'simulate' or state == 'results':
            # Draw Point B
            pos_b_screen = world_to_screen(point_b_world, zoom, offset)
            pygame.draw.circle(screen, COLOR_POINT, pos_b_screen, 10)
            screen.blit(font_small.render("B", True, COLOR_TEXT), (pos_b_screen[0] + 15, pos_b_screen[1] - 10))
            
            # --- Draw Paths (Must transform all points) ---
            screen_line_points = [world_to_screen(p, zoom, offset) for p in sim_data['line_points']]
            screen_cycloid_points = [world_to_screen(p, zoom, offset) for p in sim_data['cycloid_points']]
            
            pygame.draw.aalines(screen, COLOR_LINE, False, screen_line_points, 3)
            pygame.draw.aalines(screen, COLOR_CYCLOID, False, screen_cycloid_points, 3)
            
            # Draw Beads
            pos_line_screen = world_to_screen(pos_line_world, zoom, offset)
            pos_cycloid_screen = world_to_screen(pos_cycloid_world, zoom, offset)
            pygame.draw.circle(screen, COLOR_LINE, pos_line_screen, 8)
            pygame.draw.circle(screen, COLOR_CYCLOID, pos_cycloid_screen, 8)

        
        # --- Draw UI (in Screen Space) ---

        # Title
        title_text = font_title.render("Brachistochrone Problem", True, COLOR_TITLE)
        screen.blit(title_text, (screen_width // 2 - title_text.get_width() // 2, 20))

        # Subtitle
        subtitle_text = font_subtitle.render(
            "Given two points A and B in a vertical plane, what is the curve traced out by a point acted on only by gravity, "
            "which starts at A and reaches B in the shortest time.", True, COLOR_TEXT
        )
        screen.blit(subtitle_text, (screen_width // 2 - subtitle_text.get_width() // 2, 80))

        # Instructions (render inside the click-area rectangle so users know where to click)
        if state == 'pick_a':
            text = font_main.render("Click anywhere to set Point A", True, COLOR_TEXT)
        elif state == 'pick_b':
            text = font_main.render("Click anywhere *below* Point A to set Point B", True, COLOR_TEXT)
        else:
            text = None

        if text:
            # position text centered horizontally within the click area and near its top
            text_x = click_area_rect.left + (click_area_rect.width - text.get_width()) // 2
            text_y = click_area_rect.top + 8
            screen.blit(text, (text_x, text_y))

        # Draw the allowed click area (translucent overlay + border)
        try:
            overlay = pygame.Surface((click_area_rect.width, click_area_rect.height), pygame.SRCALPHA)
            overlay.fill((200, 200, 200, 30))  # light translucent gray
            screen.blit(overlay, click_area_rect.topleft)
        except Exception:
            # If anything fails, skip translucent overlay
            pass
        # Draw border using requested color
        pygame.draw.rect(screen, COLOR_CLICK_BORDER, click_area_rect, 2)

        # Times (centered below the click-area) - show only after both beads finish (state == 'results')
        if state == 'results' and sim_data:
            # Render each time in the matching color for clarity
            t_line_str = f"Line: {sim_data['line_t']:.3f} s"
            t_cyc_str = f"Cycloid: {sim_data['cycloid_t']:.3f} s"
            text_line = font_main.render(t_line_str, True, COLOR_LINE)
            text_cyc = font_main.render(t_cyc_str, True, COLOR_CYCLOID)

            # compute combined width and position them with small gap
            gap = 20
            combined_w = text_line.get_width() + gap + text_cyc.get_width()
            base_x = click_area_rect.left + (click_area_rect.width - combined_w) // 2
            times_y = click_area_rect.bottom + 8

            screen.blit(text_line, (base_x, times_y))
            screen.blit(text_cyc, (base_x + text_line.get_width() + gap, times_y))

        # Reset Button
        pygame.draw.rect(screen, COLOR_BUTTON_BG, RESET_BUTTON_RECT, border_radius=10)
        draw_text_centered(screen, "New Simulation", font_button, COLOR_BUTTON_TEXT, RESET_BUTTON_RECT)

        # Final Flip
        pygame.display.flip()
        clock.tick(60) 

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()