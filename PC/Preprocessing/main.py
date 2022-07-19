import os
import json
from utils import *

if __name__=="__main__":

    with open("./Preprocessing/settings.json", "r") as fin:
        settings = json.load(fin)

    for f in os.listdir("./CSI Collector/record"):
        if (f.endswith(".csv")):
            eliminate_unused_subcarrier(f"./CSI Collector/record/{f}")
            interpolate(f"./CSI Collector/record/{f}", settings["CSI_sampling_period"])