from engi1020.arduino.api import *
import pygame
import threading
import time
import random
import level_4

WIDTH, HEIGHT = 1070, 600
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Arduino Mayhem!")
pygame.font.init()

SPEECH_SIZE = round((40/600)*HEIGHT)
SPEECH_FONT = pygame.font.SysFont('timesnewroman', SPEECH_SIZE)
SPEECH_DELAY = 0.03
characters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!#?"

def make_passcode(characters):
    """Returns a string of 4 random characters"""
    chars = [random.choice(characters) for i in range(4)]
    passcode = ''
    for char in chars:
        passcode += str(char)
    return passcode


PASSCODE = make_passcode(characters)

FIRST_LINES = {"Ok, this is where you will get stuck for good.":'neutral',
              "You see, I have a very interesting hobby...":"neutral",
              "I love making secret codes.":"happy",
              "If you want to get past this level,":"neutral",
              "You are going to have to figure out the code to get out of here!":"neutral",
              "How, you may ask?":"surprised",
              "Well, I'll never tell you!":"happy",
              "And you'll be stuck here forever!":"terrified",
              "Now, where did I put that code...":"surprised",
              "You stay here, and I'll be right back.":"neutral",
              "And don't go messing with your Arduino until I get back.":"angry",}


SECOND_LINES = {"Ok, I'm back":"neutral",
                "Let's see you -NOT- crack this code":"happy",
                "Click on this text to type it if you think you got it.. hehehehe":"neutral"}

LAST_LINES = {"WHAT?!?":"terrified",
               "How did you figure out my code?!":"terrified",
               "You are smarter than I thought...":"surprised",
               "That's it!":"angry",
               "Time to bring out a true test of skill this time!":"neutral",
               "LEVEL 4!!!!":"neutral"}



current_text = ''

PLAYER_WIDTH, PLAYER_HEIGHT = round((25/854)*WIDTH), round((25/480)*HEIGHT)
LIGHTBULB_WIDTH, LIGHTBULB_HEIGHT = round((100/854)*WIDTH), round((120/480)*HEIGHT)

LIGHTBULB_MAN_SPRITES = {"neutral":"lightbulb_man_neutral.png",
                         "happy":"lightbulb_man_happy.png",
                         "surprised":"lightbulb_man_surprised.png",
                         "terrified":"lightbulb_man_terrified.png",
                         "angry":"lightbulb_man_angry.png",
                         "transparent":"lightbulb_man_transparent.png"}
CURRENT_LIGHTBULB_MAN_STATE = None

solid_objects = []
event_objects = []
event_rectangles = []
mouse_event_data = (False, 0) #The first value corresponds to mouse being pressed and the second is mouse pos
text_typed = ''

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)

running = True
player_roam = True
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

def will_collide(object, direction, object_vel):
    """Determines whether the object passed in will or will not collide, with the given velocity
         with any object in the solid_objects list"""
    if direction == "sideways":
        theoretical_object = pygame.Rect(object.x + object_vel, object.y, object.width, object.height)
    elif direction == "up_down":
        theoretical_object = pygame.Rect(object.x, object.y+ object_vel, object.width, object.height)
    for solid_object in solid_objects:
        if solid_object.colliderect(theoretical_object):
            return True
    return False


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

    for object in event_objects:
        WIN.blit(object[1], (object[0].x, object[0].y))

    for object in event_rectangles:
        pygame.draw.rect(WIN, object[1], object[0])


    pygame.display.update()

def player_move(keys_pressed, player, lightbulb_man):
    """Takes in the keys_pressed and the player. Used to give player movement while respecting
            boundaries, and aided by the will_collide function."""
    if (keys_pressed[pygame.K_LEFT] or keys_pressed[pygame.K_a]) and player.x - VEL > 0 and not will_collide(player, "sideways", -VEL):  # LEFT
        player.x -= VEL
    if (keys_pressed[pygame.K_RIGHT] or keys_pressed[pygame.K_d]) and (player.x + VEL + PLAYER_WIDTH < WIDTH) and not will_collide(player, "sideways", VEL):  # RIGHT
        player.x += VEL
    if (keys_pressed[pygame.K_UP] or keys_pressed[pygame.K_w]) and player.y - VEL > SPEECH_SIZE and not will_collide(player, "up_down", -VEL):  # UP
        player.y -= VEL
    if (keys_pressed[pygame.K_DOWN] or keys_pressed[pygame.K_s]) and player.y + VEL + PLAYER_HEIGHT < HEIGHT and not will_collide(player, "up_down", VEL):  # DOWN
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


def event_1():
    '''Create a place to input a list of characters similar to typing a passcode.
       The passcode will be given to the player via the OLED screen at the players command,
       ex; pushing the button.'''
    global player, event_rectangles, player_roam, current_text, text_typed
    player.x = 200
    player.y = 200

    set_lightbulbman_state("transparent")

    oled_clear()
    oled_print('Hey, over here')
    time.sleep(2.5)
    oled_print('Press the button')
    oled_print('if you see this')

    while True:
        if digital_read(6) == True:
            break

    oled_clear()
    oled_print('OK, here is')
    oled_print('the code...')
    time.sleep(2)
    oled_clear()
    oled_print(PASSCODE)

    print_lines(SECOND_LINES)

    input_box = pygame.Rect(0, 0, WIDTH-LIGHTBULB_WIDTH, 45)

    while True:
        if mouse_event_data[0] == True:
            if input_box.colliderect(pygame.Rect(mouse_event_data[1][0], mouse_event_data[1][1], 1, 1)):
                player_roam = False
                text_typed = ''
                while True:
                    current_text = text_typed
                    if len(text_typed) == 4 and text_typed != PASSCODE:
                        current_text = "WRONG CODE"
                        time.sleep(1)
                        text_typed = ''
                    elif len(text_typed) == 4 and text_typed == PASSCODE:
                        current_text = PASSCODE
                        break
                break

        mouse_event_data == (False, 0)

    time.sleep(1)

    pass


def events():
    """This function is threaded and contains the events of the level in chronological order"""
    #Allow pygame to start
    time.sleep(5)
    global current_text, running

    print_lines(FIRST_LINES, wait_to_skip= True)

    ####### EVENT 1
    event_1()
    #######

    print_lines(LAST_LINES)

    time.sleep(3)
    running = False

def main():
    """Starts the thread and initializes objects, then handles the main game loop."""
    events_thread = threading.Thread(target=events, daemon=True)
    events_thread.start()

    global player, mouse_event_data, text_typed
    player = pygame.Rect(200, 200, PLAYER_WIDTH, PLAYER_HEIGHT)
    lightbulb_man = pygame.Rect(WIDTH-LIGHTBULB_WIDTH, 0, LIGHTBULB_WIDTH, LIGHTBULB_HEIGHT)
    solid_objects.append(lightbulb_man)
    set_lightbulbman_state('neutral')

    clock = pygame.time.Clock()

    while True: #Check if Arduino is connected
        try:
            digital_write(4, True)
            digital_write(4, False)
            break
        except:
            print("Arduino not working...")

    while running:

        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_event_data = (True, event.pos)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    text_typed = text_typed[:-1]
                else:
                    text_typed += event.unicode

        keys_pressed = pygame.key.get_pressed()
        if player_roam:
            player_move(keys_pressed, player, lightbulb_man)
        draw_window(player, lightbulb_man)

    level_4.main()

if __name__ == "__main__":
    main()