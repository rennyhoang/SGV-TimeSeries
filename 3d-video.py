import h5py
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import animation

ts_file = "./data/sentinel_dvert_timeseries_median_filtered.h5"
disp_file = "./data/ifgram_recon_displacement.h5"
mask_file = "./data/mask_low_elevation_high_tempCoh.h5"
well_file = "./data/well_SanGabriel.txt"
# dates = [14, 28, 42, 62, 89, 118, 142, 164, 191, 223, 252, 284, 313, 336, 350, 366, 381]

np.set_printoptions(threshold=np.inf)


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
    dset_mask = np.array([x[200:400] for x in dset_mask[50:200]])
    ims = []
    fig, ax = plt.subplots(subplot_kw={"projection": "3d"})
    for i in range(len(dates) - 1):
        idx = dates.get_loc(dates[i + 1])
        disp = dset_ts[idx,] - dset_ts[dates.get_loc(dates[0]),]
        disp = np.array([x[200:400] for x in disp[50:200]])

        Z = disp * dset_mask
        x = np.arange(Z.shape[1])
        np.flip(x)
        y = np.arange(Z.shape[0])
        X, Y = np.meshgrid(x, y)

        im = ax.plot_surface(X, Y, Z, cmap="jet", vmin=-0.05, vmax=0.05)
        ims.append([im])
    ani = animation.ArtistAnimation(
        fig, ims, interval=100, blit=True, repeat_delay=100)
    ani.save("movie.mp4")


if __name__ == "__main__":
    main()
