from engi1020.arduino.api import *
import pygame
import threading
import time
import level_2

WIDTH, HEIGHT = 1070, 600
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Arduino Mayhem!")
pygame.font.init()

SPEECH_SIZE = round((40/600)*HEIGHT)
SPEECH_FONT = pygame.font.SysFont('timesnewroman', SPEECH_SIZE)
SPEECH_DELAY = 0.03

FIRST_LINES = {"........ (tap space quickly to view the next line)":'neutral',
               "!              ":"surprised",
               "Why hello there....":"neutral",
               "I see you have with you... an arduino board!":"happy",
               "Press the button to show me your competent enough to use it... hehe":"neutral"}

SECOND_LINES = {".......":"surprised",
                "Did you actually just manage to do that??":"surprised",
                "Click the button again just so that I make sure... ":"neutral"}

THIRD_LINES = {"GOOD JOB!":"happy",
               "WOW       ":"happy",
               "TRULY AMAZING.....":"happy",
               "Let's go have some fun!":"neutral",
               "LEVEL 2!!!!!!":"happy"}

current_text = ''

PLAYER_WIDTH, PLAYER_HEIGHT = round((25/854)*WIDTH), round((25/480)*HEIGHT)
LIGHTBULB_WIDTH, LIGHTBULB_HEIGHT = round((100/854)*WIDTH), round((120/480)*HEIGHT)

LIGHTBULB_MAN_SPRITES = {"neutral":"lightbulb_man_neutral.png",
                         "happy":"lightbulb_man_happy.png",
                         "surprised":"lightbulb_man_surprised.png",
                         "terrified":"lightbulb_man_terrified.png"}
CURRENT_LIGHTBULB_MAN_STATE = None

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)

running = True
FPS = 60

VEL = round((8/600)*WIDTH)

def set_lightbulbman_state(state):
    """Takes a string as an input corresponding to a key in the dictionary called
    LIGHTBULB_MAN SPRITES. Sets the variable CURRENT_LIGHTBULB_MAN_STATE to the
    corresponding asset to the passed in emotion"""
    global CURRENT_LIGHTBULB_MAN_STATE

    if state not in LIGHTBULB_MAN_SPRITES.keys():
        print(f"Cannot find state {state}")
    else:
        lightbulb_man_image = pygame.image.load(f"Assets\{LIGHTBULB_MAN_SPRITES[state]}")
        CURRENT_LIGHTBULB_MAN_STATE = pygame.transform.scale(lightbulb_man_image,
                                                             (LIGHTBULB_WIDTH, LIGHTBULB_HEIGHT))


def draw_window(player, lightbulb_man):
    """Takes in the player and lightbulb_man rectangles. Renders every object, including
                objects defined in global iterables such as event_objects and event_rectangles.
                This allows event threads to also use this function."""
    WIN.fill(BLACK)

    pygame.draw.rect(WIN, RED, player)
    WIN.blit(CURRENT_LIGHTBULB_MAN_STATE, (lightbulb_man.x, lightbulb_man.y))

    speech = SPEECH_FONT.render(
        str(current_text), 1, WHITE)
    speech = pygame.transform.scale(speech, (round(speech.get_size()[0]*(2/3)), round(speech.get_size()[1]*(2/3))))
    if speech.get_size()[0] > WIDTH - LIGHTBULB_WIDTH:
        ratio = (WIDTH-LIGHTBULB_WIDTH)/speech.get_size()[0]
        scaled_width = round(speech.get_size()[0] * ratio)
        scaled_height = round(speech.get_size()[1] * ratio)
        speech = pygame.transform.scale(speech, (scaled_width, scaled_height))

    WIN.blit(speech, (10, 10))

    pygame.display.update()

def player_move(keys_pressed, player, lightbulb_man):
    """Takes in the keys_pressed, the player, and the lightbulb man. Uses this to give player movement while respecting
    boundaries."""
    if (keys_pressed[pygame.K_LEFT] or keys_pressed[pygame.K_a]) and player.x - VEL > 0:  # LEFT
        player.x -= VEL
    if (keys_pressed[pygame.K_RIGHT] or keys_pressed[pygame.K_d]) and (player.x + VEL + PLAYER_WIDTH < WIDTH) and not lightbulb_man.colliderect(player):  # RIGHT
        player.x += VEL
    if (keys_pressed[pygame.K_UP] or keys_pressed[pygame.K_w]) and player.y - VEL > SPEECH_SIZE and not lightbulb_man.colliderect(player):  # UP
        player.y -= VEL
    if (keys_pressed[pygame.K_DOWN] or keys_pressed[pygame.K_s]) and player.y + VEL + PLAYER_HEIGHT < HEIGHT:  # DOWN
        player.y += VEL

def print_lines(lines, auto_skip_to_event = True, wait_to_skip=False):
    '''If wait_to_skip is true, then there will be a delay of 2 seconds after the last line.
     If auto_skip_to_event is true, then it will skip without user input after last line.'''
    global current_text
    current_text = ''

    line_index = 0
    skip_to_event = False

    lines_dict = lines
    lines = list(lines.keys())

    for line in lines:
        set_lightbulbman_state(lines_dict[line])
        while True:
            if line_index <= len(line):
                current_text = line[:line_index]
                line_index += 1
                time.sleep(SPEECH_DELAY)
            else:
                if lines.index(line) == len(lines)-1:
                    skip_to_event = True
                line_index = 0
                time.sleep(SPEECH_DELAY)
                break
        if skip_to_event:
            if not auto_skip_to_event:
                check_key_pressed()
            elif wait_to_skip:
                time.sleep(2)
            else:
                break
        else:
            check_key_pressed()

def check_key_pressed():
    """Breaks out of loop when space is pressed"""
    while True:
        keys_pressed = pygame.key.get_pressed()
        if keys_pressed[pygame.K_SPACE] == True:
            break


def events():
    """This function is threaded and contains the events of the level in chronological order"""
    #Allow pygame to start
    time.sleep(5)
    global current_text, running

    print_lines(FIRST_LINES)


    ####### EVENT 1
    while True:
        if digital_read(6) == True:
            break
    #######

    print_lines(SECOND_LINES)

    ####### EVENT 2
    while True:
        if digital_read(6) == True:
            break
    #######

    print_lines(THIRD_LINES)

    time.sleep(2)
    running = False

def main():
    """Starts the thread and initializes objects, then handles the main game loop."""
    events_thread = threading.Thread(target=events, daemon=True)
    events_thread.start()

    player = pygame.Rect(200, 200, PLAYER_WIDTH, PLAYER_HEIGHT)
    lightbulb_man = pygame.Rect(WIDTH-LIGHTBULB_WIDTH, 0, LIGHTBULB_WIDTH, LIGHTBULB_HEIGHT)
    set_lightbulbman_state('neutral')

    clock = pygame.time.Clock()

    while True: #Check if Arduino is connected
        try:
            digital_write(4, True)
            digital_write(4, False)
            break
        except:
            pass

    while running:

        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()

        keys_pressed = pygame.key.get_pressed()
        player_move(keys_pressed, player, lightbulb_man)
        draw_window(player, lightbulb_man)

    level_2.main()

if __name__ == "__main__":
    main()