import h5py
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy.optimize

ts_file = "./data/sentinel_dvert_timeseries_median_filtered.h5"
disp_file = "./data/ifgram_recon_displacement.h5"
mask_file = "./data/mask_low_elevation_high_tempCoh.h5"
well_file = "./data/well_SanGabriel.txt"
years = [14, 42, 89, 142, 191, 252, 313, 350, 381]
production_by_year = [
    175917.29,
    189717.07,
    196978.75,
    179408.67,
    179671.99,
    197045.07,
    177006.71,
    163986.52,
]

np.set_printoptions(threshold=np.inf)


def yx2latlon(y, x):
    # 33.50 34.4 -118.75 -117.25
    lat0 = 34.4
    lon0 = -118.75
    step = 0.00277778

    lat = (-1 * y * step) + lat0
    lon = (x * step) + lon0

    return lat, lon


def latlon2yx(lat, lon):
    # 33.50 34.4 -118.75 -117.25
    lat0 = 34.4
    lon0 = -118.75
    step = 0.00277778

    y = -int((lat - lat0) / step)
    x = int((lon - lon0) / step)

    return y, x


def regression(initial_date, final_date):
    dset_ts, dates = readtimeseries(ts_file)
    dset_mask = readmask(mask_file)
    dset_ts *= dset_mask
    deltas = []
    for date in dates:
        diff = date - dates[0]
        deltas.append(float(diff.days))
    deltas = deltas[initial_date:final_date]
    res = [
        [[0, 0, 0, 0] for _ in range(len(dset_ts[0][0]))]
        for _ in range(len(dset_ts[0]))
    ]

    def my_equation(t, b1, b2, b4, b5):
        return (
            b2 * t
            + b4 * np.sin((2 * np.pi * t) / 365)
            + b5 * np.cos((2 * np.pi * t) / 365)
            + b1
        )

    for y in range(len(dset_ts[0])):
        for x in range(len(dset_ts[0][0])):
            ts_yx = dset_ts[:, y, x]
            ts_yx = ts_yx[initial_date:final_date]
            if np.isnan(ts_yx[0]):
                continue
            popt, pcov = scipy.optimize.curve_fit(
                my_equation, np.array(deltas), np.array(ts_yx)
            )
            b1, b2, b4, b5 = popt
            res[y][x] = [b1, b2, b4, b5]

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
    # plot the regression equation
    dset_ts, dates = readtimeseries(ts_file)
    dset_mask = readmask(mask_file)
    dset_ts *= dset_mask
    annual_storage_loss = []
    for year in range(1, len(years)):
        equations = regression(years[year - 1], years[year])
        total_storage_loss = 0
        for y in range(len(dset_ts[0])):
            for x in range(len(dset_ts[0][0])):
                if equations[y][x] == [0, 0, 0, 0]:
                    continue
                else:
                    b1, b2, b4, b5 = equations[y][x]
                    linear_component = b2
                    # m/day * 365 day/year * 3.28 ft/m * 22.239 acre/90,000 m^2
                    point_storage_loss = (
                        linear_component * 365 * 3.280839895 * 22.239484332
                    )
                    total_storage_loss += point_storage_loss
        annual_storage_loss.append(total_storage_loss)

    print(
        [
            annual_storage_loss[x] + production_by_year[x]
            for x in range(len(annual_storage_loss))
        ]
    )


if __name__ == "__main__":
    main()
