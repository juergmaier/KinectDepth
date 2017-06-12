import serial
import time

ser=None

def initSerial(comPort):
    global ser
    ser = serial.Serial(port=comPort, baudrate=115200, timeout=0.1)

    print("Set up serial comm to arduino")

def readMessages():
    global orientation
    while ser.inWaiting() > 0:
        recv = ser.readline()
        print recv
        if recv[0:15] == "orientation x:":
            orientation = float(recv[16:])

def sendMoveCommand(dir, speed):
    msg = '1' + str(dir).zfill(3) + str(speed).zfill(3) + '\n'
    print("Send move " + msg)
    ser.write(msg) 

def sendRotateCommand(angle):

    if angle > 0:
        msg = '2' + str(angle).zfill(3) + '\n'
        print("Send rotate " + msg)
        ser.write(msg) 

    if angle < 0:
        msg = '3' + str(-angle).zfill(3) + '\n'
        print("Send rotate " + msg)
        ser.write(msg) 

def sendStopCommand():
    msg = '4' + '\n'
    print("Send stop " + msg)
    ser.write(msg)

def getCartOrientation():
    msg = '5' + '\n'
    #print("get Orientation " + msg)
    ser.write(msg)

def sendHeartbeat():
    ser.write('9' + '\n')
