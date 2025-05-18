import numpy as np
import xarray as xr
import pandas as pd
import vigiclimm_indicators.weather_indicators.degree_days as dd
import pytest

base = 6
cutoff_val = 30


class TestDegreeDay():

    @pytest.fixture(autouse=True)
    def setup_data(self, shared_datadir):
        self.df = pd.read_csv(shared_datadir / 'degree_day.csv')
        self.ds = xr.open_dataset(shared_datadir / 'degree_day.nc')

    def test_nocutoff_cold(self):
        exp = self.df['tbase_cold']
        obs = dd._no_cutoff_degree_days_from_tmean(self.df.tmean, base, index="cold")
        np.testing.assert_almost_equal(obs.values, exp.values)

    def test_nocutoff_hot(self):
        exp = self.df['tbase_hot']
        obs = dd._no_cutoff_degree_days_from_tmean(self.df.tmean, base, index="hot")
        np.testing.assert_almost_equal(obs.values, exp.values)

    def test_nocutoff_xarray(self):
        exp = self.ds['tbase_hot']
        obs = dd._no_cutoff_degree_days_from_tmean(self.ds.tmean, base, index="hot")
        np.testing.assert_almost_equal(obs.values, exp.values)

    def test_vertcutoff_cold(self):
        exp = self.df['tbase_vert_cold']
        obs = dd._cutoff_vertical_degree_days_from_tmean(self.df.tmean, base, cutoff_val, index="cold")
        np.testing.assert_almost_equal(obs.values, exp.values)

    def test_vertcutoff_hot(self):
        exp = self.df['tbase_vert_hot']
        obs = dd._cutoff_vertical_degree_days_from_tmean(self.df.tmean, base, cutoff_val, index="hot")
        np.testing.assert_almost_equal(obs.values, exp.values)

    def test_vertcutoff_xarray(self):
        exp = self.ds['tbase_vert_hot']
        obs = dd._cutoff_vertical_degree_days_from_tmean(self.ds.tmean, base, cutoff_val, index="hot")
        np.testing.assert_almost_equal(obs.values, exp.values)

    def test_horicutoff_cold(self):
        exp = self.df['tbase_hor_cold']
        obs = dd._cutoff_horizontal_degree_days_from_tmean(self.df.tmean, base, cutoff_val, index="cold")
        np.testing.assert_almost_equal(obs.values, exp.values)

    def test_horicutoff_hot(self):
        exp = self.df['tbase_hor_hot']
        obs = dd._cutoff_horizontal_degree_days_from_tmean(self.df.tmean, base, cutoff_val, index="hot")
        np.testing.assert_almost_equal(obs.values, exp.values)

    def test_horicutoff_xarray(self):
        exp = self.ds['tbase_hor_hot']
        obs = dd._cutoff_horizontal_degree_days_from_tmean(self.ds.tmean, base, cutoff_val, index="hot")
        np.testing.assert_almost_equal(obs.values, exp.values)

    def test_degree_days_tmintmax(self):
        exp = self.df['tbase_hor_hot']
        obs = dd.degree_days(base=base,
                             tmin=self.df.tmin,
                             tmax=self.df.tmax,
                             tmean=None,
                             index="hot",
                             cutoff_method="h",
                             cutoff_val=cutoff_val
                             )
        np.testing.assert_almost_equal(obs.values, exp.values)

    def test_degree_days_tmintmax_xarray(self):
        exp = self.ds['tbase_hor_hot']
        obs = dd.degree_days(base=base,
                             tmin=self.ds.tmin,
                             tmax=self.ds.tmax,
                             tmean=None,
                             index="hot",
                             cutoff_method="h",
                             cutoff_val=cutoff_val
                             )
        np.testing.assert_almost_equal(obs.values, exp.values)

    def test_degree_days_tmean(self):
        exp = self.df['tbase_hor_hot']
        obs = dd.degree_days(base=base,
                             tmin=None,
                             tmax=None,
                             tmean=self.df.tmean,
                             index="hot",
                             cutoff_method="h",
                             cutoff_val=cutoff_val
                             )
        np.testing.assert_almost_equal(obs.values, exp.values)

    def test_degree_days_tmean_xarray(self):
        exp = self.ds['tbase_hor_hot']
        obs = dd.degree_days(base=base,
                             tmin=None,
                             tmax=None,
                             tmean=self.ds.tmean,
                             index="hot",
                             cutoff_method="h",
                             cutoff_val=cutoff_val
                             )
        np.testing.assert_almost_equal(obs.values, exp.values)


class Spatialtest():
    time = pd.date_range("2021-01-01", "2021-01-15")
    lat = range(0, 6)
    lon = range(0, 6)
    tmin = np.ones((len(lat), len(lon), time.size)) * np.arange(time.size)
    tmax = np.ones((len(lat), len(lon), time.size)) * np.arange(time.size)+5
    ones = np.ones((len(lat), len(lon), time.size))

    ds = xr.Dataset(
        data_vars=dict(
            tmin=(["lat", "lon", "time"], tmin),
            tmax=(["lat", "lon", "time"], tmax),

        ),
        coords=dict(lat=lat, lon=lon, time=time),
    )

    def test_degreeday_spatial_xarray(self):
        data = self.ones * [0., 0., 0., 0., 0.5, 1.5, 2.5,
                            3.5, 4.5, 5.5, 6.5, 7.5, 8.5, 9.5, 10.5]
        exp = xr.DataArray(data=data, name="dd",
                           coords=self.ds.coords, dims=["lat", "lon", "time"])

        obs = dd.degree_days(base=base,
                             tmin=self.ds["tmin"],
                             tmax=self.ds["tmax"],
                             tmean=None,
                             index="hot",
                             cutoff_method="h",
                             cutoff_val=cutoff_val
                             )

        xr.testing.assert_allclose(obs, exp)
