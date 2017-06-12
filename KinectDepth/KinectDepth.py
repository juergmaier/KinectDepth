import thread
from numpy import random
import numpy as np
from pykinect import nui
import pathFinder
import time
import arduino
import rpyc
from rpyc.utils.server import ThreadedServer
import pygame


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


width = 640
height = 480
DEPTH_WINSIZE = width, height

screen_lock = thread.allocate()
screen = None

#top = np.zeros((640, 480, 3), np.uint32)

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
orientation = 0.0     # current orientation of cart
#lastMessage = None
TIMEOUT=500



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
        arduino.sendRotateCommand(angle)

    def exposed_move(self, direction, speed):
        arduino.sendMoveCommand(direction, speed)

    def exposed_stop(self):
        arduino.sendStopCommand()

    def exposed_getCartOrientation(self):
        global orientation
        arduino.getCartOrientation()
        arduino.readMessages()
        lastMessage = int(round(time.time() * 1000))
        #orientation = random.randint(0,10)
        return orientation

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


# bresenham as of http://eugen.dedu.free.fr/projects/bresenham/
def getVisionLine (x1, y1, x2, y2):

    dx = x2 - x1; 
    dy = y2 - y1; 

    xsign = 1 if dx > 0 else -1
    ysign = 1 if dy > 0 else -1

    dx = abs(dx)
    dy = abs(dy)

    if dx > dy:
        xx, xy, yx, yy = xsign, 0, 0, ysign
    else:
        dx, dy = dy, dx
        xx, xy, yx, yy = 0, ysign, xsign, 0

    D = 2*dy - dx
    y = 0

    for x in range(dx + 1):
        yield x1 + x*xx + y*yx, y1 + x*xy + y*yy
        if D > 0:
            y += 1
            D -= dx
        D += dy



def smoothPath(scaled, path):
    start = 0
    next = 1
    end = len(path) -1
    while next < len(path)-1:

        blocked = False
        for cell in getVisionLine(path[start][0], path[start][1], path[next][0], path[next][1]):
            if scaled.get_at(cell)[0] > 0:    # cell blocked
                blocked = True

        # if we hit a blocked cell add a waypoint to the list
        if blocked:
            #path.insert(next, path[next])
            start = next
            next = start+1

        # if direct path is free remove the waypoint
        else:
            del path[next]
            



def findPath(screen, source, target, scaler):
    '''
    @screen is a 640*480 image
    @source is the cam location
    @target is the point we want to go
    @scaler is the reduction factor for the path search grid
    '''
    start_time = time.time()
    finderGrid =  (screen.get_width()/scaler, screen.get_height()/scaler)
    scaled = pygame.transform.scale(screen,finderGrid)
    scaledSource = [x/8 for x in source]
    scaledTarget = [x/8 for x in target]
    a = pathFinder.AStar()
    a.init_grid(scaled.get_width(), scaled.get_height(), scaled, scaledSource, scaledTarget)
    path = a.solve()

    print("path found in %s seconds " % (time.time() - start_time))

    if path==None:
        print "no path found "
    else:
        for i in range(0, len(path) - 1):
            point = [x * 8 for x in path[i]]
            pygame.draw.circle(screen, BRIGHTGREEN, point,4, 0)
            pygame.image.save(screen, "astarPath.png")

        smoothPath(scaled, path)

        for i in range(0, len(path) - 1):
            cellFrom = [x * 8 for x in path[i]]
            cellTo = [x * 8 for x in path[i+1]]
            pygame.draw.line(screen, BRIGHTGREEN, cellFrom, cellTo, 1)
        pygame.image.save(screen, "directPath.png")

    # angle of first path segment of a  straight forward looking robot
    # tan(xdiff/ydiff)
    dx = path[0][0] - path[1][0]
    dy = path[0][1] - path[1][1]
    angle = np.degrees(np.tan(float(dx) / -dy))
    dist = np.sqrt(pow(dx, 2) + pow(dy, 2))
    dir = MOVEMENT.VORWAERTS         # at the moment we rotate and drive forward only

    print "action rotate angle: ", dir, " speed: 100"
    arduino.sendRotateCommand(dir)

    if dist > 500:
        speed = 255
    elif dist > 200:
        speed = 180
    else: 
        speed = 150

    print "action move forward, speed: ", speed
    #arduino.sendMoveCommand(0, speed)


def analyze():

    global screen
    global target
    global maxDist

    # Initialize PyGame
    print "in analyze, target: ", target

    screen = pygame.display.set_mode(DEPTH_WINSIZE)
    pygame.display.set_caption('PyKinect Depth Map Example')

    obstacleList = []
    depth = np.load("depth.npy")
    for row in range(maxDist):
        for col in range(width):
            dist = depth[col, row] / 10
            if  dist > 80 and dist < 300:
                screen.set_at((col, dist), WHITE)
                obstacleList.append((col, dist))

    pygame.display.update()
    pygame.image.save(screen, "topViewFiltered.png")

    # extend path blocking pixels to obstacles based on cart size
    for o in obstacleList:
        pygame.draw.circle(screen, RED, o, 40, 0)

    #scaled = pygame.transform.scale(screen,(80,60))
    #screen.fill((0,0,0))
    #screen.blit(scaled, (0,0))
    #pygame.display.update()
    
    # show source
    pygame.draw.circle(screen, RED, source, 10, 0)

    # show target (fixed target at the moment)
    pygame.draw.circle(screen, BLUE, target, 10, 0)
    pygame.image.save(screen, "topViewEnlarged.png")

    findPath(screen, source, target, 8)

    pygame.display.update()
    
    print "analyze done"

# -------------------------------------------
# wird für jedes empfangene Frame aufgerufen
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
        kinect.depth_frame_ready += depth_frame_ready   # fügt dem EventHandler den Aufruf von depth_frame_ready(frame) hinzu
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

    var = raw_input('option: ')
    #var = '3'

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


