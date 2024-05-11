from engi1020.arduino.api import *
import pygame
import threading
import time
import random
import math
import level_6

WIDTH, HEIGHT = 1070, 600
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Arduino Mayhem!")
pygame.font.init()

SPEECH_SIZE = round((40/600)*HEIGHT)
SPEECH_FONT = pygame.font.SysFont('timesnewroman', SPEECH_SIZE)
SPEECH_DELAY = 0.03


REQUIRED_COLLECTABLES = 16 #This should be defined lower down, but I am defining it here to be used in the lines

FIRST_LINES = {"JEFFEERRRYY!":'angry',
              "COME HERE!":"angry",}

SECOND_LINES = {"(breathes heavily)": "surprised",
                "I'm sorry": "surprised",
                "Sometimes.... my nerves get the better of me": "surprised",
                "Why don't you just go ahead and give Jeffery a hug": "happy"}

THIRD_LINES = {"HAHAHAHA": "happy",
                "Jeffery got you good!": "neutral",
                "Nothing will ever make him let got of you!": "neutral",
                "Unless you shake your arduino, activating the 3D axis accelerometer": "neutral"}

FOURTH_LINES = {".....": "surprised",
                "Sometimes I talk too much": "neutral",}

FIFTH_LINES = {"Haha! You shook Jeffery off!": "neutral",
               "But that was only a test!": "neutral",
               "Let's see how well you fare with all his friends at once!": "angry",
               f"Try to collect {REQUIRED_COLLECTABLES} little lightbulbs while being chased!": "happy",
               "If you get caught, you'll have to start over!": "neutral",
               "It was nice playing with you!": "neutral"}

SIXTH_LINES = {"WHATDIDWHATHOWPPFFFTTT":"terrified",
               "IS THIS HOW WE'RE GOING TO PLAY?":"angry",
               "DO YOU REALLY WANT TO DO THIS?!":"angry",
               "MY GOONS! ATTACK!":"angry"}

SEVENTH_LINES = {"I will literally make it impossible for you to win":"terrified",
                 "There will be NOTHING for you to do other than struggle for eternity":"angry",
                "I..... Will....":"angry",
               "DESTROY YOU!!":"furious"}

LAST_LINES = {".....                                    ":"furious",
              "......                                   ":"angry",
               ".....                                   ":"surprised",
               "Ugh... I'm sorry":"surprised",
               "I just... It's hard to let go of your ego sometimes.":"surprised",
              "Don't worry... I'll make it up to you": "neutral",
               "LEVEL 6!!!!":"neutral"}



current_text = ''

PLAYER_WIDTH, PLAYER_HEIGHT = round((25/854)*WIDTH), round((25/480)*HEIGHT)
LIGHTBULB_WIDTH, LIGHTBULB_HEIGHT = round((100/854)*WIDTH), round((120/480)*HEIGHT)

LIGHTBULB_MAN_SPRITES = {"neutral":"lightbulb_man_neutral.png",
                         "happy":"lightbulb_man_happy.png",
                         "surprised":"lightbulb_man_surprised.png",
                         "terrified":"lightbulb_man_terrified.png",
                         "angry":"lightbulb_man_angry.png",
                         "transparent":"lightbulb_man_transparent.png",
                         "furious":"lightbulb_man_furious.png"}
CURRENT_LIGHTBULB_MAN_STATE = None

ENEMY_SPRITES = ("enemy_1.png", "enemy_2.png", "enemy_3.png")
ENEMY_WIDTH, ENEMY_HEIGHT = round((50/854)*WIDTH), round((50/480)*HEIGHT)
COLLECTABLES_SPRITES = ('collectable_1.png', "collectable_2.png", "collectable_3.png")
COLLECTABLE_WIDTH, COLLECTABLE_HEIGHT = round((15/854)*WIDTH), round((25/480)*HEIGHT)
REQUIRED_STRUGGLE = 35
NUMBER_OF_ENEMIES = 3

