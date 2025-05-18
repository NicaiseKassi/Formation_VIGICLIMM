"""
The utils module gathers small useful functions which are common to several main scripts.
"""
import os
import sys
import typing as T
import pandas as pd

from pathlib import Path
from loguru import logger


def cdd_max(data: pd.Series, threshold: T.Union[int, float] = 1) -> int:
    """
    Computes the maximum consecutive dry days series within a time period.

    Args:
        data: data containing the parameters to check the events
        threshold: dry event threshold

    Returns:
        Maximum consecutive events in range, for the given time period.
    """

    true_events = data <= threshold

    current_consecutive = 0
    global_consecutive = 0

    for value in true_events:
        if value:
            current_consecutive += 1
            global_consecutive = max(global_consecutive, current_consecutive)
        else:
            current_consecutive = 0

    return global_consecutive


def consecutive_event_count(data: pd.Series) -> pd.Series:
    """
    Compute consecutive events count in a series within a time period. Data must be filled with Boolean.
    The count resets when a False event occurs.
    Can be applied to compute dry and wet consecutive days.

    Args:
        data: data containing the parameters to check the events
    Returns:
        Series with consecutive events count for the given time period.
    """
    # Initialize variables
    count = 0
    consecutive_counts = []

    # Iterate through the series
    for value in data:
        if value:
            consecutive_counts.append(count)
            count += 1
        else:
            count = 0
            consecutive_counts.append(count)

    # Append the final count for the last true sequence
    consecutive_counts.append(count)
    # Create a new series with the consecutive counts
    consecutive_series = pd.Series(consecutive_counts[:-1], index=data.index)

    return consecutive_series


def write_to_csv(df: pd.Series,
                 outdir: T.Union[str, os.PathLike],
                 station_name: str,
                 parameter: str,
                 period: str = 'forecast'
                 ) -> None:
    """
    Write Data series to CSV file.

    Args:
        df: DataSeries to be written.
        outdir: Output directory.
        station_name: Name of the station/location.
        parameter: Parameter name.
        period: Specify the nature of data, either `historical` or `forecast`.
    """
    if not isinstance(df, pd.Series):
        raise TypeError("Expected pd.Series")
    if period not in ['historical', 'forecast']:
        raise ValueError("Period must be either `historical` or `forecast`")

    if not Path(outdir).exists():
        Path(outdir).mkdir(parents=True, exist_ok=True)

    # specify name of the columns
    df.name = parameter
    df.to_csv(os.path.join(outdir, f'{station_name}_{period}_{parameter}.csv'))


def setup_logger(verbose: int):
    """
    Configure loguru logger.
    """
    log_fmt = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>"
    log_fmt_param = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | \
    {extra[param]} | <level>{message}</level>"

    loglevel = "INFO"
    if verbose == 1:
        loglevel = "DEBUG"
    if verbose >= 2:
        loglevel = "TRACE"

    logger.remove()
    logger.add(sys.stdout, format=log_fmt, level=loglevel, enqueue=False, filter=lambda r: not r["extra"])
    logger.add(sys.stdout, format=log_fmt_param, level=loglevel, enqueue=False, filter=lambda r: "param" in r["extra"])
