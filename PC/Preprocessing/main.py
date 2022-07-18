import os
from utils import *

if __name__=="__main__":
    for f in os.listdir("./PC/CSI Collector/record"):
        if (f.endswith(".csv")):
            eliminate_unused_subcarrier(f"./PC/CSI Collector/record/{f}")