from datetime import datetime
import matplotlib.pyplot as plt
import cv2
from mp_utils import *

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
                        amp_axis.append(wave_lst[i]["CSI_info"][(subcarrier-1)*2][0])
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

def CSI_record_proc(rec_util):
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
                if (len(current_data["CSI_info"])!=64):
                    continue
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

                    if (rec_util["rec_method"]==1):
                        fname = f"./record/{t}_{m}_" + rec_util["motion_name"] + ".csv"
                    elif (rec_util["rec_method"]==2):
                        fname = f"./record/{t}_{m}.csv"
                    else:
                        fname = f"./record/{t}_{m}_mp.csv"
                    writting_files[maddr] = open(fname, "w", encoding="utf8")
                    print(f"created file: {fname}")

                    writting_files[maddr].write("timestamp,")
                    #write first row
                    if (rec_util["rec_method"]<3):
                        for i in range(1, 64):
                            writting_files[maddr].write("subcarrier"+str(i).rjust(2, "0")+"_mag"+",")
                            writting_files[maddr].write("subcarrier"+str(i).rjust(2, "0")+"_ang"+",")
                        writting_files[maddr].write("subcarrier64_mag,subcarrier64_ang\n")
                    #with video (MediaPipe method)
                    else:
                        for i in range(1, 65):
                            writting_files[maddr].write("subcarrier"+str(i).rjust(2, "0")+"_mag"+",")
                            writting_files[maddr].write("subcarrier"+str(i).rjust(2, "0")+"_ang"+",")
                        for n in ["head", "chest", "left_elbow", "left_hand", "right_elbow", "right_hand", "hip", "left_knee", "left_foot", "right_knee"]:
                            writting_files[maddr].write(n+"_x,")
                            writting_files[maddr].write(n+"_y,")
                            writting_files[maddr].write(n+"_z,")
                        writting_files[maddr].write("right_foot_x,right_foot_y,right_foot_z\n")
                
                #write CSI
                if (rec_util["rec_method"]<3):
                    writting_files[maddr].write(str(current_data["recieved_time"])+",")
                    for i in range(len(current_data["CSI_info"])-1):
                        writting_files[maddr].write(str(current_data["CSI_info"][i][0])+","+str(current_data["CSI_info"][i][1])+",")
                    writting_files[maddr].write(str(current_data["CSI_info"][63][0])+","+str(current_data["CSI_info"][63][1])+"\n")

                #MediaPipe method
                else:
                    current_pose = rec_util["current_MP_pose"]
                    if (current_pose!=None):
                        writting_files[maddr].write(str(current_data["recieved_time"])+",")
                        for i in range(len(current_data["CSI_info"])):
                            writting_files[maddr].write(str(current_data["CSI_info"][i][0])+","+str(current_data["CSI_info"][i][1])+",")
                        #MP pose
                        for i in range(len(current_pose)-1):
                            writting_files[maddr].write(str(current_pose[i][0])+",")
                            writting_files[maddr].write(str(current_pose[i][1])+",")
                            writting_files[maddr].write(str(current_pose[i][2])+",")
                        writting_files[maddr].write(str(current_pose[-1][0])+",")
                        writting_files[maddr].write(str(current_pose[-1][1])+",")
                        writting_files[maddr].write(str(current_pose[-1][2])+"\n")
                        
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
    video_stream = None
    mppp = get_mp_pose_proccessor()

    if (rec_util["rec_method"]==2 or rec_util["rec_method"]==4):
        fname = "./record/" + datetime.now().strftime("%Y%m%d%H%M%S")
        fout = cv2.VideoWriter(f"{fname}.mp4", cv2.VideoWriter_fourcc(*"XVID"), 30, (640, 480))

    try:
        while (rec_util["stop_signal"]==False):
            if (rec_util["current_time"]!=ctime):
                if (video_stream==None):
                    video_stream = cv2.VideoCapture(0)
                ctime = rec_util["current_time"]
                (ret, frame) = video_stream.read()

                #MP method
                if (rec_util["rec_method"]>2):
                    frame.flags.writeable = False
                    rec_util["current_MP_pose"] = get_simplified_pose(frame, mppp, skip_incomplete=False)
                    frame.flags.writeable = True

                if (rec_util["rec_method"]==2 or rec_util["rec_method"]==4):
                    cv2.putText(frame, str(ctime), (0, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255))
                    fout.write(frame)

        video_stream.release()
        if (rec_util["rec_method"]==2 or rec_util["rec_method"]==4):
            fout.release()
    except:
        pass

if __name__=="__main__":
    cap = cv2.VideoCapture(0)
    (ret, frame) = cap.read()
    cv2.imwrite("img.png", frame)