solid_objects = []
event_objects = []
event_rectangles = []
mouse_event_data = (False, 0) #The first value corresponds to mouse being pressed and the second is mouse pos
text_typed = ''

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)

running = True
player_roam = True
FPS = 60

VEL = round((8/600)*WIDTH)
ENEMY_VEL = round((1/480)*WIDTH)

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
        if not player.colliderect(object):
            continue
        elif solid_object.colliderect(theoretical_object):
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
    solid_objects.remove(player)
    if (keys_pressed[pygame.K_LEFT] or keys_pressed[pygame.K_a]) and player.x - VEL > 0 and not will_collide(player, "sideways", -VEL):  # LEFT
        player.x -= VEL
    if (keys_pressed[pygame.K_RIGHT] or keys_pressed[pygame.K_d]) and (player.x + VEL + PLAYER_WIDTH < WIDTH) and not will_collide(player, "sideways", VEL):  # RIGHT
        player.x += VEL
    if (keys_pressed[pygame.K_UP] or keys_pressed[pygame.K_w]) and player.y - VEL > SPEECH_SIZE and not will_collide(player, "up_down", -VEL):  # UP
        player.y -= VEL
    if (keys_pressed[pygame.K_DOWN] or keys_pressed[pygame.K_s]) and player.y + VEL + PLAYER_HEIGHT < HEIGHT and not will_collide(player, "up_down", VEL):  # DOWN
        player.y += VEL
    solid_objects.append(player)

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

