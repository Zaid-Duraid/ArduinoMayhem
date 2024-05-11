from engi1020.arduino.api import *
import pygame
import threading
import time
import random

WIDTH, HEIGHT = 1070, 600
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Arduino Mayhem!")
pygame.font.init()

SPEECH_SIZE = round((40/600)*HEIGHT)
SPEECH_FONT = pygame.font.SysFont('timesnewroman', SPEECH_SIZE)
SPEECH_DELAY = 0.03

FIRST_LINES = {"Hey.. uhh.... I actually need your help with something":'neutral',
              "I've been in a bad mood because.. well..":"neutral",
              "I locked my stuff in a safe....":"neutral",
              "And I have not been able to crack it":"neutral",
               "Would you mind doing that for me?":"neutral",
              "You will need to use your turn dial, watch your LED flashes, and listen to your buzzer":"neutral",}

SECOND_LINES = {"Here's what it should sound like when you're ready to crack the safe. Hold the arduino button to proceed.":"neutral",}

THIRD_LINES = {"Ready? HOLD the arduino button when you think you've got it":"neutral"}

LAST_LINES = {"....                  ":"surprised",
              "I've literally been trying to crack this safe from months":"surprised",
               "Well, thanks for spending some time with me":"happy",
               "I've got to say, this was mostly fun":"neutral",
               "I've given out enough lightbulb moments today":"happy",
               "Have a good one!":"neutral",}



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

can_use_buzzer = False
HUD_IMAGE = "Improved_Circular_Angle_HUD.png"

CODES = (random.randint(0, 360), random.randint(0, 360), random.randint(0, 360))
LED_BUZZER_RATE_RANGE = (1, 15)
BUZZER_FREQ = 858
current_led_buzzer_rate = 0
current_hud_angle = 0
current_hud = 1

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

def rotate_HUD(HUD_surface, angle):
    """Given a pygame surface and an angle, this function returns a pygame surface that looks like
    and is centered at the same position as the surface passed in, but is rotated by a certain angle.
    Due to the way that Pygame treats objects, copies of objects are used during variable assignments."""
    rotated_HUD = pygame.transform.rotate(HUD_surface, angle)
    rotated_rect = HUD_surface.get_rect().copy()
    rotated_rect.center = rotated_HUD.get_rect().center
    rotated_HUD = rotated_HUD.subsurface(rotated_rect).copy()
    return rotated_HUD

def HUD_turner():
    """This is an event function that contains within it three loops. Each loop represents one lock (referred to as HUD in code) in the safe.
     Before each loop, a rectangle and scaled surface is made representing a HUD or a lock. The first HUD is at the left of the screen
     the second HUD is 1/3 of the way to the right of the screen, and the third HUD is 2/3 of the way to the right of the screen. The diameters
     of the HUDs are all the same, which is the global variable HUD_diameter. HUD_diameter is initialized at 1/3 of screen width.

     In each safe-picking loop, the HUD is removed from event_objects, then it is rotated according to a global variable called
     current_hud_angle (manipulated in events_2). After it is rotated, it is appended again to event_objects so that it may be drawn by the
     draw_window function in the main thread (main function).

     Finally, there is a global variable, named current_hud. Based on the value of this global variable, the HUD_turner function will
     progress to the different loops."""
    global event_objects

    HUD_diameter = round(WIDTH/3)

    HUD_1_rectangle = pygame.Rect(0, 45, HUD_diameter, HUD_diameter)
    HUD_1_surface = pygame.image.load(f"Assets\{HUD_IMAGE}")
    HUD_1_scaled_surface = pygame.transform.scale(HUD_1_surface,
                                                  (HUD_diameter, HUD_diameter))

    event_objects.append((HUD_1_rectangle, HUD_1_scaled_surface))

    clock = pygame.time.Clock()
    while current_hud == 1:
        clock.tick(FPS)
        event_objects.remove((HUD_1_rectangle, HUD_1_scaled_surface))
        HUD_1_scaled_surface = rotate_HUD(HUD_1_surface, current_hud_angle)
        HUD_1_scaled_surface = pygame.transform.scale(HUD_1_scaled_surface,
                                                      (HUD_diameter, HUD_diameter))
        event_objects.append((HUD_1_rectangle, HUD_1_scaled_surface))

    HUD_2_rectangle = pygame.Rect(HUD_diameter, 45,
                                  HUD_diameter, HUD_diameter)
    HUD_2_surface = pygame.image.load(f"Assets\{HUD_IMAGE}")
    HUD_2_scaled_surface = pygame.transform.scale(HUD_2_surface,
                                                  (HUD_diameter, HUD_diameter))
    event_objects.append((HUD_2_rectangle, HUD_2_scaled_surface))
    while current_hud == 2:
        clock.tick(FPS)
        event_objects.remove((HUD_2_rectangle, HUD_2_scaled_surface))
        HUD_2_scaled_surface = rotate_HUD(HUD_2_surface, current_hud_angle)
        HUD_2_scaled_surface = pygame.transform.scale(HUD_2_scaled_surface,
                                                      (HUD_diameter, HUD_diameter))
        event_objects.append((HUD_2_rectangle, HUD_2_scaled_surface))

    HUD_3_rectangle = pygame.Rect(HUD_diameter*2, 45,
                                  HUD_diameter, HUD_diameter)
    HUD_3_surface = pygame.image.load(f"Assets\{HUD_IMAGE}")
    HUD_3_scaled_surface = pygame.transform.scale(HUD_3_surface,
                                                  (HUD_diameter, HUD_diameter))
    event_objects.append((HUD_3_rectangle, HUD_3_scaled_surface))
    while current_hud == 3:
        clock.tick(FPS)
        event_objects.remove((HUD_3_rectangle, HUD_3_scaled_surface))
        HUD_3_scaled_surface = rotate_HUD(HUD_3_surface, current_hud_angle)
        HUD_3_scaled_surface = pygame.transform.scale(HUD_3_scaled_surface,
                                                      (HUD_diameter, HUD_diameter))
        event_objects.append((HUD_3_rectangle, HUD_3_scaled_surface))



