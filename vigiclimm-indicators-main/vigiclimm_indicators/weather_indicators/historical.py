"""
Compute and return historical values (degree days and total rainfall) for all stations.
Historical data should come from synoptic stations.
If there are not available, get precipitation from TAMSAT and temperature from ERA5-Land.
"""

import os
import pandas as pd
import xarray as xr
import typing as T
import yaml
import click
from pathlib import Path
from loguru import logger

from vigiclimm_indicators.weather_indicators.degree_days import degree_days
from vigiclimm_indicators.weather_indicators.utils import write_to_csv, setup_logger, consecutive_event_count
from vigiclimm_indicators.weather_indicators.preprocess import preprocess_gfs
from vigiclimm_indicators.weather_indicators.daily_forecast import wet_days

# loguru logger configuration
setup_logger(verbose=1)


def get_historical_data(station: str,
                        station_lat: T.Union[int, float],
                        station_lon: T.Union[int, float],
                        par: str,
                        obs_path: T.Union[str, os.PathLike],
                        era5land_path: T.Union[str, os.PathLike],
                        tamsat_path: T.Union[str, os.PathLike],
                        gfs_path: T.Union[str, os.PathLike],
                        ) -> pd.Series:
    """
    This function retrieves daily historical mean temperature and precipitation for the current year.
    First, it tries to get data from synoptic stations ('tmean' and 'tp' parameter, must be in csv format).
    If unsuccesful, gets mean temperature from ERA5-Land or rainfall from TAMSAT.

    Args:
        station: Name of the station/location.
        station_lat: Latitude of the station/location.
        station_lon: Longitude of the station/location.
        par: Name of the parameter, either 'tp' (precipitation) or 'tmean' (mean temperature).
        obs_path: Directory where observation files are stored.
        era5land_path: Directory where ERA5-Land data are stored.
        tamsat_path: Directory where the TAMSAT data are stored.
    Returns:
        Historical daily mean temperature or rainfall data for the current year.
    """
    # extract data for the current year only
    year = pd.Timestamp.now().year

    try:
        # Attempt to read data from obs files
        df = pd.read_csv(
            os.path.join(obs_path, f'{station}.csv'), index_col="time", converters={"time": pd.to_datetime})

        if df is not None:
            df = df[df.index.year == year]
            if par not in df.columns:
                raise ValueError(f"Parameter '{par}' not found in the obs file.")
            data = df[par]
            if df.empty:
                df = None

    except FileNotFoundError:
        logger.info(f"CSV file for station {station} not found. Using ERA5_LAND and TAMSAT data instead")
        df = None

    if df is None:
        # No obs data, use instead reanalysis/rainfall estimaste
        if par == 'tmean':
            data = get_era5_land_data(era5land_path, station_lat, station_lon)
        elif par == 'tp':
            data = get_tamsat_data(tamsat_path, gfs_path, station_lat, station_lon, data_filling=True)
        else:
            raise ValueError(f"Parameter '{par}' not valid, must be either 'tp' or 'tmean'")
    return data


def get_era5_land_data(era5land_path: T.Union[str, os.PathLike],
                       station_lat: float,
                       station_lon: float) -> pd.Series:

    ds = xr.open_dataset(era5land_path)
    data = ds['t2m'].sel(latitude=station_lat, longitude=station_lon, method='nearest').round(1)
    # resampling from hourly to daily values and convert to °C
    data = data.resample(time='D').mean() - 273.15
    return data.to_series()