class Enemy():
    def __init__(self, initial_pos):
        """Updates the global iterables solid_objects and event_objects with the enemy rectangle and sprites and gives the enemy a velocity
        deviation so that he does not move at the same speed as other enemies. The __init__ method also initializes enemy attributes such as
        self.flipped and self.latched."""
        global solid_objects, event_objects

        self.rectangle = pygame.Rect(initial_pos[0], initial_pos[1], ENEMY_WIDTH, ENEMY_HEIGHT)
        self.sprite = random.choice(ENEMY_SPRITES)
        self.surface = pygame.image.load(f"Assets\{random.choice(ENEMY_SPRITES)}")
        self.scaled_surface = pygame.transform.scale(self.surface,
                                                      (round(1.25*ENEMY_WIDTH),round(1.25*ENEMY_HEIGHT)))
        self.flipped = False
        self.latched = False

        self.vel_deviation = random.uniform(0.5, 1)

        solid_objects.append(self.rectangle)
        event_objects.append((self.rectangle ,self.scaled_surface))

    def move(self, direction, vel):
        """Given a direction and a velocity, the enemy removes itself from the solid_objects and events_objects global iterables
        then proceeds to update it's current x or y position based on the velocity and direction given. If the enemy is moving left, it
        will face the left by setting self.flipped to True. After applying the velocity in the desired direction, the enemy adds itself
        again to the event_objects and solid_objects global iterables.

        If the enemy finds that it has collided with the player, it sets the attribute self.latched equal to True. This is used in the
        event loops to check if an enemy is colliding with a player and accordingly calls the method initiate_grab_sequence on that enemy.

        Note that when two enemies are exactly atop each other (same exact location) this can cause an error in the following lines:
        solid_objects.remove(self.rectangle)
        event_objects.remove((self.rectangle, self.scaled_surface))
        Where it says that we are attempting to remove an element from solid objects that doesn't exist there

        This error would have required a complicated rework of the datatypes contained in solid_objects (currently only pygame rectangle objects).
        However, it seems to have been fixed in a try-except loop, where duplicate objects in solid_objects are removed.
        The reason why this fixed it is honestly not known, but no errors or problems were further encountered when testing
        the level so this solution stayed how it was."""
        try:
            solid_objects.remove(self.rectangle)
            event_objects.remove((self.rectangle, self.scaled_surface))
        except:
            for solid_object in solid_objects:
                if solid_objects.count(solid_object) >= 2:
                    solid_objects.remove(solid_object)
            event_objects.remove((self.rectangle, self.scaled_surface))


        if direction == "up_down" and not will_collide(self.rectangle, "up_down", vel):
            self.rectangle.y += round(vel*self.vel_deviation) + random.randint(-1,1)
        elif direction == "up_down" and will_collide(self.rectangle, "up_down", vel):
            self.latched = True


        if direction == "sideways" and not will_collide(self.rectangle, "sideways", vel):
            if vel > 0 and self.flipped == True:
                self.scaled_surface = pygame.transform.flip(self.scaled_surface, True, False)
                self.flipped = False
            elif vel < 0 and self.flipped == False:
                self.scaled_surface = pygame.transform.flip(self.scaled_surface, True, False)
                self.flipped = True
            self.rectangle.x += round(vel*self.vel_deviation) + random.randint(-1,1)
        elif direction == "sideways" and will_collide(self.rectangle, "sideways", vel):
            self.latched = True


        solid_objects.append(self.rectangle)
        event_objects.append((self.rectangle, self.scaled_surface))

    def chase_player(self):
        """Based on the difference between the player and the enemy in the x and y, this function uses the math module to calculate
        the angle of a vector that points from the enemy to the player. Then, using this angle, it uses the self.move() method defined
        in the enemy class to move the enemy along this vector in the x and y, such that the magnitude of the overall velocity vector
        is equal to the global variable ENEMY_VEL"""
        delta_y = player.y-self.rectangle.y
        delta_x = player.x-self.rectangle.x
        theta = math.atan2(delta_y, delta_x)

        self.move('up_down', round(ENEMY_VEL*math.sin(theta)))
        self.move('sideways', round(ENEMY_VEL * math.cos(theta)))

    def initiate_grab_sequence(self):
        """This method uses the arduino's 3-Axis Accelerometer and also creates a progress bar. When this method is called,
        a while loop starts in the event thread (main thread runs undisturbed) that checks if the total amount that the player has
        shaken the arduino in the x,y, and z (stored in total_struggle) is equal to the global variable REQUIRED_STRUGGLE. The progress
        bar is updated based on what the total_struggle is of the REQUIRED_STRUGGLE. If the total_struggle equals REQUIRED_STRUGGLE, the
        loop is broken."""
        global event_rectangles, solid_objects, player, struggle_data_list_x, struggle_data_list_y, struggle_data_list_z

        clock = pygame.time.Clock()


        if player.y >= HEIGHT/2:
            progress_bar_x_pos = 0
            progress_bar_y_pos = 45
        else:
            progress_bar_x_pos = round(WIDTH / 2)
            progress_bar_y_pos = round((9 / 10) * HEIGHT)

        progress_bar_background = pygame.Rect(progress_bar_x_pos, progress_bar_y_pos, round(WIDTH / 2),
                                              round((1 / 10) * HEIGHT))
        event_rectangles.append([progress_bar_background, WHITE])
        solid_objects.append(progress_bar_background)

        progress_bar_rect = pygame.Rect(progress_bar_x_pos, progress_bar_y_pos, round(WIDTH / 2),
                                        round((1 / 10) * HEIGHT))
        event_rectangles.append([progress_bar_rect, GREEN])
        total_struggle = 0
        while True:
            clock.tick(FPS)
            accelerometer_data_x, accelerometer_data_y, accelerometer_data_z = three_axis_get_accelX(), three_axis_get_accelY(), three_axis_get_accelZ()
            if abs(accelerometer_data_x) > 0.35:
                total_struggle += abs(accelerometer_data_x) - 0.35
            if abs(accelerometer_data_y) > 0.35:
                total_struggle += abs(accelerometer_data_y) - 0.35
            if abs(accelerometer_data_z-1) > 0.35:
                total_struggle += abs(accelerometer_data_z-1) - 0.35
            event_rectangles.remove([progress_bar_rect, GREEN])
            progress_bar_rect = pygame.Rect(progress_bar_x_pos, progress_bar_y_pos,
                                            round((WIDTH / 2) * (total_struggle / REQUIRED_STRUGGLE)),
                                            round((1 / 10) * HEIGHT))
            event_rectangles.append([progress_bar_rect, GREEN])
            if total_struggle > REQUIRED_STRUGGLE:
                break

        event_rectangles = []
        solid_objects.remove(progress_bar_background)
        player.x = round(WIDTH/2)
        player.y = round(HEIGHT/2)

    def __del__(self):
        """When an enemy object is deleted, it removes itself from the global iterables solid_objects and event_objects"""
        if self.rectangle in solid_objects:
            solid_objects.remove(self.rectangle)
        if (self.rectangle, self.scaled_surface) in event_objects:
            event_objects.remove((self.rectangle, self.scaled_surface))

