import pandas as pd
import pytest
from vigiclimm_indicators.weather_indicators.extreme_events import generate_risk


@pytest.fixture
def df():
    tmax_values = [39.5, 36.7, 32.8]
    df = pd.DataFrame(
        {"tmax": tmax_values,
         'time': pd.date_range('2024-01-01', freq='D', periods=3)}).set_index(['time'])
    return df


@pytest.fixture
def ds(df):
    return df.to_xarray()


def test_pandas_high_risk(df):
    assert generate_risk(df['tmax'], 35, 38).iloc[0] == 2


def test_pandas_moderate_risk(df):
    assert generate_risk(df['tmax'], 35, 38).iloc[1] == 1


def test_pandas_no_risk(df):
    assert generate_risk(df['tmax'], 35, 38).iloc[2] == 0


def test_xarray_high_risk(ds):
    assert generate_risk(ds['tmax'], 35, 38)[0] == 2


def test_xarray_moderate_risk(ds):
    assert generate_risk(ds['tmax'], 35, 38)[1] == 1


def test_xarray_no_risk(ds):
    assert generate_risk(ds['tmax'], 35, 38)[2] == 0
