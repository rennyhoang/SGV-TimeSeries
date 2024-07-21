import csv
import sys

import h5py
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy.optimize

ts_file = "./data/sentinel_dvert_timeseries_median_filtered.h5"
disp_file = "./data/ifgram_recon_displacement.h5"
mask_file = "./data/mask_low_elevation_high_tempCoh.h5"
well_file = "./data/well_SanGabriel.txt"

np.set_printoptions(threshold=np.inf)


def latlon2yx(lat, lon):
    # 33.50 34.4 -118.75 -117.25
    lat0 = 34.4
    lon0 = -118.75
    step = 0.002277778

    y = -int((lat - lat0) / step)
    x = int((lon - lon0) / step)

    return y, x


def regression():
    dset_ts, dates = readtimeseries(ts_file)
    deltas = []
    for date in dates:
        diff = date - dates[0]
        deltas.append(float(diff.days))
    deltas = deltas[:150]
    res = [
        [[0, 0, 0] for _ in range(len(dset_ts[0][0]))] for _ in range(len(dset_ts[0]))
    ]

    def my_equation(t, b1, b2, b4):
        return (
            b2 * t
            + b4 * np.sin((2 * np.pi * t) / 365)
            # + b5 * np.cos((2 * np.pi * t) / 365)
            + b1
        )

    for y in range(len(dset_ts[0])):
        for x in range(len(dset_ts[0][0])):
            ts_yx = dset_ts[:, y, x]
            ts_yx = ts_yx[:150]
            if np.isnan(ts_yx[0]):
                continue
            popt, pcov = scipy.optimize.curve_fit(
                my_equation, np.array(deltas), np.array(ts_yx)
            )
            b1, b2, b4 = popt
            res[y][x] = [b1, b2, b4]

    return res


def readtimeseries(filepath):
    # read the data
    f = h5py.File(filepath, "r")
    dset = f["timeseries"]
    dset = np.array(dset)
    dates = [i.decode("utf8") for i in f["date"][:]]
    dates = pd.to_datetime(dates)
    f.close()
    return dset, dates


def readmask(filepath):
    # read the data
    f = h5py.File(filepath, "r")
    dset = f["mask"]
    dset = np.array(dset)
    f.close()
    return dset


def main():
    print(regression())


if __name__ == "__main__":
    main()
