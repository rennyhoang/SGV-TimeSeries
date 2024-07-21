import csv
import sys

import h5py
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from dateutil.parser import parse
from matplotlib.ticker import FormatStrFormatter, StrMethodFormatter

ts_file = "./data/sentinel_dvert_timeseries_median_filtered.h5"
disp_file = "./data/ifgram_recon_displacement.h5"
mask_file = "./data/mask_low_elevation_high_tempCoh.h5"
well_file = "./data/well_SanGabriel.txt"

np.set_printoptions(threshold=np.inf)


def calculate_storage_loss(dset, idx1, idx2):
    meters_to_acrefeet = 350656.168
    diff = dset[idx2,] - dset[idx1,]

    total = 0
    n = 0
    for lat in diff[115:126]:
        for measurement in lat[260:271]:
            if np.isnan(measurement):
                continue
            total += measurement
            if measurement < 0:
                print("hooray!")
            n += 1
    avg = total / n
    total_disp = avg * meters_to_acrefeet

    return total_disp


def averagetimeseries(dset, dates):
    # iterate over all the times
    res = []
    for time in dset:
        # average displacement over all x, y
        total = 0
        n = 0
        for lat in time[115:126]:
            for measurement in lat[260:271]:
                if np.isnan(measurement):
                    continue
                total += measurement
                n += 1
        total /= n if n != 0 else 1
        res.append(total)
    return np.array(res)


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
    dset_ts, dates = readtimeseries(ts_file)
    dset_mask = readmask(mask_file)
    dset_ts *= dset_mask
    print(dates[14], dates[42])
    print(calculate_storage_loss(dset_ts, 14, 42))
    averaged_dset = averagetimeseries(dset_ts, dates)

    # parse well data
    rows = []
    with open("data/well_SanGabriel.txt", "r") as csvfile:
        csv_reader = csv.reader(csvfile)
        fields = next(csv_reader)
        for row in csv_reader:
            date = parse(row[0]).strftime("%Y-%m-%d")
            year = int(date[:4])
            measurement = row[1]
            if year >= 2015:
                rows.append((date, measurement))
            well_dates = np.array([row[0] for row in rows])
            well_dates = pd.to_datetime(well_dates)
            measurements = np.array([float(row[1]) for row in rows])

    plt.figure(figsize=(20, 5))
    fig, ax1 = plt.subplots()
    fig.set_figwidth(10)
    ax1.set_xlabel("Time [y]", labelpad=10)
    ax1.set_ylabel("InSAR Displacement [m]", labelpad=0)
    ax1.set_ylim(-0.01, 0.02)
    ax2 = ax1.twinx()
    ax2.set_ylabel("Well Measurement [mm]", labelpad=10)

    water_prod_dates = pd.to_datetime(
        [
            "2015-10-1",
            "2016-10-1",
            "2017-10-1",
            "2018-10-1",
            "2019-10-1",
            "2020-10-1",
            "2021-10-1",
            "2022-10-1",
        ]
    )
    water_prod_vals = [
        182826.49,
        197243.28,
        209499.70,
        190156.12,
        192583.66,
        207821.52,
        186184.04,
        168360.09,
    ]

    ax3 = ax1.twinx()
    ax3.spines.right.set_position(("axes", 1.2))
    ax3.set_ylabel("Water Production [acre/feet]", labelpad=10)
    ax3.set_ylim(150000, 300000)
    ax3.yaxis.set_major_formatter(StrMethodFormatter("{x:,}"))
    ax1.set_zorder(ax2.get_zorder() + 1)
    ax1.patch.set_visible(False)
    ax1.scatter(dates, averaged_dset, c="k", s=4, label="InSAR", zorder=10)
    line3 = ax3.bar(
        water_prod_dates,
        water_prod_vals,
        width=360,
        zorder=1000,
        align="edge",
        color="#ECE27D80",
    )
    ax2.plot(
        well_dates,
        measurements,
        c="b",
        label="Well Data",
        linestyle="dashed",
        zorder=11,
    )

    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()

    lines = lines_1 + lines_2
    labels = labels_1 + labels_2

    ax1.legend(lines + [line3], labels +
               ["Water Production"], loc=0, frameon=False)

    fig.tight_layout()
    plot_filename = "static/new-average-plot.png"
    fig.savefig(plot_filename, bbox_inches="tight")


if __name__ == "__main__":
    main()
