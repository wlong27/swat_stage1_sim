# Simulator
# Tank T101, valve MV101, pump P101, level sensor LIT101
# T101 H = 800mm, L = 500mm, should never overflow
# P101 should be OFF is T101 at L marker
# attack is to compromise integrity of LIT101


import tkinter
import time
import threading
import random
import queue
from tkinter import ttk

# initialise simulator variables
isAttacked_MV101 = False
isAttacked_LIT101 = False
isAttacked_P101 = False
isAutoSIM = True
isAttack = True


FLOWRATE_1 = 1.11857
FLOWRATE_2 = 28.5234
FLOWRATE_3 = -27.40
FLOWRATE_4 = 0
flowRate_T101 = FLOWRATE_2


BIAS = 2
TAU = 5
CUSUM = 0

isBIAS_ATK = False
isSURGE_ATK = False
isGEO_ATK = False

ATTACKS = 0
DETECTED = 0
FALSE_ALARMS = 0

#MV101=OPEN, P101=ON:  Rise at 1.11857mm/minute
#MV101=OPEN, P101=OFF: Rise at 28.5234mm/minute
#MV101=CLOSED, P101=ON:  Fall at 27.40 mm/minute
#MV101=CLOSED, P101=OFF: No change in water level

HVal = 771
LVal = 530
start_time = time.time()

def startCommand():
    print('test')

