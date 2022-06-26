import math
import socket
import json
import multiprocessing
from multiprocessing import Manager
import numpy
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
                        amp_axis.append(rec_list[i]["CSI_info"][subcarrier][0])
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
    send_mode = True

    time_scope = 3
    subcarrier = int(input("subcarrier: "))
    rec_list = Manager().list()
    plot_proc = None

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("", 3333))
    while (True):
        if (send_mode==True):
            s.sendto("rx".encode(), ("192.168.4.1", 3333))
            send_mode = False
        else:
            (indata, addr) = s.recvfrom(4096)
            try:
                rx_data = json.loads(indata.decode())
                print(rx_data)
                if (rx_data["client_MAC"]=="8C:CE:4E:9A:04:5C"):
                    rec_list.append(rx_data)
                while (len(rec_list)>time_scope/0.01):
                    rec_list.pop(0)
                #figure proc
                if (plot_proc==None):
                    plot_proc = multiprocessing.Process(target=CSI_figure_proc, args=(rec_list, subcarrier, time_scope))
                    plot_proc.start()

            except:
                pass