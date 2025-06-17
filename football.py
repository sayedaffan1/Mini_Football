import pygame
import sys
import random
import math

# Initialize pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 600
GOAL_WIDTH, GOAL_HEIGHT = 400, 250
GOALKEEPER_WIDTH, GOALKEEPER_HEIGHT = 80, 120
BALL_SIZE = 25
FPS = 60
GRAVITY = 0.15
FRICTION = 0.98

# Colors
SKY_COLOR = (135, 206, 235)
GRASS_COLOR = (34, 139, 34)
GOAL_COLOR = (240, 240, 240)
BALL_COLOR = (255, 215, 0)
GOALIE_COLOR = (30, 80, 200)
TEXT_COLOR = (255, 255, 255)
BUTTON_COLOR = (70, 130, 180)
BUTTON_HOVER = (100, 150, 200)

# Create the screen
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Penalty Shootout Game")
clock = pygame.time.Clock()

class Ball:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, BALL_SIZE, BALL_SIZE)
        self.velocity = [0, 0]
        self.in_play = False
        self.trail = []
    
    def update(self):
        # Apply physics
        self.velocity[1] += GRAVITY
        self.velocity[0] *= FRICTION
        self.velocity[1] *= FRICTION
        
        # Update position
        self.rect.x += self.velocity[0]
        self.rect.y += self.velocity[1]
        
        # Record trail
        self.trail.append((self.rect.centerx, self.rect.centery))
        if len(self.trail) > 10:
            self.trail.pop(0)
    
    def draw(self, surface):
        # Draw trail
        for i, pos in enumerate(self.trail):
            alpha = 200 * (i / len(self.trail))
            size = BALL_SIZE * (i / len(self.trail))
            pygame.draw.circle(surface, (255, 215, 0, int(alpha)), pos, int(size))
        
        # Draw ball
        pygame.draw.circle(surface, BALL_COLOR, self.rect.center, BALL_SIZE)

class Goalkeeper:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, GOALKEEPER_WIDTH, GOALKEEPER_HEIGHT)
        self.target_x = x
        self.dive_power = 0
        self.dive_direction = 0
        self.reaction_time = random.uniform(0.3, 0.7)
        self.reaction_counter = 0
    
    def update(self, ball):
        # Move toward target
        if abs(self.rect.centerx - self.target_x) > 2:
            self.rect.x += (self.target_x - self.rect.centerx) * 0.1
        
        # Dive logic
        if ball.in_play:
            self.reaction_counter += 1/FPS
            
            if self.reaction_counter >= self.reaction_time and self.dive_power == 0:
                # Predict ball trajectory
                predicted_x = ball.rect.centerx + ball.velocity[0] * 15
                goal_center = self.rect.centerx
                
                if abs(predicted_x - goal_center) > 40:  # Only dive for clear shots
                    self.dive_direction = -1 if predicted_x < goal_center else 1
                    power = abs(ball.velocity[0]) * 0.6 * self.dive_direction
                    self.dive_power = min(25, power)  # Fixed the parenthesis issue here
        
        # Apply dive
        if self.dive_power != 0:
            self.rect.x += self.dive_power * 0.5
            self.dive_power *= 0.9  # Slow down
    
    def draw(self, surface):
        pygame.draw.ellipse(surface, GOALIE_COLOR, self.rect)

class Button:
    def __init__(self, x, y, width, height, text, action=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.action = action
        self.is_hovered = False
    
    def draw(self, surface):
        color = BUTTON_HOVER if self.is_hovered else BUTTON_COLOR
        pygame.draw.rect(surface, color, self.rect, border_radius=5)
        pygame.draw.rect(surface, (255, 255, 255), self.rect, 2, border_radius=5)
        
        font = pygame.font.SysFont(None, 30)
        text_surf = font.render(self.text, True, TEXT_COLOR)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
    
    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)
        return self.is_hovered
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.is_hovered:
            if self.action:
                self.action()

def draw_goal(surface, goal):
    pygame.draw.rect(surface, GOAL_COLOR, goal, 5)
    # Draw net
    for i in range(0, GOAL_WIDTH, 15):
        pygame.draw.line(surface, (220, 220, 220), (goal.left + i, goal.top), (goal.left + i, goal.bottom), 1)
    for i in range(0, GOAL_HEIGHT, 15):
        pygame.draw.line(surface, (220, 220, 220), (goal.left, goal.top + i), (goal.right, goal.top + i), 1)

def draw_power_meter(surface, power, max_power, x, y, width, height):
    pygame.draw.rect(surface, (50, 50, 50), (x, y, width, height), 0, 5)
    power_width = int(width * (power/max_power))
    for i in range(power_width):
        pos = i / width
        r = int(255 * pos)
        g = int(255 * (1 - pos))
        pygame.draw.rect(surface, (r, g, 0), (x + i, y, 1, height))

