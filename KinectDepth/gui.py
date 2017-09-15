import arduino
import Tkinter as tk
import time
import KinectDepth
import map
from thread import start_new_thread

gui = None

class manualControl:
    def __init__(self, mainWindow):

        self.w = mainWindow
        self.btnArduino = tk.Button(mainWindow, text="Arduino", command=self.startArduino)
        self.btnArduino.grid(row=0, columnspan=2)
           
        self.lblInfo = tk.Label(mainWindow, text="wait for Arduino button pressed", fg ="white", bg="red")
        self.lblInfo.grid(row=1, columnspan=2)
    
        self.lblCommand = tk.Label(mainWindow, text="command: ")
        self.lblCommand.grid(row = 2, column = 0, sticky=tk.E)

        self.lblCommandValue = tk.Label(mainWindow, text=" ")
        self.lblCommandValue.grid(row = 2, column = 1)
                
        self.lblRotationTarget = tk.Label(mainWindow, text="target rotation: ")
        self.lblRotationTarget.grid(row = 3, column = 0, sticky=tk.E)

        self.lblRotationTargetValue = tk.Label(mainWindow, text=" ")
        self.lblRotationTargetValue.grid(row = 3, column = 1)

        self.lblRotationCurrent = tk.Label(mainWindow, text="current rotation: ")
        self.lblRotationCurrent.grid(row = 40, column = 0, sticky=tk.E)

        self.lblRotationCurrentValue = tk.Label(mainWindow, text=" ")
        self.lblRotationCurrentValue.grid(row = 40, column = 1)
        
        self.sbRotation = tk.Spinbox(mainWindow, from_=-90, to=90)
        self.sbRotation.grid(row = 50, column = 0, pady=20)

        self.btnRotate = tk.Button(mainWindow, text="Rotate", state="disabled", command=self.rotateCart)
        self.btnRotate.grid(row = 50, column = 1)
        
        self.choices = ["stop","vor","vor_diag_rechts","vor_diag_links","links","rechts","rueckwaerts","rueck_diag_rechts","rueck_diag_links"]
        defaultDirection = "vor"
        self.direction = self.choices.index(defaultDirection)

        move = tk.StringVar(gui)
        move.set(defaultDirection)
        self.ddMove = tk.OptionMenu(mainWindow, move, *self.choices, command=self.selectedDirection)
        self.ddMove.grid(row = 60, column = 0, sticky=tk.E)

        self.btnMove = tk.Button(mainWindow, text="Move", state="disabled", command = self.moveCart)
        self.btnMove.grid(row = 60, column = 1) 
        
        self.lblXValue = tk.Label(mainWindow, text="X: ")
        self.lblXValue.grid(row = 80, column = 0, pady=20, sticky=tk.E)

        self.sbX = tk.Spinbox(mainWindow, from_=0, to=400, text = "300")
        self.sbX.grid(row = 80, column = 1)
        self.sbX.insert(0, 30)

        self.lblYValue = tk.Label(mainWindow, text="Y: ")
        self.lblYValue.grid(row = 82, column = 0, sticky=tk.E)

        self.sbY = tk.Spinbox(mainWindow, from_=0, to=400)
        self.sbY.grid(row = 82, column = 1)
        self.sbY.insert(0, 34)

        self.btnNav = tk.Button(mainWindow, text="navigate", state="normal", command = self.navigateTo)
        self.btnNav.grid(row = 84, column = 1)
        
        self.lblHeartBeat = tk.Label(mainWindow, text="Heart Beat", fg="red")
        self.lblHeartBeat.grid(row = 100, column = 0, columnspan = 2, pady=20)

        self.btnStop = tk.Button(mainWindow, text="STOP CART", state="normal", command = self.stopCart, bg = "red", fg = "white")
        self.btnStop.grid(row = 200, column = 0, columnspan=2, pady=30)

    def selectedDirection(self, value):
        self.direction = self.choices.index(value)
        #println("selected direction: " + value + " index: " + self.direction)


    def startArduino(self):

        arduino.initSerial("COM5")
        self.lblInfo.configure(text = "arduino connected, waiting for cart ready message", bg="white smoke", fg="orange")
        self.btnArduino.configure(state = "disabled")

        # Messages sent by the Arduino should always get processed
        # Start reader in its own thread
        start_new_thread(arduino.readMessages,())

        self.w.update_idletasks()
        self.w.after(2000, self.checkStatus)


    def checkStatus(self):
    
        if KinectDepth.arduinoStatus == 1:
            self.lblInfo.configure(text = "cart ready", bg="lawn green", fg="black")
            self.btnRotate.configure(state="normal")
            self.btnMove.configure(state="normal")
            self.btnNav.configure(state="normal")
            self.w.update_idletasks()
            self.w.after(10, self.heartBeat)
        else:
            self.w.after(400, self.checkStatus)
            #map.continue_pygame_loop()        

    def navigateTo(self):
        start = time.time()
        KinectDepth.analyze((int(self.sbX.get()),int(self.sbY.get())))
        print "analyzed in: ", time.time()-start, " seconds."
    
    def heartBeat(self):

        # toggle heartBeat message color
        if self.lblHeartBeat.cget("fg") == "red":
            self.lblHeartBeat.configure(fg = "green")
        else: 
            self.lblHeartBeat.configure(fg = "red")

        arduino.sendHeartbeat()
        arduino.getCartOrientation()
        self.lblRotationCurrentValue.configure(text=str(KinectDepth.orientation))
        self.w.update_idletasks()
        self.w.after(300, self.heartBeat)   # heart beat loop
        #map.continue_pygame_loop()

    def stopCart(self):

        arduino.sendStopCommand()
        self.lblCommand.configure(text="Stop")
        self.w.update_idletasks()

    
    def moveCart(self, speed = 50):

        arduino.sendMoveCommand(self.direction, speed)
        self.lblCommandValue.configure(text="Move")
        #self.lblMove.configure(text=str(speed))
        self.w.update_idletasks()


    def rotateCart(self):

        angle = int(self.sbRotation.get())

        self.lblCommandValue.configure(text="Rotate")
        self.lblRotationTargetValue.configure(text=str(KinectDepth.orientation + angle))
        arduino.sendRotateCommand(angle)
        self.w.update_idletasks()





def startGui():

    global gui

    start=time.time()
    gui = tk.Tk()
    gui.geometry('300x450+100+150')     # window size and position

    controller = manualControl(gui)
    print "gui initialized in: ", time.time()-start, " seconds"
    gui.mainloop()

