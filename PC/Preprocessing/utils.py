import json
import warnings
import numpy
import matplotlib.pyplot as plt
import pandas
from pandas.errors import PerformanceWarning
from scipy.signal import butter, lfilter

warnings.simplefilter(action="ignore", category=PerformanceWarning)

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
    fin = pandas.read_csv(fpath)
    start_idx = (batch_num-1) * batch_size
    end_idx = batch_num * batch_size
    signals = pandas.DataFrame()

    #search & collect data
    for n in subcarriers:
        if ("subcarrier"+str(n).rjust(2, "0")+f"_{part}" in fin.keys()):
            signals["subcarrier"+str(n).rjust(2, "0")+f"_{part}"] = fin["subcarrier"+str(n).rjust(2, "0")+f"_{part}"].iloc[start_idx:end_idx]

    #plot
    plt.figure()
    plt.xlabel("packets")
    plt.ylabel(part)
    plt.ylim([-100, 100])
    for k in signals.keys():
        signals[k].plot(linewidth=0.2)
    plt.legend()
    plt.show()

def get_butterworth_LPF(cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return b, a

def filtering(fpath, b, a):
    fin = pandas.read_csv(fpath)
    result = pandas.DataFrame()

    #filtering
    for key in fin.keys():
        if (key[0:10]=="subcarrier"):
            result[key] = lfilter(b, a, fin[key])
        else:
            result[key] = fin[key]
    
    #save file
    result.to_csv(fpath, index=False)

if __name__=="__main__":
    fpath = "./CSI Collector/record/20220718171953_8CCE4E9A045C_mp.csv"
    with open("./Preprocessing/settings.json", "r") as fin:
        settings = json.load(fin)

    fs = 1 / settings["CSI_sampling_period"]
    b, a = get_butterworth_LPF(fs*0.3, fs, order=20)
    
    plot_CSI_signal(fpath)
    filtering(fpath, b, a)
    plot_CSI_signal(fpath)