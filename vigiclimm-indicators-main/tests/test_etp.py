import numpy as np
import pandas as pd
from vigiclimm_indicators.weather_indicators import etp


class TestFao56PenmanMonteith:
    """
    See this website for all relevant values
    http://www.fao.org/3/x0490e/x0490e08.htm#eto%20calculated%20with%20different%20time%20steps
    """

    net_rad = 13.28  # MJ m-2 day-1
    ws = 2.078  # m s-1
    t = 16.9  # degC
    svp = 1.997  # kPa
    avp = 1.409  # kPa
    delta_svp = 0.122  # kPa degC-1
    psy = 0.0666  # kPa degC-1
    elevation = 100  # m
    tmax = 21.5  # degC
    tmin = 12.3  # degC
    wind10m = 2.778  # m s-1
    rhmax = 84  # %
    rhmin = 63  # %

    n_lat = 3
    n_lon = 3
    n_time = 3
    n_total = n_lat * n_lon * n_time
    lats = pd.Index(np.linspace(43, 45, n_lat), name="lat")
    lons = pd.Index(np.linspace(1, 3, n_lon), name="lon")
    times = pd.date_range("20210401", freq="D", periods=n_time, name="time")
    index = pd.MultiIndex.from_product([lats, lons, times])
    df = pd.DataFrame(
        {
            "elevation": [elevation] * n_total,  # m
            "tmax": [tmax] * n_total,  # ˚C
            "tmin": [tmin] * n_total,  # ˚C
            "rhmax": [rhmax] * n_total,  # %
            "rhmin": [rhmin] * n_total,  # %
            "wind10m": [wind10m] * n_total,  # m/s
            "net_rad": [net_rad] * n_total,  # MJ m-2 day-1
            "ws": [ws] * n_total,  # m/s
            "t": [t] * n_total,  # degC
            "svp": [svp] * n_total,  # kPa
            "avp": [avp] * n_total,  # kPa
            "delta_svp": [delta_svp] * n_total,  # kPa degC-1
            "psy": [psy] * n_total,  # kPa degC-1
        },
        index=index,
    )

    def test_single_values(self):
        result = etp.fao56_penman_monteith(
            net_rad=self.net_rad,
            t=self.t,
            ws=self.ws,
            svp=self.svp,
            avp=self.avp,
            delta_svp=self.delta_svp,
            psy=self.psy,
        )
        np.testing.assert_almost_equal(result, 3.8747182802519218)

    def test_numpy_arrays(self):
        df = self.df.iloc[:3]
        result = etp.fao56_penman_monteith(
            net_rad=df["net_rad"].values,
            t=df["t"].values,
            ws=df["ws"].values,
            svp=df["svp"].values,
            avp=df["avp"].values,
            delta_svp=df["delta_svp"].values,
            psy=df["psy"].values,
        )
        np.testing.assert_almost_equal(result, np.array([3.8747182802519218, 3.8747182802519218, 3.8747182802519218]))

    def test_numpy_from_FAO_reference(self):

        net_rad = np.array(
            [
                10.42845478,
                11.13644742,
                11.40253126,
                10.62931851,
                8.6849771,
                7.63433474,
                7.65048804,
                8.01958468,
                8.34868737,
                8.82691997,
                9.70871935,
                10.139698,
            ]
        )
        ws = np.array(
            [
                0.90277778,
                0.79861111,
                0.90277778,
                0.79861111,
                0.79861111,
                0.79861111,
                0.90277778,
                0.90277778,
                1.2037037,
                1.50462963,
                1.2037037,
                1.09953704,
            ]
        )
        t = np.array([26.2, 26.5, 26.8, 26.6, 25.3, 22.85, 21.35, 21.95, 23.5, 25.25, 25.85, 26.05])
        svp = np.array(
            [
                3.46115644,
                3.5377435,
                3.60036478,
                3.55071033,
                3.27897025,
                2.84352174,
                2.59967115,
                2.68399025,
                2.93686182,
                3.25275899,
                3.37309556,
                3.41916102,
            ]
        )
        delta_svp = np.array(
            [
                0.20075516,
                0.20387302,
                0.20703153,
                0.20492132,
                0.19164126,
                0.16857813,
                0.15564952,
                0.16071661,
                0.17445562,
                0.19114532,
                0.19716846,
                0.19921133,
            ]
        )
        psy = 0.06690424258407811
        avp = np.array(
            [
                2.80353672,
                2.90094967,
                2.88029183,
                2.91158247,
                2.75433501,
                2.30325261,
                2.0277435,
                2.0935124,
                2.29075222,
                2.5696796,
                2.69847645,
                2.80371204,
            ]
        )

        result = etp.fao56_penman_monteith(
            net_rad=net_rad, t=t, ws=ws, svp=svp, avp=avp, delta_svp=delta_svp, psy=psy
        )
        expected = np.array([3.4, 3.7, 3.8, 3.5, 2.9, 2.6, 2.6, 2.6, 2.8, 3.1, 3.3, 3.4])
        np.testing.assert_almost_equal(result, expected, decimal=0)
