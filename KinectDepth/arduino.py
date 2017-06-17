import serial
import time
import gui
import KinectDepth

ser=None

def initSerial(comPort):
    global ser
  
    while True:
        try:
            ser = serial.Serial(port=comPort, baudrate=115200, timeout=0.1)
            print("Serial comm to arduino established")
            break

        except:
            print("exception on serial connect with " + comPort)
            time.sleep(1)

# this runs in its own thread
def readMessages():
    
    while ser.is_open:

        while ser.inWaiting() > 0:
            recv = ser.readline()

            if recv[0:10] == "cart ready":
                KinectDepth.arduinoStatus = 1

            elif recv[0:14] == "orientation x:":
                newOrientation = float(recv[15:])
                if int(KinectDepth.orientation) != int(newOrientation):
                    KinectDepth.orientation = newOrientation
                    print "new cart orientation: " + str(KinectDepth.orientation)

            else:
                print "<-A " + recv
        pass

def sendMoveCommand(dir, speed):

    msg = '1' + str(dir).zfill(3) + str(speed).zfill(3) + '\n'
    print("Send move " + msg)
    ser.write(msg) 


def sendRotateCommand(angle):

#    global ser

    if angle > 0:
        msg = '2' + str(angle).zfill(3) + '\n'
        print("Send rotate " + msg)
        ser.write(msg) 

    if angle < 0:
        msg = '3' + str(-angle).zfill(3) + '\n'
        print("Send rotate " + msg)
        ser.write(msg) 

def sendStopCommand():

#    global ser

    msg = '4' + '\n'
    print("Send stop " + msg)
    ser.write(msg)

def getCartOrientation():

#    global ser

    msg = '5' + '\n'
    #print("get Orientation " + msg)
    ser.write(msg)

def sendHeartbeat():

    ser.write('9' + '\n')