class GuiPart:
    def __init__(self, master, queue, stopCommand):
        self.queue = queue    
        self.master = master 
        self.isAttacked_MV101 = False
        self.isAttacked_LIT101 = False
        self.isAttacked_P101 = False
        self.isAutoSIM = True

        # btn_start = tkinter.Button(master, text="STOP", command=stopCommand)
        # btn_start.place(x=30, y=270, anchor="center")        
        #Custom vertical progress bar styling
        s = ttk.Style()
        s.theme_use('clam')
        s.configure("blue.Vertical.TProgressbar", foreground='blue', background='blue')
        
         # T101 progress bar
        self.var_pb_progress = tkinter.IntVar()
        pb_T101 = ttk.Progressbar(master, orient="vertical",
                     length=200, maximum=10,
                     mode="determinate",
                     var=self.var_pb_progress, style="blue.Vertical.TProgressbar")
        pb_T101.place(relx=0.5, rely=0.5, anchor="center")
        pb_T101["value"] = 0

        # T101 volume display label        
        self.var_T101 = tkinter.DoubleVar()
        lbl_T101 = tkinter.Label(root, textvariable=self.var_T101)
        lbl_T101.place(x=120, y=300)
        lbl_T101.configure(font="Bold 11")
        self.var_T101.set("T101: 0" )

        #High(H), Low(L) markers 
        lbl_high = tkinter.Label(master, text="H: 800")
        lbl_high.place(x=190, y=130, anchor="center")
        lbl_high.configure(fg="red", font="Bold 10")
        lbl_low = tkinter.Label(master, text="L: 500")
        lbl_low.place(x=190, y=200, anchor="center")
        lbl_low.configure(fg="green", font="Bold 10")

        # Application message
        self.var_Msg = tkinter.StringVar()
        lbl_Msg = tkinter.Label(master, textvariable=self.var_Msg)
        lbl_Msg.pack(side="bottom")
        lbl_Msg.configure(font="Bold 9")
        self.var_Msg.set("NORMAL operation")

        # Auto simulation 
        self.btn_SIM = tkinter.Button(master, text="Auto", command=self.toggle_SIM)
        self.btn_SIM.place(x=30, y=150, anchor="center")
        self.btn_SIM.configure(text="Auto", bg="green", fg="white")
   
        # MV101 toggle button
        self.btn_MV101 = tkinter.Button(master, text="MV101", command=self.toggle_MV101)
        self.btn_MV101.place(x=30, y=30, anchor="center")
        #self.btn_MV101.configure(text="MV101", bg="green", fg="white")

        # MV101 state label
        self.var_MV101 = tkinter.StringVar()
        self.lbl_MV101 = tkinter.Label(master, textvariable=self.var_MV101)
        self.lbl_MV101.place(x=30, y=60, anchor="center")
        self.lbl_MV101.configure(font="Bold 10")
        self.var_MV101.set("OPEN")

        # P101 state label
        self.var_FlowRate = tkinter.StringVar()
        self.lbl_FlowRate = tkinter.Label(master, textvariable=self.var_FlowRate)
        self.lbl_FlowRate.place(x=10, y=100)
        self.lbl_FlowRate.configure(font="Bold 10")
        self.var_FlowRate.set("Level Rate: \n" + str(round(flowRate_T101, 4)) + "mm/min")

        #CUSUM threshold tau
        self.var_Tau = tkinter.StringVar()
        self.lbl_Tau = tkinter.Label(master, textvariable=self.var_Tau)
        self.lbl_Tau.place(x=10, y=170)
        self.lbl_Tau.configure(font="Bold 11")
        self.var_Tau.set("t: " + str(TAU))

        #CUSUM bias
        self.var_Bias = tkinter.StringVar()
        self.lbl_Bias = tkinter.Label(master, textvariable=self.var_Bias)
        self.lbl_Bias.place(x=10, y=190)
        self.lbl_Bias.configure(font="Bold 11")
        self.var_Bias.set("b: " + str(BIAS)) 

        #Attacks count
        self.var_Atk = tkinter.StringVar()
        self.lbl_Atk = tkinter.Label(master, textvariable=self.var_Atk)
        self.lbl_Atk.place(x=10, y=220)
        self.lbl_Atk.configure(font="Bold 11")
        self.var_Atk.set("A: " + str(ATTACKS))

        #Detection count
        self.var_Det = tkinter.StringVar()
        self.lbl_Det = tkinter.Label(master, textvariable=self.var_Det)
        self.lbl_Det.place(x=10, y=240)
        self.lbl_Det.configure(font="Bold 11")
        self.var_Det.set("D: " + str(DETECTED))

        #Detection rate D/A
        self.var_DetRate = tkinter.StringVar()
        self.lbl_DetRate = tkinter.Label(master, textvariable=self.var_DetRate)
        self.lbl_DetRate.place(x=10, y=260)
        self.lbl_DetRate.configure(font="Bold 11")
        self.var_DetRate.set("D/A: " + str((DETECTED/ATTACKS) if ATTACKS > 0 else 0))

        #False alarm
        self.var_FA = tkinter.StringVar()
        self.lbl_FA = tkinter.Label(master, textvariable=self.var_FA)
        self.lbl_FA.place(x=10, y=280)
        self.lbl_FA.configure(font="Bold 11")
        self.var_FA.set("False: " + str(FALSE_ALARMS))


        # LIT101 attack button
        self.btn_LIT101 = tkinter.Button(root, text="LIT101", command=self.attack_LIT101)
        self.btn_LIT101.place(x=150, y=30, anchor="center")
        #self.btn_LIT101.configure(state="disabled")
        self.btn_LIT101.configure(text="LIT101", bg="grey", fg="white")

        # LIT101 label to show values
        self.var_LIT101 = tkinter.DoubleVar()
        lbl_LIT101 = tkinter.Label(master, textvariable=self.var_LIT101)
        lbl_LIT101.place(x=120, y=50)
        lbl_LIT101.configure(font="Bold 11")
        self.var_LIT101.set("0" )

        # P101 toggle button
        self.btn_P101 = tkinter.Button(root, text="P101", command=self.toggle_P101)
        self.btn_P101.place(x=270, y=30, anchor="center")
        #self.btn_P101.configure(text="P101", bg="green", fg="white")

        # P101 state label
        self.var_P101 = tkinter.StringVar()
        self.lbl_PIP01 = tkinter.Label(master, textvariable=self.var_P101)
        self.lbl_PIP01.place(x=270, y=60, anchor="center")
        self.lbl_PIP01.configure(font="Bold 10")
        self.var_P101.set("OFF")
    
    def toggle_SIM(self):
        if (self.isAutoSIM):
            self.btn_SIM.configure(text="Manual", bg="grey", fg="white")
            self.isAutoSIM = False
        else: 
            self.btn_SIM.configure(text="Auto", bg="green", fg="white")
            self.isAutoSIM = True

    def toggle_MV101(self):
        if (self.var_MV101.get() == "CLOSED"):
            self.btn_MV101.configure(bg="green", fg="white")
            self.var_MV101.set("OPEN")
        else: 
            self.btn_MV101.configure(bg="grey", fg="white")
            self.var_MV101.set("CLOSED")

    def toggle_P101(self):
        if (self.var_P101.get() == "OFF"):
            self.btn_P101.configure(bg="green", fg="white")
            self.var_P101.set("ON")
        else: 
            self.btn_P101.configure(bg="grey", fg="white")
            self.var_P101.set("OFF")
     

    def attack_MV101(self):
        if (self.isAttacked_MV101):
            self.btn_MV101.configure(bg="green", fg="white")
            self.isAttacked_MV101 = False
            self.var_Msg.set("NORMAL operation")
        else: 
            self.btn_MV101.configure(bg="red", fg="black")
            self.isAttacked_MV101 = True
            self.var_Msg.set("MV101 is attacked!")

    def attack_LIT101(self):
        if (self.isAttacked_LIT101):
            self.btn_LIT101.configure(bg="grey", fg="white")
            self.isAttacked_LIT101 = False
        else: 
            self.btn_LIT101.configure(bg="red", fg="black")
            self.isAttacked_LIT101 = True
            self.var_Msg.set("LIT101 is attacked!")
    
    def attack_P101(self):
        if (self.isAttacked_P101):
            self.btn_P101.configure(bg="green", fg="white")
            self.isAttacked_P101 = False
            self.var_Msg.set("NORMAL operation")
        else: 
            self.btn_P101.configure(bg="red", fg="black")
            self.isAttacked_P101 = True
            self.var_Msg.set("P101 is attacked!")

    def processIncoming(self):
        """Handle all messages currently in the queue, if any."""
        while self.queue.qsize():
            try:
                volume_T101 = self.queue.get(0)
                self.var_pb_progress.set(volume_T101/100) #scale to 100
                self.var_T101.set("T101: " + str(round(volume_T101,4)))
                self.var_LIT101.set(self.take_reading(volume_T101))
                self.update_physical(volume_T101)
                self.PLC_command()
                self.check_attack(volume_T101)
                self.output_results()
                self.master.update_idletasks()
            except queue.Empty:
                pass
    
    def update_physical(self, volume_T101):
        global flowRate_T101
        if volume_T101 < 500:
            self.var_Msg.set("*** ERROR: UNDERFLOW !!! ***");
        elif volume_T101 > 800:
            self.var_Msg.set("*** ERROR: OVERFLOW !!! ***");
        else:
            self.var_Msg.set("NORMAL operation")            

        if self.var_MV101.get() == "OPEN" and self.var_P101.get() == "ON":
            flowRate_T101 = FLOWRATE_1
        elif self.var_MV101.get() == "OPEN" and self.var_P101.get() == "OFF":
            flowRate_T101 = FLOWRATE_2
        elif self.var_MV101.get() == "CLOSED" and self.var_P101.get() == "ON":
            flowRate_T101 = FLOWRATE_3
        elif self.var_MV101.get() == "CLOSED" and self.var_P101.get() == "OFF":
            flowRate_T101 = FLOWRATE_4
        
        #update flow level
        self.var_FlowRate.set("Level Rate: \n" + str(round(flowRate_T101, 4)) + "mm/min")


    def PLC_command(self):
        global HVal, LVal
        if self.isAutoSIM:
            if self.var_LIT101.get() > HVal:
                self.var_P101.set("ON")
                self.btn_P101.configure(bg="green", fg="white")
                self.var_MV101.set("CLOSED")
                self.btn_MV101.configure(bg="grey", fg="white")
            elif self.var_LIT101.get() < LVal:
                self.var_P101.set("OFF")
                self.btn_P101.configure(bg="grey", fg="white")
                self.var_MV101.set("OPEN")
                self.btn_MV101.configure(bg="green", fg="white")
            else:
                self.var_P101.set("ON")
                self.btn_P101.configure(bg="green", fg="white")
                self.var_MV101.set("OPEN")
                self.btn_MV101.configure(bg="green", fg="white")
    
    def check_attack(self, volume_T101):
        #attack detection via CUSUM
        global CUSUM, BIAS, TAU, DETECTED, FALSE_ALARMS, isAttack, isBIAS_ATK, isGEO_ATK, isSURGE_ATK
        f = open("cusum.txt","r")
        params = f.read().split()

        #check the current attack type
        f = open("attacktype.txt","r")
        attackType = f.read()
        if (attackType == 'BIAS'):
            isBIAS_ATK = True
        elif(attackType == 'GEOMETRIC'): #not implemented
            isGEO_ATK = True
        elif(attackType == 'SURGE'):
            isSURGE_ATK = True

        if (len(params) >= 2):
            BIAS = float(params[0])
            TAU = float(params[1])
            self.var_Tau.set("t: " + str(TAU))
            self.var_Bias.set("b: " + str(BIAS))
        
        T101_expected = volume_T101
        LIT101 = self.var_LIT101.get()

        #increase bias per timestep
        if (isBIAS_ATK):
            BIAS = round(BIAS * (time.time() -start_time), 4)
            self.var_Bias.set("b: " + str(BIAS))
        
        T101_z = abs(T101_expected - LIT101) - BIAS
        #S(k) = (S(k-1) + z(k))+
        CUSUM = CUSUM + T101_z
        if CUSUM < 0:
            CUSUM = 0
        
        self.var_Msg.set("CUSUM value = " + str(round(CUSUM, 4)))
        if CUSUM > TAU:
            DETECTED += 1
            self.var_Det.set("D: " + str(DETECTED))
            self.var_Msg.set("!!!! CUSUM ALERT detected !!!! value = " + str(round(CUSUM, 4)))

            #check if detection is false alarm
            if (isAttack == False):
                FALSE_ALARMS += 1
                self.var_FA.set("False: " + str(FALSE_ALARMS))
            
            self.var_DetRate.set("D/A: " + str(round(DETECTED/ATTACKS, 4) if ATTACKS > 0 else 0))


    def take_reading(self, volume_T101):
        global ATTACKS, isAttack

        noise = int(random.choice([0, 11, -11, 11]))
        if self.isAttacked_LIT101 == False:
            isAttack = False
            return round(volume_T101 + noise, 4)

        # this is where the attack can take place
        # it will look for the file "attack.txt" and perform the change value in the file 
        f = open("attack.txt","r")
        deltas = f.read().split()
        delta = int(random.choice(deltas))
        isAttack = True if delta != 0 else False
        if delta != 0:
            ATTACKS += 1
            isAttack = True
            self.var_Atk.set("A: " + str(ATTACKS))
        else:
            isAttack = False

        return round(volume_T101 + delta + noise, 4) 

    def output_results(self):
        global BIAS, TAU, ATTACKS, DETECTED, CUSUM, FALSE_ALARMS
        f = open("outputs.txt","a")
        f.write(f"{BIAS},{TAU},{ATTACKS},{DETECTED},{round(CUSUM,4)},{FALSE_ALARMS}\n")


       

