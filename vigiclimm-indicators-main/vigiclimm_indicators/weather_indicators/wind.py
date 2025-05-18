"""
Module containing all weather parameter functions related to wind.
"""

import numpy as np
import xarray as xr
import pandas as pd
import typing as T


def wind_speed_2m(
    ws: T.Union[np.ndarray, pd.Series, xr.DataArray],
    z: T.Union[int, float],
) -> T.Union[np.ndarray, pd.Series, xr.DataArray]:
    """
    Convert wind speed measured at different heights above the soil surface to wind speed at 2 m above the surface,
    assuming a short grass surface. Based on FAO equation 47 in Allen et al (1998).

    Args:
        ws: Measured wind speed [m s-1]
        z: Height of wind measurement above ground surface [m]

    Returns:
        Wind speed at 2 m above the surface [m s-1]
    """
    if ws is None:
        raise ValueError("`ws` must be provided")
    if z is None:
        raise ValueError("`z` must be provided")

    return (ws * 4.87) / np.log((67.8 * z) - 5.42)


def wind_speed(
    u: T.Union[np.ndarray, pd.Series, xr.DataArray],
    v: T.Union[np.ndarray, pd.Series, xr.DataArray]
) -> T.Union[np.ndarray, pd.Series, xr.DataArray]:
    """
    Compute the wind speed from U and V components.

    Args:
        u: U component of the wind based on the [ECMWF](https://apps.ecmwf.int/codes/grib/param-db/?id=131)
            definition.
        v: V component of wind based on the [ECMWF](https://apps.ecmwf.int/codes/grib/param-db?id=132)
            definition.
    Returns:
        Wind speed in the same units as the imput u and v.
    """
    return np.sqrt(u * u + v * v)
