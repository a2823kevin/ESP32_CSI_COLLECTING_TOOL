import socket
import json
import multiprocessing
from multiprocessing import Manager
from pynput.keyboard import Key, Listener
from utils import *

#key to stop recording(with video)
def On_press(key):
    global rec_util
    if (key==Key.esc):
        rec_util["stop_signal"] = True

if (__name__=="__main__"):
    lisener = Listener(on_press=On_press)
    lisener.start()

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
            rec_util = Manager().dict()
            while True:
                rec_video = input("record with video(without specifying motion)?(yes/no): ")
                if (rec_video=="yes"):
                    rec_util["record_time"] = None
                    rec_video = True
                    motion_name = None
                    break
                elif (rec_video=="no"):
                    motion_name = input("what motion you want to record?: ")
                    rec_util["record_time"] = float(input("how long do you want to record?: "))
                    rec_video = False
                    break
                else:
                    print("wrong input")
                    continue
            rec = True
            rec_util["rx_data"] = None
            rec_util["stop_signal"] = False
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
        CSI_rec_proc = multiprocessing.Process(target=CSI_record_proc, args=(motion_name, rec_util))
        CSI_rec_proc.start()
    #with video recording

    while (rec_util["stop_signal"]==False):
        (indata, _) = s.recvfrom(4096)
        try:
            indata = json.loads(indata.decode())
            #print(rec_util["rx_data"])
            if (indata["client_MAC"] in settings["STA_MAC_ARRDS"]):

                if (fig==True):
                    wave_lst.append(rec_util["rx_data"])
                    while (len(wave_lst)>time_scope/0.01):
                        wave_lst.pop(0)

                if (rec==True):
                    rec_util["rx_data"] = indata
                    if (rec_video==True):
                        pass
        except:
            pass