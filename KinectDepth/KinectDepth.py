import threading
import numpy as np
from pykinect import nui
import pathFinder
import gui
import time
import rpyc
from rpyc.utils.server import ThreadedServer
import pygame
import map



screen_lock = None
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
floorDist = 280   # after 2.8 m the floor starts to show
#lastMessage = None
TIMEOUT=500
orientation = 0.0
arduinoStatus = 0
showMap = False

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

    obstacleList = []       # points of obstacles
    depth = np.load("depth.npy")
    depth = depth.astype(float)

    start = time.time()
    # ignore objects closer 80 cm (not reliable)
    depth[depth < 800.0] = np.NaN
    depth[depth > 2800.0] = np.NaN
    # improved version could ignore the floor. 
    # cam is at 1150mm height and has a downview angle of 14 degrees
    # for depth values > 2800 ignore rows > 480 - (depth - 2800) * sin(14)/sin(76) * 0.2
    # ignore this for the moment as calculations on single values are too slow

    # for each column the closest point
    obstacles  = np.nanmin(depth, axis=1)
    for index, i in enumerate(obstacles):
        if not np.isnan(i):
            screen.set_at((index, int(i)/10), WHITE)

    if showMap:
        print("map topViewFiltered")
        map.update()
        map.save("topViewFiltered.png")
    print("obstacle points: ", time.time()-start, "seconds")

    # extend path blocking pixels to obstacles based on cart size
    start = time.time()
    for index, i in enumerate(obstacles):
        if not np.isnan(i):
            map.circle(RED, (index, int(i)/10), 40)
    print("enlarged points: ", time.time()-start, "seconds")

    if showMap:    
        # show source
        map.circle(RED, source, 10)

        # show target (fixed target at the moment)
        map.circle(BLUE, target, 10)
        print "map topViewEnlarged"
        map.update()
        map.save("topViewEnlarged.png")

    start = time.time()
    pathFinder.findPath(screen, source, target, 8)
    print "pathFinder: ", time.time()-start, "seconds"

    if showMap:
        map.update()
    
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
    screen.set_palette(tuple([(i, i, i) for i in np.nditer(255)]))
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
        for i in np.nditer(20):
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

        start = time.time()
        map.createWindow()
        print "window created in: ", time.time()-start, " seconds."

        gui.startGui()
