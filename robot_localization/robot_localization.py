# robot localization with Python and Particle Filters
# influenced by coursera course
# baldwibr

import numpy as np
import cv2

map = cv2.imread("map.png",0)
HEIGHT, WIDTH = map.shape

rx,ry,rtheta = (WIDTH/4, HEIGHT/4, 0)

STEP = 5 # number of pixels to move
TURN = np.radians(25) # how far to turn each time

# read keyboard input
def get_input():
    fwd = 0 # initialize fwd
    turn = 0 # initialize turn
    halt = False # initialize halt
    k = cv2.waitKeyEx(0)
    if k == 2490368: #windows "up" arrow
        fwd = STEP
    elif k == 2555904: #windows "right" arrow
        turn = TURN
    elif k == 2424832: #windows "lef" arrow
        turn = -TURN
    else: # any other key will halt the program
        halt = True
    return fwd, turn, halt

# robots in real life aren't always perfect in movement
# because of terrain, a robot may turn more or less than intended
# to simulate this, I will add Gaussian noise to our commands
SIGMA_STEP = 0.5 # initialize step noise
SIGMA_TURN = np.radians(5) # intialize turn noise

# moving the robot
def move_robot(rx, ry, rtheta, fwd, turn):
    fwd_noisy = np.random.normal(fwd, SIGMA_STEP, 1)
    rx += fwd_noisy * np.cos(rtheta)
    ry += fwd_noisy * np.sin(rtheta)
    #print("fwd_noisy=", fwd_noisy)
    
    turn_noisy = np.random.normal(turn, SIGMA_TURN, 1)
    rtheta += turn_noisy
    #print("turn_noisy=", np.degrees(turn_noisy))
    
    return rx, ry, rtheta

# sets the number of particles
NUM_PARTICLES = 3000

# initialize the particle positions
def init():
    particles = np.random.rand(NUM_PARTICLES, 3)
    particles *= np.array( (WIDTH, HEIGHT, np.radians(360)))
    return particles

# move the particles with each movement of the robot
def move_particles(particles, fwd, turn):
    particles[:,0] += fwd * np.cos(particles[:,2])
    particles[:,1] += fwd * np.sin(particles[:,2])
    particles[:,2] += turn
    
    particles[:,0] = np.clip(particles[:,0], 0.0, WIDTH-1)
    particles[:,1] = np.clip(particles[:,1], 0.0, HEIGHT-1
                            )
    return particles

# initialize the simulated noise in the robot sensors
SIGMA_SENSOR = 2

# sense the altitude of the position of the robot on the map
def sense(x, y, noisy=False):
    x = int(x)
    y = int(y)
    if noisy:
        return np.random.normal(map[y,x], SIGMA_SENSOR, 1)
    return map[y,x]

# read the altitude from the sensor with noise
# then weight the particles to how close they
# are to the robot's sensed altititude
def compute_weights(particles, robot_sensor):    
    errors = np.zeros(NUM_PARTICLES)
    for i in range(NUM_PARTICLES):
        elevation = sense(particles[i,0],particles[i,1], noisy=False)
        errors[i] = abs(robot_sensor - elevation)
    weights = np.max(errors) - errors
 # keeps particles on the map   
    weights[
        (particles[:,0] == 0) |
        (particles[:,0] == WIDTH - 1) |
        (particles[:,1] == 0) |
        (particles[:,1] == HEIGHT-1)
    ] = 0.0
    
    weights = weights ** 3
    return weights

# resample the particles using the new weight values
def resample(particles, weights):
    probabilities = weights / np.sum(weights)
    new_index = np.random.choice(
        NUM_PARTICLES,
        size = NUM_PARTICLES,
        p = probabilities
    )
    particles = particles[new_index,:]
    return particles

# initialize the particle movement steps
SIGMA_POS = 2
SIGMA_TURN = np.radians(10)

# adds the noise to the particles positions
def add_noise(particles):
    noise = np.concatenate(
        (
            np.random.normal(0, SIGMA_POS, (NUM_PARTICLES, 1)),
            np.random.normal(0, SIGMA_POS, (NUM_PARTICLES, 1)),
            np.random.normal(0, SIGMA_TURN, (NUM_PARTICLES, 1)),
        ),
        axis=1
    )
    particles += noise
    return particles

# builds the display of robot and particle positions
def display(map, rx, ry, particles):
    lmap = cv2.cvtColor(map, cv2.COLOR_GRAY2BGR)
    
    # display particles
    if len(particles) > 0:
        for i in range(NUM_PARTICLES):
            cv2.circle(lmap, 
                       (int(particles[i,0]), int(particles[i,1])), 
                       1, 
                       (255,0,0), 
                       1)
        
    # display robot
    cv2.circle(lmap, (int(rx), int(ry)), 5, (0,255,0), 10)

    # display best guess
    if len(particles) > 0:
        px = np.mean(particles[:,0])
        py = np.mean(particles[:,1])
        cv2.circle(lmap, (int(px), int(py)), 5, (0,0,255), 5)

    cv2.imshow('map', lmap)

# initializing particles
particles = init()

# runs the program continuously until a non-arrow
# button is pressed
while True:
    display(map, rx, ry, particles)
    fwd, turn, halt = get_input()
    if halt:
        break
    rx, ry, rtheta = move_robot(rx, ry, rtheta, fwd, turn)
    particles = move_particles(particles, fwd, turn)
    if fwd != 0:
        robot_sensor = sense(rx, ry, noisy=True)        
        weights = compute_weights(particles, robot_sensor)
        particles = resample(particles, weights)
        particles = add_noise(particles)

# closes the program
cv2.destroyAllWindows()    