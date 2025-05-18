"""
Compute and return daily weather parameters and forecasted indicators from GFS.
"""

import os
import click
import xarray as xr
import pandas as pd
import typing as T
import yaml

from pathlib import Path
from loguru import logger
from .preprocess import preprocess_gfs
from .extreme_events import generate_risk
from .etp import etp_from_gfs
from .utils import write_to_csv, setup_logger

# loguru logger configuration
setup_logger(verbose=1)


def compute_and_write(ds_path: T.Union[str, os.PathLike],
                      station_lat: T.Union[int, float],
                      station_lon: T.Union[int, float],
                      station_name: str,
                      outdir: T.Union[str, os.PathLike]) -> None:
    """
    Write weather parameters and forecast indicators to CSV format for a location.
    Input data should be GFS.

    Args:
        ds_path: Path of the GFS file containing all parameters for all steps.
        station_lat: Latitude of the location.
        station_lon: Longitude of the location.
        station_name: Name of the station/location.
        outdir: Path of the output directory where CSV files will be saved.
    """
    par_list = ['tp', 'tmax', 'tmean', 'tmin', 'dswrf', 'rhmean', 'rhmax', 'rhmin', 'gust', 'mcc', 'lcc']
    for par in par_list:
        # keep raw Solar Radiation units; converts otherwise.
        if par == 'dswrf':
            ds = preprocess_gfs(ds_path, par, station_lat, station_lon, convert=False)
        else:
            ds = preprocess_gfs(ds_path, par, station_lat, station_lon, convert=True)
        df = ds.to_series()

        # Write raw forecast data to CSV file
        logger.info(f'Writing {par} parameter for {station_name}')
        write_to_csv(df, outdir, station_name, par)

        # Write indicators
        if par == 'tp':
            wet = wet_days(df)
            write_to_csv(wet, outdir, station_name, 'wet_days')

            sum_tp = pd.Series(df.sum(), index=[df.index[0]]).round(1)
            sum_tp.index.names = ['time']
            write_to_csv(sum_tp, outdir, station_name, 'sum_tp')

            df_rain = generate_risk(df, 10, 30)
            write_to_csv(df_rain, outdir, station_name, 'heavy_rain')

        if par == 'tmax':
            df_heat = generate_risk(df, 35, 38)
            write_to_csv(df_heat, outdir, station_name, 'heat_stress')

        if par == 'gust':
            df_wind = generate_risk(df, 50, 70)
            write_to_csv(df_wind, outdir, station_name, 'strong_wind')

    ds_etp = etp_from_gfs(ds_path, station_lat, station_lon)
    df_etp = ds_etp.to_series()
    write_to_csv(df_etp, outdir, station_name, 'etp')


def wet_days(
    data: T.Union[pd.Series, pd.DataFrame, xr.DataArray, xr.Dataset],
    threshold: T.Union[int, float] = 1,
) -> T.Union[pd.Series, pd.DataFrame, xr.DataArray, xr.Dataset]:
    """
    Counts wet days occurences.
    A wet day is counted when tp > 1 mm. This is the standard threshold given by
    the WMO: https://indico.ictp.it/event/a10167/session/16/contribution/12/material/0/0.pdf.

    Args:
        data: Rainfall forecast data
        threshold: Minimal amount to consider a rainy day

    Returns:
        Data with boolean values, `True` for wet_days.
    """
    wet_days = threshold <= data
    return wet_days


@click.command()
@click.option("--yml-path", required=True, type=click.Path(exists=True, path_type=Path))
@click.option("--ds-path", required=True, type=click.Path(exists=True, path_type=Path))
@click.option("--outdir", required=True, type=Path)
def run_all_stations(yml_path: T.Union[str, os.PathLike],
                     ds_path: T.Union[str, os.PathLike],
                     outdir: T.Union[str, os.PathLike]):

    with open(yml_path, 'r') as file:
        station_list = yaml.safe_load(file)

        for station in station_list:
            logger.info(f'Writing forecast indicators for {station}')
            compute_and_write(ds_path, station['lat'], station['lon'], station['station'], outdir)
    logger.opt(ansi=True).info('<green>All indicators written successfully</green>')
