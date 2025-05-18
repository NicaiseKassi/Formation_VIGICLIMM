"""
Generation of agro indicators and risk disease indicator for all reference stations.
Input data are forecast indicators (CSV format).
Output data in a CSV format (one indicator/station).
"""

import vigiclimm_indicators.agro_indicators.agro_indicators as agro
from vigiclimm_indicators.agro_indicators.disease import rice_blast
from vigiclimm_indicators.weather_indicators.utils import write_to_csv, setup_logger

import pandas as pd
import typing as T
import yaml
import glob
import os
import click
from pathlib import Path
from loguru import logger

# loguru logger configuration
setup_logger(verbose=1)


def compute_and_write(input_path: T.Union[str, os.PathLike],
                      station_name: str,
                      outdir: T.Union[str, os.PathLike]) -> None:
    """
    Write agro_indicators, returns CSV format for every location.

    Args:
        input_path: Repositery where forecast and historical input are stored (csv files).
        station_name: Name of the station/location.
        outdir: Path of the output directory where CSV files will be saved.
    """
    # get all forecast values in the same dataframe
    df = merge_forecast_files(input_path, station_name)

    # get historical rainfall
    df_histo = pd.read_csv(
        os.path.join(
            input_path, f'{station_name}_historical_tp.csv'), index_col="time", converters={"time": pd.to_datetime})

    df_sowing = agro.sowing(df_histo, df.tp, df.gust)
    write_to_csv(df_sowing, outdir, station_name, 'sowing')

    df_drying = agro.drying(df.tp, df.tmax, df.rhmean, df.rhmin)
    write_to_csv(df_drying, outdir, station_name, 'drying')

    df_land_preparation = agro.land_preparation(df_histo.tp, df.tp, df.gust)
    write_to_csv(df_land_preparation, outdir, station_name, 'land_preparation')

    df_fertilization = agro.fertilization(df_histo.tp, df.tp, df.tmax, df.rhmean, df.gust)
    write_to_csv(df_fertilization, outdir, station_name, 'fertilization')

    df_harvesting = agro.harvesting(df_histo.tp, df.tp, df.rhmean)
    write_to_csv(df_harvesting, outdir, station_name, 'harvesting')

    df_protection = agro.protection(df_histo.tp, df.tp, df.tmax, df.gust, compute_mean_cloud_cover(df.mcc, df.lcc))
    write_to_csv(df_protection, outdir, station_name, 'protection')

    df_irrigation = agro.irrigation(df_histo.tp, df.tp, df.etp)
    write_to_csv(df_irrigation, outdir, station_name, 'irrigation')

    df_risk_disease = rice_blast(df.tmean, df.tmin, df.rhmean)
    write_to_csv(df_risk_disease, outdir, station_name, 'rice_blast') # type: ignore  # noqa


def compute_mean_cloud_cover(mcc: pd.Series, lcc: pd.Series) -> pd.Series:
    """
    Compute mean cloud cover, using low and medium level.
    Input are from GFS forecast.

    Args:
        mcc: Medium cloud cover [%].
        lcc : Low cloud cover [%].

    Returns:
        Series containing mean cloud cover values [%].
    """
    cloud_cover = (mcc+lcc)/2
    cloud_cover.name = 'cloud_cover'
    return cloud_cover


def merge_forecast_files(input_path: T.Union[str, os.PathLike], station_name: str) -> pd.DataFrame:
    """
     Merge all forecast input into one DataFrame.
        Args:
            input_path: Repositery where forecast input are stored (CSV files).
            station_name: Name of the station/location.

        Returns:
            Datafame containing all forecast input.
    """
    list_csv = glob.glob(os.path.join(input_path, f'{station_name}_forecast*.csv'))

    dataframes = []
    for filename in list_csv:
        df = pd.read_csv(filename, index_col="time", converters={"time": pd.to_datetime})
        dataframes.append(df)

    df = pd.concat(dataframes, axis='columns')
    return df


@click.command()
@click.option("--yml-path", required=True, type=click.Path(exists=True, path_type=Path))
@click.option("--input-path", required=True, type=click.Path(exists=True, path_type=Path))
@click.option("--outdir", required=True, type=Path)
def run_all_stations(yml_path: T.Union[str, os.PathLike],
                     input_path: T.Union[str, os.PathLike],
                     outdir: T.Union[str, os.PathLike]):

    with open(yml_path, 'r') as file:
        station_list = yaml.safe_load(file)

        for station in station_list:
            logger.info(f'Writing agro indicators for {station}')
            compute_and_write(input_path, station['station'], outdir)
    logger.opt(ansi=True).info('<green>All indicators written successfully</green>')
