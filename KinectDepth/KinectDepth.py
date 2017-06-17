import thread
from numpy import random
import numpy as np
from pykinect import nui
import pathFinder
import gui
import time
import rpyc
from rpyc.utils.server import ThreadedServer
import pygame
import map

class MOVEMENT:
    VORWAERTS = 0
    VOR_DIAG_RECHTS = 1 
    VOR_DIAG_LINKS = 2
    LINKS = 3 
    RECHTS = 4
    RUECKWAERTS = 5 
    RUECK_DIAG_RECHTS = 6 
    RUECK_DIAG_LINKS = 7
    DREHEN_LINKS = 8 
    DREHEN_RECHTS = 9



screen_lock = thread.allocate()
screen = None

WHITE = (255,255,255)
BLUE = (0,0,255)
BLACK = (0,0,0)
RED = (255,0,0)
BRIGHTRED = (255,100,100)
BRIGHTGREEN = (100,255,100)

iteration = 0
source = (320,0)
#sourceCell = [x / 2 for x in source]
target = (300,350)
#targetCell = [x / 2 for x in target]
maxDist = 300   # after 3 m the floor starts to show
#lastMessage = None
TIMEOUT=500
orientation = 0.0
arduinoStatus = 0

##################################################
# solves issue with blocking threads in pygame
# needs to be called repeateadly from main thread
def continue_pygame_loop():
    pygame.mainloop(0.1)
    yield
##################################################   



class MsgReaderService(rpyc.Service):

    def exposed_echo(self, text):
        return text + " from KinectDepth"

    def exposed_navigateTo(self, pos):
        global target
        target = pos
        analyze()
        return "path evaluated"

    def exposed_rotate(self, angle):
        gui.rotateCart(angle)

    def exposed_move(self, direction, speed):
        arduino.sendMoveCommand(direction, speed)

    def exposed_stop(self):
        gui.stopCart()

    def exposed_getCartOrientation(self):
        arduino.getCartOrientation()
        arduino.readMessages()
        lastMessage = int(round(time.time() * 1000))
        orientation = arduino.getOrientation()
        #print "orientation in getCartOrientation: " + str(orientation)
        return str(orientation)

    def exposed_heartBeat(self):
        global lastMessage
        continue_pygame_loop()

        currTime = int(round(time.time() * 1000))
        print currTime-lastMessage
        if currTime - lastMessage > TIMEOUT:
            arduino.sendStopCommand()
        else:
            arduino.sendHeartbeat()
            print("arduino Heartbeat sent")

        lastMessage = int(round(time.time() * 1000))




def analyze(target):

    global screen

    obstacleList = []
    depth = np.load("depth.npy")
    for row in range(screen.get_height()):
        for col in range(screen.get_width()):
            dist = depth[col, row] / 10
            if  dist > 80 and dist < 300:
                screen.set_at((col, dist), WHITE)
                obstacleList.append((col, dist))

    map.update()
    map.save("topViewFiltered.png")

    # extend path blocking pixels to obstacles based on cart size
    for o in obstacleList:
        map.circle(RED, o, 40)
    
    # show source
    map.circle(RED, source, 10)

    # show target (fixed target at the moment)
    map.circle(BLUE, target, 10)
    map.save("topViewEnlarged.png")

    pathFinder.findPath(screen, source, target, 8)

    pygame.display.update()
    
    print "analyze done"

# -------------------------------------------
# wird fuer jedes empfangene Frame aufgerufen
# -------------------------------------------
def depth_frame_ready(frame):
    global iteration
    tmp_s = pygame.Surface(DEPTH_WINSIZE, 0, 16)
    iteration += 1
    if iteration == 1:    
        with screen_lock:
            frame.image.copy_bits(tmp_s._pixels_address)
            arr2d = (pygame.surfarray.pixels2d(tmp_s) >> 7) & 255
            depth = (pygame.surfarray.pixels2d(tmp_s) >> 3) & 4095
            np.save("depth", depth) # get it back with np.load("depth")
            pygame.image.save(tmp_s, "depth.png")
            pygame.surfarray.blit_array(screen, arr2d)
            pygame.display.update()

    arduino.sendHeartbeat();

def getDepthImage():
    """take a depth picture"""
    pygame.init()

    # Initialize PyGame
    global screen
    screen = pygame.display.set_mode(DEPTH_WINSIZE, 0, 8)
    screen.set_palette(tuple([(i, i, i) for i in range(256)]))
    pygame.display.set_caption('PyKinect Depth Map Example')
     
    with nui.Runtime() as kinect:
        kinect.depth_frame_ready += depth_frame_ready   # fuegt dem EventHandler den Aufruf von depth_frame_ready(frame) hinzu
        kinect.depth_stream.open(nui.ImageStreamType.Depth, 2, nui.ImageResolution.Resolution640x480, nui.ImageType.Depth)

        # Main game loop
        while True:
            event = pygame.event.wait()

            if event.type == pygame.QUIT:
                break

if __name__ == '__main__':
    
    # ask for user input to change run mode
    print '1 - get single depth frame'
    print '2 - analyze depht frame'
    print '3 - check serial comm to MotorizedBase'
    print '4 - process commands'
    print '5 - rotate left'
    print '6 - rotate right'
    print '7 - dialog'

    #var = raw_input('option: ')
    var = '7'

    if var=='1':
        getDepthImage()

    if var=='2':
        #arduino.initSerial("COM5")
        analyze()

    if var=='3':
        arduino.initSerial("COM5")
        sendHeartBeat = True

        time.sleep(8)
        for i in range(1):

            arduino.sendStopCommand()
            time.sleep(1)
            arduino.readMessages()

            arduino.getCartOrientation()
            time.sleep(1)
            arduino.readMessages()

            arduino.sendRotateCommand(15)
            time.sleep(0.5)
            arduino.readMessages()

            arduino.sendRotateCommand(-14)
            time.sleep(0.5)
            arduino.readMessages()

        

    if var=='4':

        arduino.initSerial("COM5")
        print("startMsgReader")
        
        lastMessage = int(round(time.time() * 1000))

        server = ThreadedServer(MsgReaderService, port = 18812)
        server.start()

    if var=='5':

        arduino.initSerial("COM5")
        print("send rotate command")
        arduino.sendRotateCommand(10)
        for i in range(20):
            arduino.readMessages()
            arduino.sendHeartbeat()
            time.sleep(0.3)

    if var=='6':

        arduino.initSerial("COM5")
        print("send rotate command")
        arduino.sendRotateCommand(-10)
        for i in range(20):
            arduino.readMessages()
            arduino.sendHeartbeat()
            time.sleep(0.3)

    if var=='7':

        map.createWindow()

        gui.startGui()