def main():
    # Game objects
    goal = pygame.Rect(WIDTH//2 - GOAL_WIDTH//2, 50, GOAL_WIDTH, GOAL_HEIGHT)
    goalkeeper = Goalkeeper(WIDTH//2 - GOALKEEPER_WIDTH//2, goal.centery - GOALKEEPER_HEIGHT//2)
    ball = Ball(WIDTH//2 - BALL_SIZE//2, HEIGHT - 100)

    # Game state
    score = 0
    attempts = 0
    power = 0
    max_power = 100
    power_increasing = True
    game_state = "aiming"  # "aiming", "shooting", "scored", "saved", "missed"

    # Create buttons
    def quit_game():
        pygame.quit()
        sys.exit()
    
    quit_button = Button(WIDTH - 120, HEIGHT - 70, 100, 40, "Quit", quit_game)
    buttons = [quit_button]

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # Handle button events
            for button in buttons:
                button.check_hover(mouse_pos)
                button.handle_event(event)
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and game_state == "aiming":
                    # Shoot the ball
                    power = min(max_power, max(20, power))
                    angle = random.uniform(math.pi/4, 3*math.pi/4)
                    speed = 8 + (power / 12)
                    
                    ball.velocity = [
                        math.cos(angle) * speed * random.uniform(0.9, 1.1),
                        -math.sin(angle) * speed * random.uniform(0.9, 1.1)
                    ]
                    ball.in_play = True
                    attempts += 1
                    game_state = "shooting"
                    
                    # Set random goalkeeper target
                    goalkeeper.target_x = random.randint(
                        goal.left + GOALKEEPER_WIDTH//2, 
                        goal.right - GOALKEEPER_WIDTH//2
                    )
                    goalkeeper.reaction_time = random.uniform(0.3, 0.7)
                    goalkeeper.reaction_counter = 0
                    goalkeeper.dive_power = 0
                
                elif event.key == pygame.K_r and game_state in ["scored", "saved", "missed"]:
                    # Reset for next shot
                    ball = Ball(WIDTH//2 - BALL_SIZE//2, HEIGHT - 100)
                    goalkeeper = Goalkeeper(WIDTH//2 - GOALKEEPER_WIDTH//2, goal.centery - GOALKEEPER_HEIGHT//2)
                    game_state = "aiming"
                    power = 0
                    power_increasing = True

        # Update game state
        if game_state == "aiming":
            # Animate power meter
            if power_increasing:
                power += 2
                if power >= max_power:
                    power_increasing = False
            else:
                power -= 2
                if power <= 0:
                    power_increasing = True
        
        elif game_state == "shooting":
            ball.update()
            goalkeeper.update(ball)
            
            # Check for goal
            if ball.rect.colliderect(goal):
                game_state = "scored"
                score += 1
                ball.in_play = False
            
            # Check for save
            elif ball.rect.colliderect(goalkeeper.rect):
                game_state = "saved"
                ball.in_play = False
            
            # Check for miss
            elif ball.rect.bottom < goal.top or ball.rect.top < 0 or ball.rect.left < 0 or ball.rect.right > WIDTH:
                game_state = "missed"
                ball.in_play = False

        # Drawing
        screen.fill(SKY_COLOR)
        
        # Draw grass
        pygame.draw.rect(screen, GRASS_COLOR, (0, HEIGHT//2, WIDTH, HEIGHT//2))
        
        # Draw field markings
        pygame.draw.circle(screen, (255, 255, 255, 120), (WIDTH//2, HEIGHT - 150), 70, 2)
        pygame.draw.line(screen, (255, 255, 255, 120), (WIDTH//2, HEIGHT//2), (WIDTH//2, HEIGHT), 2)
        
        # Draw goal
        draw_goal(screen, goal)
        
        # Draw goalkeeper
        goalkeeper.draw(screen)
        
        # Draw ball
        ball.draw(screen)
        
        # Draw power meter
        if game_state == "aiming":
            draw_power_meter(screen, power, max_power, WIDTH//2 - 150, HEIGHT - 60, 300, 20)
        
        # Draw score
        font = pygame.font.SysFont(None, 36)
        score_text = font.render(f"Score: {score}/{attempts}", True, TEXT_COLOR)
        screen.blit(score_text, (20, 20))
        
        # Draw accuracy
        accuracy = 0 if attempts == 0 else int((score/attempts)*100)
        accuracy_text = font.render(f"Accuracy: {accuracy}%", True, TEXT_COLOR)
        screen.blit(accuracy_text, (20, 60))
        
        # Draw buttons
        for button in buttons:
            button.draw(screen)
        
        # Draw instructions
        if game_state == "aiming":
            text = font.render("Hold SPACE to set power, release to shoot", True, TEXT_COLOR)
            screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT - 30))
        elif game_state in ["scored", "saved", "missed"]:
            text = font.render("Press R to restart", True, TEXT_COLOR)
            screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT - 30))
        
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()