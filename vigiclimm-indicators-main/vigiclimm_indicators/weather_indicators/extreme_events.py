"""
This module contains a generic function that generates risks for extreme events.
Three events are concerned in the VIGICLIMM project:

- Heavy rain ("fortes pluies")
- Heat stress ("température élévée")
- Strong wind ("vents forts")
"""
import pandas as pd
import xarray as xr
import typing as T


def generate_risk(data: T.Union[pd.Series, xr.DataArray],
                  lower_threshold: T.Union[int, float],
                  upper_threshold: T.Union[int, float]
                  ) -> T.Union[pd.Series, xr.DataArray]:
    """
    Returns risk values based on specified thresholds for a given parameter. The risk scale is as follows:
        - no risk = 0
        - moderate risk = 1
        - high risk = 2

    This function can be used to generate "extreme events indicators" such as Heavy Rain, Heat Stress, or Strong Wind.

    Args:
        data: Dataset containing the parameter of interest.
        lower_threshold: Lower threshold value. For example, set to 35°C to generate Heat Stress risk.
        upper_threshold: Upper threshold value. For example, set to 38°C to generate Heat Stress risk.

    Returns:
        Risk values indicating the severity of the parameter relative to the thresholds.

    """
    # Assign risk values based on thresholds
    high_risk = (data >= upper_threshold)
    no_risk = (data < lower_threshold)
    moderate_risk = ~high_risk & ~no_risk

    # Map boolean arrays to risk values
    risk_values = high_risk.astype(int) * 2 + moderate_risk.astype(int)

    # Create the output object based on input type
    if isinstance(data, xr.DataArray):
        risk = xr.DataArray(risk_values, coords=data.coords)
    elif isinstance(data, pd.Series):
        risk = pd.Series(risk_values, index=data.index, dtype=int) # type: ignore  # noqa
    else:
        raise TypeError("Expected pd.Series or xr.DataArray")

    return risk