class Collectable():

    def __init__(self, initial_pos):
        """Updates the global iterable event_objects with the collectable rectangle and sprites and gives the collectable one of three sprites
                    randomly. The __init__ method also initializes collectable attributes such as self.collected"""
        global event_objects

        self.rectangle = pygame.Rect(initial_pos[0], initial_pos[1], COLLECTABLE_WIDTH, COLLECTABLE_HEIGHT)
        self.sprite = random.choice(ENEMY_SPRITES)
        self.surface = pygame.image.load(f"Assets\{random.choice(COLLECTABLES_SPRITES)}")
        self.scaled_surface = pygame.transform.scale(self.surface,
                                                      (round(1.25*COLLECTABLE_WIDTH),round(1.25*COLLECTABLE_HEIGHT)))
        self.collected = False

        event_objects.append((self.rectangle ,self.scaled_surface))

    def check_for_player_collision(self):
        """Returns True if the collectable is colliding with the player (player is a global object)"""
        if self.rectangle.colliderect(player):
            self.collected = True

    def __del__(self):
        """When a collectable object is deleted, it removes itself from the global iterable event_objects"""
        if (self.rectangle, self.scaled_surface) in event_objects:
            event_objects.remove((self.rectangle, self.scaled_surface))


def swarm_event(number_of_enemies = NUMBER_OF_ENEMIES, required_collectables = REQUIRED_COLLECTABLES):
    """Given a number of enemies and a number of required collectables (equal to global variabels NUMBER_OF_ENEMIES and REQUIRED_COLLECTABLES
    by default), this function uses the Enemy class, Collectable class, and the random module to swarm the player in a dramatic event.

    When this function is called, an inner nested function called initiate_enemy_swarm spawns the enemies at a random location off-screen
    and spawns the collectables at a random location on-screen. Then, this function goes into a while loop that updates at a rate equal to
    the global variable FPS. The global variable current_text, which is used by draw windows (a function that operates in the main thread
    independent of this one) to update the text at the top of the screen, is updates with the player's progress in the swarm_event function.
    At every frame in the loop, the following happens:

    1.Call chase_player() on each enemy
    2.IF any enemy has collided with the player. If this is the case call initiate_grab_sequence on the enemy that got hold of the player.
    Also, set the global variable player_roam to False such that, in the main() function, the player_move() function is not called.
    Once the player has shaken the arduino to get rid of the enemy, the whole event loop resets and the function initiate_enemy_swarm is called
    again. Also, the player's score is reset and player_road is set to True.
    3.Check if any collectable is colliding with the player. If this is the case, delete that corresponding collectable and increase
    the varible number_of_collected_collectables by 1. Also, update the global variable current_text to show this progress.
    4.IF number_of_collected_collectables reaches the required_collectables, break out of the
    function, as the player has won."""
    global player_roam, current_text

    current_text = f"Collected 0/{required_collectables}"

    def initiate_enemy_swarm():
        """This is a nested function that is defined only in the scope of its outer function. When called, this function
        will initiate enemies at random locations off-screen and collectables at random locations on-screen. Once done, this
        function returns a tuple that contains a list of the enemies and a list of the collectables to be used in the outer function's
        while loop"""
        enemies_list = []
        collectables_list = []
        while len(enemies_list) < number_of_enemies:
            spawn_location_x = random.choice([i for i in range(-ENEMY_WIDTH*3, WIDTH+(ENEMY_WIDTH*3)) if (i not in range(0, WIDTH))])
            spawn_location_y = random.choice([i for i in range(LIGHTBULB_HEIGHT+50, HEIGHT+ENEMY_HEIGHT)])

            enemy = Enemy((spawn_location_x, spawn_location_y))
            for solid_object in solid_objects:
                if enemy.rectangle.colliderect(solid_object) and enemy.rectangle != solid_object:
                    solid_objects.remove(enemy.rectangle)
                    del enemy
                    break

            try:
                enemies_list += [enemy]
            except UnboundLocalError:
                continue

        while len(collectables_list) < required_collectables:
            spawn_location_x = random.choice([i for i in range(0, WIDTH-COLLECTABLE_WIDTH)])
            spawn_location_y = random.choice([i for i in range(LIGHTBULB_HEIGHT, HEIGHT-COLLECTABLE_HEIGHT)])
            collectable = Collectable((spawn_location_x, spawn_location_y))

            for solid_object in solid_objects: #if the collectable spawns on an solid object, delete it and try again
                if collectable.rectangle.colliderect(solid_object):
                    del collectable
                    break
            else:
                collectables_list += [collectable]

        return enemies_list, collectables_list

    enemies, collectables = initiate_enemy_swarm()

    clock = pygame.time.Clock()
    number_of_collected_collectables = 0
    while True:
        clock.tick(FPS)

        for enemy in enemies:
            enemy.chase_player()
            if enemy.latched == True:
                player_roam = False
                enemy.initiate_grab_sequence()
                player_roam = True
                del enemy
                for instance in enemies:
                    del instance
                number_of_collected_collectables = 0
                current_text = f"Collected: {number_of_collected_collectables}/{required_collectables}"
                for collectable in collectables:
                    del collectable
                enemies, collectables = initiate_enemy_swarm()
                break

        for collectable in collectables:
            collectable.check_for_player_collision()
            if collectable.collected == True:
                number_of_collected_collectables += 1
                current_text = f"Collected: {number_of_collected_collectables}/{required_collectables}"
                collectables.remove(collectable)
                del collectable
        if number_of_collected_collectables >= required_collectables:
            break

