import csv
import numpy

def eliminate_unused_subcarrier(fpath):
    arr = []
    with open(fpath, "r", encoding="utf8") as fin:
        for row in csv.reader(fin):
            arr.append(row)

    #record unused column
    tr_arr = numpy.array(arr).transpose()
    unused_idxes = []
    for i in range(tr_arr.shape[0]):
        if (len(set(tr_arr[i]))==2):
            unused_idxes.append(i)

    #eliminate
    l = []
    for i in range(len(unused_idxes)):
        if ((unused_idxes[i]%2==0 and unused_idxes[i]-1 not in unused_idxes) 
        or (unused_idxes[i]%2==1 and unused_idxes[i]+1 not in unused_idxes)):
            l.append(i)
            continue
    for i in range(len(l)):
        unused_idxes.pop(l[i]-i)

    tr_arr = numpy.delete(tr_arr, unused_idxes, axis=0)

    #save file
    arr = (tr_arr.transpose()).tolist()
    with open(fpath, "w", encoding="utf8", newline="") as fout:
        writer = csv.writer(fout)
        writer.writerows(arr)
    print(f"eliminated unused subcarriers: {[int(idx/2) for idx in unused_idxes if idx%2==0]} for {fpath}")

def get_sampling_period(fpath):
    arr = []
    with open(fpath, "r", encoding="utf8") as fin:
        for row in csv.reader(fin):
            try:
                arr.append(float(row[0]))
            except:
                continue
    diff = []
    for i in range(2, len(arr)):
        d = arr[i]-arr[i-1]
        if (d>0 and d<1):
            diff.append(d)

    #return min & avg
    return (min(diff), sum(diff)/len(diff))
    

def interpolate(fpath, sampling_period):
    arr = []
    with open(fpath, "r", encoding="utf8") as fin:
        for row in csv.reader(fin):
            arr.append(row)

    #determine which row needs interpolation
    interp_idx = []
    for i in range(2, len(arr)):
        interval = float(arr[i][0]) - float(arr[i-1][0])
        if (interval==0):
            continue
        if (sampling_period/interval>=0.4 and sampling_period/interval<=0.6):
            interp_idx.append(i)

    #interpolate
    for i in range(len(interp_idx)):
        row = []
        for j in range(len(arr[0])):
            row.append((float(arr[interp_idx[i]+i][j])+float(arr[interp_idx[i]+i-1][j]))/2)
        arr.insert(interp_idx[i]+i, row)
    
    #save file
    with open(fpath, "w", encoding="utf8", newline="") as fout:
        writer = csv.writer(fout)
        writer.writerows(arr)
    print(f"interpolated {fpath} with sampling period: {sampling_period}(sec)")

def clip(fpath, start=None, end=None, motion=None):
    arr = []
    with open(fpath, "r", encoding="utf8") as fin:
        for row in csv.reader(fin):
            arr.append(row)
    clipped_idxes = []

    #clip
    if (start==None and end==None):
        return
    elif (start!=None and end==None):
        for i in range(1, len(arr)):
            if (float(arr[i][0])<start):
                clipped_idxes.append(i)
    elif (start==None and end!=None):
        for i in range(1, len(arr)):
            if (float(arr[i][0])>end):
                clipped_idxes.append(i)
    else:
        for i in range(1, len(arr)):
            if (float(arr[i][0])<start or float(arr[i][0])>end):
                clipped_idxes.append(i)
    
    for i in range(len(clipped_idxes)):
        arr.pop(clipped_idxes[i]-i)
    
    #save file
    if (motion!=None):
        fpath = fpath[:-4] + f"_{motion}.csv"
    with open(fpath, "w", encoding="utf8", newline="") as fout:
        writer = csv.writer(fout)
        writer.writerows(arr)
    print(f"clipped record from {arr[1][0]} to {arr[-1][0]} and saved it to {fpath}")

if __name__=="__main__":
    fpath = "./CSI Collector/record/20220718171953_8CCE4E9A045C_mp.csv"
    #eliminate_unused_subcarrier("./CSI Collector/record/20220718171953_8CCE4E9A045C_mp.csv")
    #clip("./CSI Collector/record/20220718171953_8CCE4E9A045C_mp.csv", 230, 260, "walk_aside")