def event_2():
    """This event first starts a thread that updates the safe-picking locks visual. This thread uses the function hud_turner defined
    above. The following is what happens at each iteration of the loop:

    1. Set the current_code equal to the index of the global variable CODES that corresponds to the current HUD/lock. The global variable
    CODE uses the random module to generate a tuple of size 3 where each element is a random number between 0 and 360. Codes to crack the
    safe are always between 0 and 360.
    2. Set the current_hud_angle global variable to a value between 0 and 360 based on the percentage of the current potentiometer reading
    (read using the engi1020 function called analog_read) of the max potentiometer value. This is used by the HUD_turner function.
    3. Set the percent progress to 1 - ((the absolute value of the difference between the current_code (of the safe we're trying to crack) and
    the current_hud_angle (where the potentiometer is at)) divided by 360)
    4. There is a global variable, defined LED_BUZZER_RATE_RANGE, which is a list containing two numbers (upper & lower range). Use this to define
    the current_led_buzzer_rate as (upper range - round((upper range - lower range)*percent_progess))
    5.Turn on the LED and the buzzer
    6. Wait for the specified current_led_buzzer_rate
    7. Turn off the LED and buzzer
    8. if the current_led_buzzer_rate is equal to the lower range of LED_BUZZER_RATE_RANGE (AKA we are extremely close to the code)
    and the button is not being held haphazardly (the player is not holding the button as they twist the potentiometer) yet the button
    is notetheless held at that moment, increment the current_hud global variable by 1 and restart the loop.
    9.If the current_hud global variable is equal to 4 (we've cracked 3 locks) then break out of the event_2 function completely
    """
    global current_hud, event_objects, current_led_buzzer_rate, current_hud_angle

    hud_thread = threading.Thread(target=HUD_turner, daemon=True)
    hud_thread.start()

    potentiometer_min, potentiometer_max = 0, 1023
    clock = pygame.time.Clock()
    button_may_be_held_haphazardly = True
    while True:
        current_code = CODES[current_hud-1]
        current_hud_angle = round(analog_read(0)*(360/potentiometer_max))
        percent_progess = 1 - (abs(current_code-current_hud_angle)/360)
        current_led_buzzer_rate = LED_BUZZER_RATE_RANGE[1] - round((LED_BUZZER_RATE_RANGE[1]-LED_BUZZER_RATE_RANGE[0])*percent_progess)
        digital_write(4, True)
        buzzer_frequency(5, BUZZER_FREQ)
        clock.tick(current_led_buzzer_rate)
        digital_write(4, False)
        buzzer_stop(5)
        if current_led_buzzer_rate == LED_BUZZER_RATE_RANGE[0] and not button_may_be_held_haphazardly and digital_read(6):
            current_hud += 1
            button_may_be_held_haphazardly = True
            if current_hud == 4:
                break
        elif current_led_buzzer_rate == LED_BUZZER_RATE_RANGE[0] and not digital_read(6):
            button_may_be_held_haphazardly = False
        elif digital_read(6):
            button_may_be_held_haphazardly = True

    time.sleep(1)

    pass


def events():
    """This function is threaded and contains the events of the level in chronological order"""
    #Allow pygame to start
    time.sleep(5)
    global current_text, running, can_use_buzzer

    print_lines(FIRST_LINES, auto_skip_to_event=False)

    ####### EVENT 1
    print_lines(SECOND_LINES, wait_to_skip=True)
    clock = pygame.time.Clock()
    while not digital_read(6):
        digital_write(4, True)
        buzzer_frequency(5, BUZZER_FREQ)
        clock.tick(LED_BUZZER_RATE_RANGE[0])
        digital_write(4, False)
        buzzer_stop(5)
    digital_write(4, False)
    buzzer_stop(5)
    #######

    print_lines(THIRD_LINES, wait_to_skip=True)

    ####### EVENT 2
    event_2()
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

    pygame.quit()

if __name__ == "__main__":
    main()