def mega_swarm_event():
    """This function is almost identical to swarm_event, but has a few differences.

    No number_of_enemies or number_of_required_collectables need to be passed in. This function will always spawn 25 enemies and 100
    collectables (huge number)

    Just like swarm_event, mega_swarm_event returns once the player collected all collectables. However, this is extremely difficult if
    not impossible, as stated by the lightbulb_man in the global dictionary SEVENTH_LINES. Instead, whenever the player is caught by an
    enemy, the variable times_latched increases by 1. If the player has been latched and has escaped twice, the loop breaks. This is not
    meant to frustrate the player, instead it is meant to show the lightbulb_man's anger."""
    global player_roam, current_text, ENEMY_VEL, player

    player.x = round(WIDTH / 2)
    player.y = round(HEIGHT / 2)
    ENEMY_VEL = VEL

    current_text = f"Collected 0/{100}"

    def initiate_enemy_swarm():
        """This is a nested function that is defined only in the scope of its outer function. When called, this function
                will initiate enemies at random locations off-screen and collectables at random locations on-screen. Once done, this
                function returns a tuple that contains a list of the enemies and a list of the collectables to be used in the outer function's
                while loop"""
        enemies_list = []
        collectables_list = []
        while len(enemies_list) < 25:
            spawn_location_x = random.choice(
                [i for i in range(-ENEMY_WIDTH * 3, WIDTH + (ENEMY_WIDTH * 3)) if (i not in range(0, WIDTH))])
            spawn_location_y = random.choice([i for i in range(LIGHTBULB_HEIGHT + 50, HEIGHT + ENEMY_HEIGHT)])

            enemy = Enemy((spawn_location_x, spawn_location_y))
            for solid_object in solid_objects:
                if enemy.rectangle.colliderect(solid_object) and enemy.rectangle != solid_object:
                    solid_objects.remove(enemy.rectangle)
                    del enemy
                    break

            try:
                enemies_list += [enemy]
            except UnboundLocalError:
                continue

        while len(collectables_list) < 100:
            spawn_location_x = random.choice([i for i in range(0, WIDTH - COLLECTABLE_WIDTH)])
            spawn_location_y = random.choice([i for i in range(LIGHTBULB_HEIGHT, HEIGHT - COLLECTABLE_HEIGHT)])
            collectable = Collectable((spawn_location_x, spawn_location_y))

            for solid_object in solid_objects:  # if the collectable spawns on an solid object, delete it and try again
                if collectable.rectangle.colliderect(solid_object):
                    del collectable
                    break
            else:
                collectables_list += [collectable]

        return enemies_list, collectables_list

    enemies, collectables = initiate_enemy_swarm()

    clock = pygame.time.Clock()
    number_of_collected_collectables = 0
    times_latched = 0
    while True:
        clock.tick(FPS)

        for enemy in enemies:
            enemy.chase_player()
            if enemy.latched == True:
                player_roam = False
                times_latched += 1
                enemy.initiate_grab_sequence()
                player_roam = True
                del enemy
                for instance in enemies:
                    del instance
                number_of_collected_collectables = 0
                current_text = f"Collected: {number_of_collected_collectables}/{100}"
                for collectable in collectables:
                    del collectable
                enemies, collectables = initiate_enemy_swarm()
                break

        for collectable in collectables:
            collectable.check_for_player_collision()
            if collectable.collected == True:
                number_of_collected_collectables += 1
                current_text = f"Collected: {number_of_collected_collectables}/{100}"
                collectables.remove(collectable)
                del collectable
        if number_of_collected_collectables >= 100:
            break
        if times_latched == 2:
            break