class ThreadedClient:
    def __init__(self, master):
        self.master = master
        # Create the queue and GUI
        self.queue = queue.Queue()
        self.gui = GuiPart(master, self.queue, self.stopThread)
 
        # More threads can also be created and used, if necessary
        self.running = 1
        self.thread1 = threading.Thread(target=self.workerThread1)
        self.thread1.start()

        # Start the periodic call in the GUI to check if the queue contains
        self.periodicCall()
        print(f"Time elapsed:{time}")

    def periodicCall(self):
        # Periodic call every 200ms to process incoming msg
        self.gui.processIncoming()
        if not self.running:
            import sys
            sys.exit(1)
        self.master.after(200, self.periodicCall)

    def workerThread1(self):
        global start_time
        volume_T101 = 0 
        while self.running:
            volume_T101 += flowRate_T101
            if volume_T101 < 0:
                volume_T101 = 0
            print(str(time.time() - start_time))
            time.sleep(1)
            self.queue.put(volume_T101)
            
    def stopThread(self):
        self.running = 0
       

if __name__== "__main__":
    rand = random.Random()
    root = tkinter.Tk()
    root.minsize(width=300, height=400)
    root.maxsize(width=300, height=400)
    root.title("Simulator - Stage1")
    client = ThreadedClient(root)
    root.mainloop()