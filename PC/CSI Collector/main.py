import socket
import json
import multiprocessing
from multiprocessing import Manager
import matplotlib.pyplot as plt

def CSI_figure_proc(rec_list, subcarrier, time_scope):
    plt.ion()
    plt.figure()
    while True:
        try:
            time_axis = []
            amp_axis = []
            ctime = rec_list[-1]["recieved_time"]
            for i in range(len(rec_list)-1, -1, -1):
                try:
                    if (rec_list[i]["recieved_time"]-ctime<time_scope):
                        time_axis.append(rec_list[i]["recieved_time"])
                        amp_axis.append(rec_list[i]["CSI_info"][subcarrier-1][0])
                    else:
                        break
                except:
                    pass
            time_axis.reverse()
            amp_axis.reverse()

            plt.title(f"Subcarrier {subcarrier}: CSI recieved from {rec_list[0]['client_MAC']}")
            plt.xlabel("time")
            plt.ylabel("amplitude")
            plt.ylim([-127, 127])
            plt.plot(time_axis, amp_axis, "b-")
            plt.draw()
            plt.pause(0.01)
            plt.clf()
        except:
            continue

if (__name__=="__main__"):
    #determine whether to plot waveform & record CSI
    while True:
        fig = input("Observe CSI waveform?(yes/no): ")
        if (fig=="yes"):
            while True:
                subcarrier = int(input("subcarrier(1~64): "))
                if (subcarrier>=1 and subcarrier<=64):
                    time_scope = 3
                    rec_list = Manager().list()
                    break
                else:
                    print("wrong input")
                    continue
            break
        elif (fig=="no"):
            break
        else:
            print("wrong input")
            continue
    
    while True:
        rec = input("record CSI ?(yes/no): ")
        if (rec=="yes"):
            while True:
                rec_video = input("record with video?(yes/no): ")
                if (rec_video=="yes" or rec_video=="no"):
                    break
                else:
                    print("wrong input")
                    continue
            rec_proc = None
        elif (rec=="no"):
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
    if (fig=="yes"):
        plot_proc = multiprocessing.Process(target=CSI_figure_proc, args=(rec_list, subcarrier, time_scope))
        plot_proc.start()

    while (True):
        (indata, addr) = s.recvfrom(4096)
        try:
            rx_data = json.loads(indata.decode())
            #print(rx_data)
            if (rx_data["client_MAC"] in settings["STA_MAC_ARRDS"]):
                rec_list.append(rx_data)
            while (len(rec_list)>time_scope/0.01):
                rec_list.pop(0)
        except:
            pass