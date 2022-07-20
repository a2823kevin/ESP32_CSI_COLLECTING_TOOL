import json
import csv
from pydoc import cli
import numpy
import matplotlib.pyplot as plt
import pandas
from scipy.signal import butter, lfilter, freqz

def eliminate_unused_subcarrier(fpath):
    fin = pandas.read_csv(fpath)
    count_table = fin.nunique(0)
    unused_sc = []

    #search unused subcarriers
    for key in count_table.keys():
        if (key[0:10]=="subcarrier" and key[-3:]=="mag"):
            if (count_table[key]==1 and count_table[key[:-3]+"ang"]==1):
                unused_sc.append(key[:-4])
    
    #eliminate
    for sc in unused_sc:
        fin = fin.drop(sc+"_mag", axis=1)
        fin = fin.drop(sc+"_ang", axis=1)
    
    #save file
    fin.to_csv(fpath, index=False)
    print(f"eliminated unused subcarriers: {unused_sc} for {fpath}")

def get_sampling_period(fpath):
    fin = pandas.read_csv(fpath)
    fin = fin["timestamp"].diff()
    fin = fin.dropna()
    eq_zero = (fin==0)
    for idx in range(1, len(eq_zero==0)+1):
        if (eq_zero[idx]==True):
            fin = fin.drop(idx)

    #return min & avg
    return (fin.min(), fin.mean())

def interpolate(fpath, sampling_period):
    fin = pandas.read_csv(fpath)
    interval = fin["timestamp"].diff()

    row = {}
    for key in fin.keys():
        row[key] = numpy.NaN
    row["timestamp"] = []

    #search timing to interpolate
    for i in interval.keys():
        if (interval[i]==0):
            continue
        if (sampling_period/interval[i]>=0.4 and sampling_period/interval[i]<=0.6):
            row["timestamp"].append((fin["timestamp"][i]+fin["timestamp"][i-1])/2)
    
    #add to data & interpolate
    fin = pandas.concat([fin, pandas.DataFrame(row)])
    fin = fin.sort_values("timestamp")
    fin = fin.interpolate("linear")

    #save file
    fin.to_csv(fpath, index=False)

def clip(fpath, start=None, end=None, motion=None):
    fin = pandas.read_csv(fpath)
    if (start==None):
        start = fin["timestamp"][0]
    if (end==None):
        end = fin["timestamp"][len(fin["timestamp"])-1]
    
    #search start point & end point
    time = fin["timestamp"]
    start_idx, end_idx = None, None
    for i in range(len(time)):
        if (time[i]<=start and time[i+1]>=start):
            start_idx = i + 1
            break
    for i in range(start_idx+1, len(time)):
        if (time[i]<=end and time[i+1]>=end):
            end_idx = i
            break
    
    #clip
    fin = fin.iloc[start_idx:end_idx+1, :]

    #save file
    if (motion!=None):
        fpath = fpath[:-4] + f"_{motion}.csv"
    fin.to_csv(fpath, index=False)
    print("clipped record from "+str(fin["timestamp"][start_idx])+" to "+str(fin["timestamp"][end_idx])+f" and saved it to {fpath}")

def plot_CSI_signal(fpath, batch_size=15000, batch_num=1, part="mag", subcarriers=[4, 8, 16, 32, 64]):
    sc_map = {}
    sc_idx_map = {}
    start = (batch_num-1) * batch_size
    end = batch_num * batch_size
    counter = 0

    with open(fpath, "r", encoding="utf8") as fin:
        for row in csv.reader(fin):
            if (row[0]=="timestamp"):
                nonexist_sc = []
                for n in subcarriers:
                    col_head = " subcarrier"+str(n).rjust(2, "0")+f"_{part}"
                    if (col_head in row):
                        sc_map[n] = []
                        sc_idx_map[n] = row.index(col_head)
                    else:
                        nonexist_sc.append(n)
                for n in nonexist_sc:
                    subcarriers.pop(subcarriers.index(n))
            else:
                if (counter>=start and counter<end):
                    for n in subcarriers:
                        sc_map[n].append(float(row[sc_idx_map[n]]))
                    counter += 1
                    continue
                elif (counter<start):
                    counter += 1
                    continue
                elif (counter>=end):
                    break
        
    #plot
    plt.figure()
    plt.xlabel("packets")
    plt.ylabel(part)
    plt.ylim([-127, 127])
    for n in sc_map:
        plt.plot(range(start, counter), sc_map[n], label="subcarrier"+str(n).rjust(2, "0"), linewidth=0.3)
    plt.legend()
    plt.show()


def get_butterworth_LPF(cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return b, a

def filtering(fpath, b, a):
    arr = []
    with open(fpath, "r", encoding="utf8") as fin:
        for row in csv.reader(fin):
            arr.append(row)

if __name__=="__main__":
    fpath = "./CSI Collector/record/20220718171953_8CCE4E9A045C_mp.csv"
    with open("./Preprocessing/settings.json", "r") as fin:
        settings = json.load(fin)

    #eliminate_unused_subcarrier("./CSI Collector/record/20220718171953_8CCE4E9A045C_mp.csv")
    #clip("./CSI Collector/record/20220718171953_8CCE4E9A045C_mp.csv", 230, 260, "walk_aside")
    fs = 1 / settings["CSI_sampling_period"]
    b, a = get_butterworth_LPF(fs*0.3, fs)
    clip(fpath, 200, 400, "apple")