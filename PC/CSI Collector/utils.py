from datetime import datetime
import matplotlib.pyplot as plt
import cv2

def CSI_figure_proc(wave_lst, subcarrier, time_scope):
    plt.ion()
    plt.figure()
    while (True):
        try:
            time_axis = []
            amp_axis = []
            ctime = wave_lst[-1]["recieved_time"]
            for i in range(len(wave_lst)-1, -1, -1):
                try:
                    if (wave_lst[i]["recieved_time"]-ctime<time_scope):
                        time_axis.append(wave_lst[i]["recieved_time"])
                        amp_axis.append(wave_lst[i]["CSI_info"][subcarrier-1][0])
                    else:
                        break
                except:
                    pass
            time_axis.reverse()
            amp_axis.reverse()

            plt.title(f"Subcarrier {subcarrier}: CSI recieved from {wave_lst[0]['client_MAC']}")
            plt.xlabel("time")
            plt.ylabel("amplitude")
            plt.ylim([-127, 127])
            plt.plot(time_axis, amp_axis, "b-")
            plt.draw()
            plt.pause(0.01)
            plt.clf()
        except:
            continue

def CSI_record_proc(motion, rec_util):
    #data name: YYYYMMDDHHMMSS_MACADDR_MOTIONNAME.csv / YYYYMMDDHHMMSS_MACADDR.csv
    #form: timestamp, subcarrier0, subcarrier1, ..., subcarrier64
    writting_files = {}
    current_data = None
    start_time = None

    while (rec_util["stop_signal"]==False):
        try:
            #avoid to record duplicate data
            if (current_data!=rec_util["rx_data"]):
                current_data = rec_util["rx_data"]
                rec_util["current_time"] = current_data["recieved_time"]

                #init start time
                if (start_time==None):
                    start_time = rec_util["rx_data"]["recieved_time"]

                #prepare file for recording
                if (current_data["client_MAC"] not in writting_files):
                    t = datetime.now().strftime("%Y%m%d%H%M%S")
                    maddr = current_data["client_MAC"]
                    m = ""
                    for s in maddr.split(":"):
                        m += s

                    if (motion!=None):
                        fname = f"./record/{t}_{m}_{motion}.csv"
                    else:
                        fname = f"./record/{t}_{m}.csv"
                    writting_files[maddr] = open(fname, "w", encoding="utf8")
                    print(f"created file: {fname}")

                    writting_files[maddr].write("timestamp, ")
                    for i in range(1, 64):
                        writting_files[maddr].write("subcarrier"+str(i).rjust(2, "0")+"_mag"+", ")
                        writting_files[maddr].write("subcarrier"+str(i).rjust(2, "0")+"_ang"+", ")
                    writting_files[maddr].write("subcarrier64_mag, subcarrier64_ang\n")
                
                #write CSI
                writting_files[maddr].write(str(current_data["recieved_time"])+", ")
                for i in range(len(current_data["CSI_info"])-1):
                    writting_files[maddr].write(str(current_data["CSI_info"][i][0])+", "+str(current_data["CSI_info"][i][1])+", ")
                writting_files[maddr].write(str(current_data["CSI_info"][63][0])+", "+str(current_data["CSI_info"][63][1])+"\n")
        except:
            pass

        #stop by time
        if (rec_util["record_time"]!=None):
            if (rec_util["current_time"]-start_time>=rec_util["record_time"]):
                rec_util["stop_signal"] = True
                break
    
    for mac in writting_files:
        writting_files[mac].close()
    print("stopped recording")

def video_record_proc(rec_util):
    ctime = None
    fname = "./record/" + datetime.now().strftime("%Y%m%d%H%M%S")
    fout = cv2.VideoWriter(f"{fname}.mp4", cv2.VideoWriter_fourcc(*"XVID"), 30, (640, 480))
    video_stream = None

    try:
        while (rec_util["stop_signal"]==False):
            if (rec_util["current_time"]!=ctime):
                if (video_stream==None):
                    video_stream = cv2.VideoCapture(0)
                ctime = rec_util["current_time"]
                (ret, frame) = video_stream.read()
                cv2.putText(frame, str(ctime), (0, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0))
                fout.write(frame)
    except:
        pass

    video_stream.release()
    fout.release()

if __name__=="__main__":
    cap = cv2.VideoCapture(0)
    (ret, frame) = cap.read()
    cv2.imwrite("img.png", frame)