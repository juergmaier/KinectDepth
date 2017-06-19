import os
import pygame
import KinectDepth

width = 640
height = 480
DEPTH_WINSIZE = width, height

##################################################
# solves issue with blocking threads in pygame
# needs to be called repeateadly from main thread
def continue_pygame_loop():
    pygame.mainloop(0.1)
    yield
##################################################   

def update():
    pygame.display.update()
    #continue_pygame_loop()

def circle(color, pos, size):
    pygame.draw.circle(KinectDepth.screen, color, pos, size, 0)

def line(color, p1, p2, width):
    pygame.draw.line(KinectDepth.screen, color, p1, p2, width)

def save(file):
    pygame.image.save(KinectDepth.screen, file)


def createWindow():

    os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (410,180)

    # Initialize PyGame
    print "create map window"

    KinectDepth.screen = pygame.display.set_mode(DEPTH_WINSIZE)
    if KinectDepth.showMap:
        pygame.display.set_caption('Kinect Depth Map')
        pygame.image.load("depth.png")
        pygame.display.update()

    