def events():
    """This function is threaded and contains the events of the level in chronological order"""
    #Allow pygame to start
    time.sleep(5)
    global current_text, running, player_roam, player, event_rectangles, event_objects

    player_roam = False
    player.x = 200
    player.y = 200


    print_lines(FIRST_LINES, wait_to_skip= True)

    clock = pygame.time.Clock()

    jeffery = Enemy((WIDTH, 200)) #You may view jeffery as a demo of how object-oriented programming is used in this level
    ####### EVENT 1
    while True:
        clock.tick(FPS)
        jeffery.move('sideways', -ENEMY_VEL)
        if jeffery.rectangle.x < (3/4)*WIDTH:
            break


    print_lines(SECOND_LINES, wait_to_skip=True)
    set_lightbulbman_state("neutral")

    player_roam = True
    while True:
        clock.tick(FPS)
        jeffery.chase_player()
        if jeffery.latched == True:
            player_roam = False
            print_lines(THIRD_LINES,wait_to_skip=True)
            print_lines(FOURTH_LINES)
            jeffery.initiate_grab_sequence()
            player_roam = True
            del jeffery
            break
    #######

    print_lines(FIFTH_LINES, wait_to_skip=True)

    ####### EVENT 2
    swarm_event()
    #######

    print_lines(SIXTH_LINES, wait_to_skip=True)

    ####### EVENT 3
    swarm_event(number_of_enemies=round(NUMBER_OF_ENEMIES*1.3), required_collectables=round(REQUIRED_COLLECTABLES*1.5))
    #######

    print_lines(SEVENTH_LINES, wait_to_skip=True)

    ######## EVENT 4
    mega_swarm_event()
    ########

    print_lines(LAST_LINES, wait_to_skip=True)

    time.sleep(3)
    running = False

def main():
    """Starts the thread and initializes objects, then handles the main game loop."""
    events_thread = threading.Thread(target=events, daemon=True)
    events_thread.start()

    global player, mouse_event_data, text_typed
    player = pygame.Rect(200, 200, PLAYER_WIDTH, PLAYER_HEIGHT)
    solid_objects.append(player)
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

    level_6.main()

if __name__ == "__main__":
    main()