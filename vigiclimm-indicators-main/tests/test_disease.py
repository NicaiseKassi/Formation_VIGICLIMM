import pandas as pd
import pytest
from vigiclimm_indicators.agro_indicators.disease import rice_blast


class TestRiceBlast():

    tmean = [30.5, 26.5, 27.9, 26.5, 25.5]
    tmin = [24.2, 22.3, 22.9, 22.2, 21.8]
    rhmean = [85, 90, 88, 94, 95]

    df = pd.DataFrame(
        {'tmean': tmean,
         'tmin': tmin,
         'rhmean': rhmean,
         'time': pd.date_range('2024-01-01', freq='D', periods=5)}).set_index(['time'])

    def test_pandas_no_risk(self):
        assert rice_blast(self.df.tmean, self.df.tmin, self.df.rhmean).iloc[0] == 0

    def test_pandas_high_risk(self):
        assert rice_blast(self.df.tmean, self.df.tmin, self.df.rhmean).iloc[4] == 2

    def test_pandas_moderate_risk(self):
        assert rice_blast(self.df.tmean, self.df.tmin, self.df.rhmean).iloc[3] == 1

    def test_xarray(self):
        ds = self.df.to_xarray()
        assert rice_blast(ds.tmean, ds.tmin, ds.rhmean)[0] == 0
        assert rice_blast(ds.tmean, ds.tmin, ds.rhmean)[4] == 2
        assert rice_blast(ds.tmean, ds.tmin, ds.rhmean)[3] == 1
