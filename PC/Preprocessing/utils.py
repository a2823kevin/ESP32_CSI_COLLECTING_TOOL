import csv
import numpy

def eliminate_unused_subcarrier(fpath):
    arr = []
    with open(fpath, "r", encoding="utf8") as fin:
        for row in csv.reader(fin):
            arr.append(numpy.array(row))

    #record unused column
    tr_arr = numpy.array(arr).transpose()
    unused_idxes = []
    for i in range(tr_arr.shape[0]):
        if (len(set(tr_arr[i]))==2):
            unused_idxes.append(i)

    #eliminate
    for i in range(len(unused_idxes)):
        if (unused_idxes[i]%2==0 and unused_idxes[i]-1 not in unused_idxes):
            unused_idxes.pop(i)
            continue
        elif (unused_idxes[i]%2==1 and unused_idxes[i]+1 not in unused_idxes):
            unused_idxes.pop(i)
            continue
    tr_arr = numpy.delete(tr_arr, unused_idxes, axis=0)

    #save file
    arr = (tr_arr.transpose()).tolist()
    with open(fpath, "w", encoding="utf8", newline="") as fout:
        writer = csv.writer(fout, )
        writer.writerows(arr)
    print(f"eliminated unused subcarriers: {[int(idx/2) for idx in unused_idxes if idx%2==0]} for {fpath}")

if __name__=="__main__":
    eliminate_unused_subcarrier("./CSI Collector/record/20220703163553_8CCE4E9A045C.csv")