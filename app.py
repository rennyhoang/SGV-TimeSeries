from flask import Flask, render_template, request
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import h5py

app = Flask(__name__)

ts_file = './data/sentinel_dvert_timeseries_median_filtered.h5'
disp_file = './data/ifgram_recon_displacement.h5'
mask_file = './data/mask_low_elevation_high_tempCoh.h5'
plot_filename = None
snapshot_filename = None


def readtimeseries(filepath):
    # read the data
    f = h5py.File(filepath, 'r')
    dset = f['timeseries']
    dset = np.array(dset)
    dates = [i.decode('utf8') for i in f['date'][:]]
    dates = pd.to_datetime(dates)
    print(dates)
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
    lat0 = 34.1
    lon0 = -118
    step = 0.02277778

    y = -int((lat - lat0) / step)
    x = int((lon - lon0) / step)

    return y, x


@app.route('/', methods=['GET', 'POST'])
def index():  # put application's code here
    global plot_filename, snapshot_filename

    if request.method == 'POST':
        if 'latitude' in request.form:
            dset_ts, dates = readtimeseries(ts_file)
            lat = float(request.form['latitude'])
            lon = float(request.form['longitude'])
            y, x = latlon2yx(lat, lon)
            # print('Pixel location: ', y, x)
            ts_yx = dset_ts[:, y, x]
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.scatter(dates, ts_yx, c='k', label='Sentinel-1')
            ax.set_xlabel('Date')
            ax.set_ylabel('Displacement [m]')
            plot_filename = "static/plot.png"
            fig.savefig(plot_filename, bbox_inches='tight')

            return render_template('index.html',
                                   plot_filename=plot_filename,
                                   snapshot_filename=snapshot_filename)

        elif 'date1' in request.form:
            dset_ts, dates = readtimeseries(ts_file)
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
                                   snapshot_filename=snapshot_filename)

    # Render the form
    return render_template('index.html',
                           plot_filename=None,
                           snapshot_filename=None)


if __name__ == '__main__':
    app.run(debug=True)
