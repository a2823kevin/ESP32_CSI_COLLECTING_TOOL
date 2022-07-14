import socket
import json
import multiprocessing
from multiprocessing import Manager
from pynput.keyboard import Key, Listener
from mp_utils import *
from proc_utils import *

#key to stop recording(with video)
def On_press(key):
    global rec_util
    if (key==Key.esc):
        rec_util["stop_signal"] = True

if (__name__=="__main__"):
    lisener = Listener(on_press=On_press)
    lisener.start()

    fig = None
    rec = None

    rec_util = Manager().dict()
    rec_util["record_time"] = None
    rec_util["motion_name"] = None
    rec_util["current_time"] = None
    rec_util["rx_data"] = None
    rec_util["stop_signal"] = False

    #determine whether to plot waveform & record CSI
    while True:
        fig = input("Observe CSI waveform?(yes/no): ")
        if (fig=="yes"):
            while True:
                subcarrier = int(input("subcarrier(1~64): "))
                if (subcarrier>=1 and subcarrier<=64):
                    time_scope = 3
                    wave_lst = Manager().list()
                    break
                else:
                    print("wrong input")
                    continue
            fig = True
            break
        elif (fig=="no"):
            fig = False
            break
        else:
            print("wrong input")
            continue
    
    while True:
        rec = input("record CSI ?(yes/no): ")
        if (rec=="yes"):
            while True:
                rec_util["rec_method"] = int(input("recording method\n1.single motion with fixed recoring time\n2.with video recoring(without MediaPipe model)\n3.without video recoring(with MediaPipe model)\n4.with video recoring(with MediaPipe model): "))
                if (rec_util["rec_method"] not in range(1, 5)):
                    print("wrong input")
                    continue
                else:
                    if (rec_util["rec_method"]==1):
                        rec_util["motion_name"] = input("what motion you want to record?: ")
                        rec_util["record_time"] = float(input("how long do you want to record(sec)?: "))
                    rec = True
                    break
        elif (rec=="no"):
            rec = False
            break
        else:
            print("wrong input")
            continue

    #load settings
    with open("settings.json", "r") as fin:
        settings = json.load(fin)
    print("loaded settings.")

    #create UDP socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("", 3333))
    print("started UDP server.")

    #send "rx" to AP first
    for i in range(10):
        s.sendto("rx".encode(), (settings["AP_IP_ADDR"], 3333))

    #recieve packet from AP
    #with ploting
    if (fig==True):
        plot_proc = multiprocessing.Process(target=CSI_figure_proc, args=(wave_lst, subcarrier, time_scope))
        plot_proc.start()

    #with CSI recording
    if (rec==True):
        CSI_rec_proc = multiprocessing.Process(target=CSI_record_proc, args=(rec_util,))
        CSI_rec_proc.start()

    #with video recording
    if (rec_util["rec_method"]>1):
        video_rec_proc = multiprocessing.Process(target=video_record_proc, args=(rec_util,))
        video_rec_proc.start()

    while (rec_util["stop_signal"]==False):
        (indata, _) = s.recvfrom(4096)
        try:
            indata = json.loads(indata.decode())
            #print(indata)
            if (indata["client_MAC"] in settings["STA_MAC_ARRDS"]):
                rec_util["rx_data"] = indata
                if (fig==True):
                    wave_lst.append(indata)
                    while (len(wave_lst)>time_scope/0.01):
                        wave_lst.pop(0)
        except:
            pass