import os
from utils import *

if __name__=="__main__":
    for f in os.listdir("./CSI Collector/record"):
        if (f.endswith(".csv")):
            eliminate_unused_subcarrier(f"./CSI Collector/record/{f}")