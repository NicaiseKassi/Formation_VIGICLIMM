"""
Focus on Rice Blast disease (caused by Pyricularia oryzae).
"""

import pandas as pd
import xarray as xr
import typing as T


def rice_blast(tmean: T.Union[pd.Series, xr.DataArray],
               tmin: T.Union[pd.Series, xr.DataArray],
               rhmean: T.Union[pd.Series, xr.DataArray],
               ) -> T.Union[pd.Series, xr.DataArray]:
    """
    Optimal weather conditions to observe rice blast development.
    The developement occurs typically when the temperatures are relatively low combined with hight moisture.
    There is a low risk of development during hot days with lower relative humidity.

    Rainfall could also have an influence according to Yoshino model (1979).
    "The infection starts with rain smaller than 4 mm/h".
    -> if no hourly data but tri-hourly -> less than 12 mm/3h ?
    -> This variable will be not considered. The literature says that rainfall effect is unclear.

    Reference for weather thresholds, see: https://www.jstor.org/stable/44809338.

    Args:
        tmean: Daily mean temperature [°C]
        tmin: Daily minimum temperature [°C]
        rhmean: Daily mean relative humidity [%]

    Returns:
        Dataframe containing risk values, either 0, 1 or 2 (low, moderate or high risk).
    """

    # Assign risk values based on thresholds
    high_risk = (tmean <= 28) & (tmean >= 25) & (tmin <= 22) & (rhmean >= 90)
    no_risk = (tmean >= 29) | (rhmean <= 85)

    moderate_risk = ~high_risk & ~no_risk

    # Map boolean arrays to risk values
    risk_values = high_risk.astype(int) * 2 + moderate_risk.astype(int)

    # Create the output object based on input type
    if isinstance(risk_values, xr.DataArray):
        risk = xr.DataArray(risk_values, coords=risk_values.coords)
    elif isinstance(risk_values, pd.Series):
        risk = pd.Series(risk_values, index=risk_values.index, dtype=int) # type: ignore  # noqa
    else:
        raise TypeError("Expected pd.Series or xr.DataArray")

    return risk
