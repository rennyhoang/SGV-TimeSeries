from flask import Flask, render_template, request
from dateutil.parser import parse
import csv
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import h5py
import sys

ts_file = './data/sentinel_dvert_timeseries_median_filtered.h5'
disp_file = './data/ifgram_recon_displacement.h5'
mask_file = './data/mask_low_elevation_high_tempCoh.h5'
well_file = './data/well_SanGabriel.txt'

np.set_printoptions(threshold=sys.maxsize)


def calculate_storage_loss(dset):
    # TODO:
    # calculate total displacement at every time
    # interpolate over the area
    # integrate interpolation with respect to area
    # find area in terms of acre feet
    print(len(dset), len(dset[0]))
    for idx, curr in enumerate(dset[:1]):
        # disp_idx1_idx2 = dset_ts[idx2,] - dset_ts[idx1,]
        diff = dset[idx,] - dset[idx - 1,]
        print(diff)


def averagetimeseries(dset, dates):
    # TODO
    # iterate over all the times
    res = []
    for time in dset:
        # average displacement over all x, y
        total = 0
        n = 0
        for lat in time:
            for measurement in lat:
                if np.isnan(measurement):
                    continue
                total += measurement
                n += 1
        total /= n
        res.append(total)
    return np.array(res)


def readtimeseries(filepath):
    # read the data
    f = h5py.File(filepath, 'r')
    dset = f['timeseries']
    dset = np.array(dset)
    dates = [i.decode('utf8') for i in f['date'][:]]
    dates = pd.to_datetime(dates)
    f.close()
    return dset, dates


def readmask(filepath):
    # read the data
    f = h5py.File(filepath, 'r')
    dset = f['mask']
    dset = np.array(dset)
    f.close()
    return dset


def main():
    dset_ts, dates = readtimeseries(ts_file)
    dset_mask = readmask(mask_file)
    dset_ts *= dset_mask
    calculate_storage_loss(dset_ts)
    averaged_dset = averagetimeseries(dset_ts, dates)

    # parse well data
    rows = []
    with open("data/well_SanGabriel.txt", "r") as csvfile:
        csv_reader = csv.reader(csvfile)
        fields = next(csv_reader)
        for row in csv_reader:
            date = parse(row[0]).strftime('%Y-%m-%d')
            year = int(date[:4])
            measurement = row[1]
            if year >= 2015:
                rows.append((date, measurement))
            well_dates = np.array([row[0] for row in rows])
            well_dates = pd.to_datetime(well_dates)
            measurements = np.array([float(row[1]) for row in rows])

    fig, ax1 = plt.subplots()
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Displacement [m]')
    ax1.scatter(dates, averaged_dset, c='k')
    ax2 = ax1.twinx()
    ax2.set_ylabel('Measurement [mm]')
    ax2.scatter(well_dates, measurements, c='c')
    fig.tight_layout()
    plot_filename = "static/average-plot.png"
    fig.savefig(plot_filename, bbox_inches='tight')


if __name__ == '__main__':
    main()
