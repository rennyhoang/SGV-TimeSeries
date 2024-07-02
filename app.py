from flask import Flask, render_template, request
from dateutil.parser import parse
import csv
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import h5py

app = Flask(__name__)

ts_file = './data/sentinel_dvert_timeseries_median_filtered.h5'
disp_file = './data/ifgram_recon_displacement.h5'
mask_file = './data/mask_low_elevation_high_tempCoh.h5'
well_file = './data/well_SanGabriel.txt'
plot_filename = None
snapshot_filename = None
coordinates = ""


def averagetimeseries(dset, dates):
    # iterate over all the times
    res = []
    for time in dset:
        # average displacement over all x, y
        total = 0
        n = 0
        for lat in time:
            for measurement in lat:
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


def readdisplacement(filepath):
    # read the data
    f = h5py.File(filepath, 'r')
    dset = f['velocity']
    dset = np.array(dset)
    f.close()
    return dset


def readmask(filepath):
    # read the data
    f = h5py.File(filepath, 'r')
    dset = f['mask']
    dset = np.array(dset)
    f.close()
    return dset


def latlon2yx(lat, lon):
    # 33.50 34.4 -118.75 -117.25
    lat0 = 34.4
    lon0 = -118.75
    step = 0.002277778

    y = -int((lat - lat0) / step)
    x = int((lon - lon0) / step)

    return y, x


@app.route('/', methods=['GET', 'POST'])
def index():  # put application's code here
    global plot_filename, snapshot_filename, coordinates

    if request.method == 'POST':
        if 'latitude' in request.form:
            # parse ts data
            dset_ts, dates = readtimeseries(ts_file)
            lat = float(request.form['latitude'])
            lon = float(request.form['longitude'])
            y, x = latlon2yx(lat, lon)
            coordinates = "Pixel location: " + str(y) + ", " + str(x)
            ts_yx = dset_ts[:, y, x]
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

            # plot well/ts data
            fig, ax1 = plt.subplots()
            ax1.set_xlabel('Date')
            ax1.set_ylabel('Displacement [m]')
            ax1.scatter(dates, ts_yx, c='k')
            ax2 = ax1.twinx()
            ax2.set_ylabel('Measurement [mm]')
            ax2.scatter(well_dates, measurements, c='c')
            fig.tight_layout()
            plot_filename = "static/plot.png"
            fig.savefig(plot_filename, bbox_inches='tight')

            return render_template('index.html',
                                   plot_filename=plot_filename,
                                   snapshot_filename=snapshot_filename,
                                   coordinates=coordinates)

        elif 'date1' in request.form:
            dset_ts, dates = readtimeseries(ts_file)
            print(dates)
            dset_mask = readmask(mask_file)
            date1 = str(request.form['date1'])
            date2 = str(request.form['date2'])
            idx1 = dates.get_loc(date1)
            idx2 = dates.get_loc(date2)
            disp_idx1_idx2 = dset_ts[idx2,] - dset_ts[idx1,]
            plt.figure()
            plt.imshow(disp_idx1_idx2 * dset_mask, cmap='jet', vmin=-0.05, vmax=0.05)
            snapshot_filename = "static/snapshot.png"
            plt.savefig(snapshot_filename, bbox_inches='tight')

            return render_template('index.html',
                                   plot_filename=plot_filename,
                                   snapshot_filename=snapshot_filename,
                                   coordinates=coordinates)

    # Render the form
    return render_template('index.html',
                           plot_filename=None,
                           snapshot_filename=None,
                           coordinates='')


if __name__ == '__main__':
    app.run(debug=True)
