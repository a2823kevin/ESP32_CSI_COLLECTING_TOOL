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
    print(unused_idxes)
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
    #eliminate_unused_subcarrier("./CSI Collector/record/20220703193923_8CCE4E9A045C.csv")
    clip("./CSI Collector/record/20220703193923_8CCE4E9A045C.csv", 230, 260, "walk_aside")