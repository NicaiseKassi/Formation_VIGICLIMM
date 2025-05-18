import pandas as pd
import numpy as np
import pytest
from vigiclimm_indicators.agro_indicators import agro_indicators as agro


@pytest.fixture
def df():

    # simulating a D+8 forecast
    tp_values = [0, 35, 5, 5.5, 7.5, 0, 1.5, 17.2]
    tmax_values = [35, 42, 35, 36, 33, 35, 34, 33.8]
    rhmean_values = [45, 40, 45, 42, 72, 55, 60, 55]
    rhmin_values = [20, 15, 20, 22, 21, 28, 30, 35]
    gust_values = [52, 35, 20, 34, 5, 8, 10, 12]
    cloud_cover_values = [15, 26, 23, 38, 56, 45, 89, 45]
    df = pd.DataFrame(
        {"tp": tp_values,
         "tmax": tmax_values,
         "rhmean": rhmean_values,
         "rhmin": rhmin_values,
         "gust": gust_values,
         "cloud_cover": cloud_cover_values,
         'time': pd.date_range('2024-01-01', freq='D', periods=8)}).set_index(['time'])
    return df


class TestDrying:

    def test_critical_condition(self, df):
        assert agro.drying(df.tp, df.tmax, df.rhmean, df.rhmin).iloc[2] == 0

    def test_ideal_condition(self, df):
        assert agro.drying(df.tp, df.tmax, df.rhmean, df.rhmin).iloc[0] == 2

    def test_intermediate_condition(self, df):
        assert agro.drying(df.tp, df.tmax, df.rhmean, df.rhmin).iloc[5] == 1


class TestLandPreparation:

    last_month_dry = pd.DataFrame(
        {"tp": np.zeros(30),
         'time': pd.date_range('2023-12-02', freq='D', periods=30)}).set_index(['time'])

    last_month_wet = pd.DataFrame(
        {"tp": np.ones(30) + 1,
         'time': pd.date_range('2023-12-02', freq='D', periods=30)}).set_index(['time'])

    def test_critical_condition(self, df):
        assert agro.land_preparation(self.last_month_dry.tp, df.tp, df.gust).iloc[0] == 0

    def test_ideal_condition(self, df):
        assert agro.land_preparation(self.last_month_wet.tp, df.tp, df.gust).iloc[2] == 2

    def test_intermediate_condition(self, df):
        assert agro.land_preparation(self.last_month_wet.tp, df.tp, df.gust).iloc[3] == 1


class TestHarvesting:

    last_month_dry = pd.DataFrame(
        {"tp": np.zeros(14),
         'time': pd.date_range('2023-12-18', freq='D', periods=14)}).set_index(['time'])

    last_month_wet = pd.DataFrame(
        {"tp": np.ones(14) + 1,
         'time': pd.date_range('2023-01-18', freq='D', periods=14)}).set_index(['time'])

    def test_critical_condition(self, df):
        assert agro.harvesting(self.last_month_wet.tp, df.tp, df.rhmean).iloc[0] == 0

    def test_ideal_condition(self, df):
        assert not agro.harvesting(self.last_month_dry.tp, df.tp, df.rhmean).iloc[3] == 2

    def test_intermediate_condition(self, df):
        assert agro.harvesting(self.last_month_dry.tp, df.tp, df.rhmean).iloc[5] == 1


class TestFertilization:

    last_month_wet = pd.DataFrame(
        {"tp": np.ones(14) + 1,
         'time': pd.date_range('2023-01-18', freq='D', periods=14)}).set_index(['time'])

    def test_critical_condition(self, df):
        assert agro.fertilization(self.last_month_wet.tp, df.tp, df.tmax, df.rhmean, df.gust).iloc[1] == 0

    def test_ideal_condition(self, df):
        assert agro.fertilization(self.last_month_wet.tp, df.tp, df.tmax, df.rhmean, df.gust).iloc[4] == 2

    def test_intermediate_condition(self, df):
        assert agro.fertilization(self.last_month_wet.tp, df.tp, df.tmax, df.rhmean, df.gust).iloc[6] == 1


class TestProtection:

    last_month_wet = pd.DataFrame(
        {"tp": np.ones(14) + 1,
         'time': pd.date_range('2023-01-18', freq='D', periods=14)}).set_index(['time'])

    def test_critical_condition(self, df):
        assert agro.protection(self.last_month_wet.tp, df.tp, df.tmax, df.gust, df.cloud_cover).iloc[0] == 0

    def test_ideal_condition(self, df):
        assert agro.protection(self.last_month_wet.tp, df.tp, df.tmax, df.gust, df.cloud_cover).iloc[4] == 2

    def test_intermediate_condition(self, df):
        assert agro.protection(self.last_month_wet.tp, df.tp, df.tmax, df.gust, df.cloud_cover).iloc[7] == 1


class TestSowing:

    last_month_dry = pd.DataFrame(
        {"tp": np.zeros(14),
         'time': pd.date_range('2023-12-18', freq='D', periods=14)}).set_index(['time'])

    def test_critical_condition(self, df):
        assert agro.sowing(self.last_month_dry.tp, df.tp, df.gust).iloc[3] == 0

    def test_ideal_condition(self, df):
        assert agro.sowing(self.last_month_dry.tp, df.tp, df.gust).iloc[6] == 2

    def test_intermediate_condition(self, df):
        assert agro.sowing(self.last_month_dry.tp, df.tp, df.gust).iloc[4] == 1


class TestIrrigation:

    last_month_dry = pd.DataFrame(
        {"tp": np.zeros(14),
         'time': pd.date_range('2023-12-18', freq='D', periods=14)}).set_index(['time'])

    tp_values = [0, 0, 0.5, 0.8, 0.1, 10.5, 3.1]
    etp_values = [10, 11, 8, 9.5, 7.5, 6.8, 4.5]
    df = pd.DataFrame(
        {"tp": tp_values,
         "etp": etp_values,
         'time': pd.date_range('2024-01-01', freq='D', periods=7)}).set_index(['time'])

    def test_critical_condition(self):
        assert agro.irrigation(self.last_month_dry.tp, self.df.tp, self.df.etp).iloc[6] == 0

    def test_ideal_condition(self):
        assert agro.irrigation(self.last_month_dry.tp, self.df.tp, self.df.etp).iloc[0] == 2

    def test_intermediate_condition(self):
        assert agro.irrigation(self.last_month_dry.tp, self.df.tp, self.df.etp).iloc[2] == 1