def get_tamsat_data(tamsat_path: T.Union[str, os.PathLike],
                    gfs_path: T.Union[str, os.PathLike],
                    station_lat: T.Union[int, float],
                    station_lon: T.Union[int, float],
                    data_filling: bool = True) -> pd.Series:

    ds = xr.open_dataset(tamsat_path)
    data = ds['rfe'].sel(lat=station_lat, lon=station_lon, method='nearest').round(1)

    if data_filling:
        logger.info('Filling missing dates with GFS pseudo observations')

        # Check last date, must have data until D-3.
        last_time = pd.Timestamp(data.time[-1].item())
        today_minus_three = pd.Timestamp.now().date() - pd.Timedelta(days=3)

        if last_time.date() == today_minus_three:
            logger.info("Last TAMSAT data was three days ago, filling two last dates with GFS")
        else:
            logger.warning(f"No TAMSAT data after {last_time.date()}, more than two dates to fill")
        # fill missing dates (last D-1 and D-2 with GFS pseudo_obs)
        pseudo_obs = get_gfs_pseudo_obs(gfs_path, station_lat, station_lon)
        data_filled = xr.concat([data, pseudo_obs], dim='time')
        return data_filled.to_series()

    else:
        return data.to_series()


def get_gfs_pseudo_obs(gfs_path: T.Union[str, os.PathLike],
                       station_lat: T.Union[int, float],
                       station_lon: T.Union[int, float]
                       ) -> xr.DataArray:
    """
    Args:
        ds_path: GFS forecast data from D-2
        station_lat: Latitude of the station/location.
        station_lon: Longitude of the station/location.

    Returns:
        Data Array with the first valid time from D-2 forecast
    """
    ds = preprocess_gfs(gfs_path, 'tp', station_lat, station_lon)
    ds_first_two_days = ds.isel(time=[0, 1])

    return ds_first_two_days


def compute_and_write(tmean: T.Union[pd.Series, xr.DataArray],
                      tp: T.Union[pd.Series, xr.DataArray],
                      outdir: T.Union[str, os.PathLike],
                      station_name: str):

    # compute and write degree days
    df_dd = degree_days(base=18, tmean=tmean, index="hot").round(1)
    logger.info(f"Writing historical degree days for {station_name}")
    write_to_csv(df_dd, outdir, station_name, 'degree_days', period='historical')

    # write historical tp, wet/dry days + consecutive days count
    logger.info(f"Writing historical rainfall for {station_name}")
    write_to_csv(tp, outdir, station_name, 'tp', period='historical')

    logger.info(f"Writing historical wet_days for {station_name}")
    wet = wet_days(tp)
    write_to_csv(wet, outdir, station_name, 'wet_days', period='historical')

    consecutive_wet_days = consecutive_event_count(wet)
    write_to_csv(consecutive_wet_days, outdir, station_name, 'consecutive_wet_days', period='historical')

    logger.info(f"Writing historical dry_days for {station_name}")
    dry = ~wet
    write_to_csv(dry, outdir, station_name, 'dry_days', period='historical')

    consecutive_dry_days = consecutive_event_count(dry)
    write_to_csv(consecutive_dry_days, outdir, station_name, 'consecutive_dry_days', period='historical')


@click.command()
@click.option("--yml-path", required=True, type=click.Path(exists=True, path_type=Path))
@click.option("--obs-path", required=True, type=click.Path(exists=True, path_type=Path))
@click.option("--era5land-path", required=True, type=click.Path(exists=True, path_type=Path))
@click.option("--tamsat-path", required=True, type=click.Path(exists=True, path_type=Path))
@click.option("--gfs-path", required=True, type=click.Path(exists=True, path_type=Path))
@click.option("--outdir", required=True, type=Path)
def run_all_stations(yml_path: T.Union[str, os.PathLike],
                     obs_path: T.Union[str, os.PathLike],
                     era5land_path: T.Union[str, os.PathLike],
                     tamsat_path: T.Union[str, os.PathLike],
                     gfs_path: T.Union[str, os.PathLike],
                     outdir: T.Union[str, os.PathLike]):

    with open(yml_path, 'r') as file:
        station_list = yaml.safe_load(file)

        for station in station_list:
            logger.info(f'Writing historical indicators for {station}')
            compute_and_write(
                get_historical_data(
                    station['station'], station['lat'], station['lon'], 'tmean',
                    obs_path, era5land_path, tamsat_path, gfs_path),
                get_historical_data(
                    station['station'], station['lat'], station['lon'], 'tp',
                    obs_path, era5land_path, tamsat_path, gfs_path),
                outdir,
                station['station'])
    logger.opt(ansi=True).info('<green>All indicators written successfully</green>')
