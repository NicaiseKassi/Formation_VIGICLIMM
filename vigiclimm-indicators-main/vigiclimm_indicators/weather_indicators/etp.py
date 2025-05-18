"""
Module containing functionality to estimate reference evapotransporation (ETo), sometimes referred as
potential evapotranspiration (PET), for a grass reference crop using the FAO-56 Penman-Monteith equation.
"""
import os
import xarray as xr
import pandas as pd
import typing as T

import vigiclimm_indicators.weather_indicators.thermodynamics as thermo
from vigiclimm_indicators.weather_indicators.preprocess import preprocess_gfs
from .wind import wind_speed, wind_speed_2m


def fao56_penman_monteith(
    net_rad: T.Union[pd.Series, xr.DataArray],
    t: T.Union[pd.Series, xr.DataArray],
    ws: T.Union[pd.Series, xr.DataArray],
    svp: T.Union[pd.Series, xr.DataArray],
    avp: T.Union[pd.Series, xr.DataArray],
    delta_svp: T.Union[pd.Series, xr.DataArray],
    psy: T.Union[pd.Series, xr.DataArray],
    shf: T.Union[int, float] = 0.0
) -> T.Union[pd.Series, xr.DataArray]:
    """
    Estimate reference evapotranspiration (ETo) from a hypothetical short grass reference surface using
    the FAO-56 Penman-Monteith equation. Based on equation 6 in Allen et al (1998).

    This is the method recommended by the Food and Agriculture Organisation of the United Nations (FAO)
    for estimating (ETo) for a short grass crop using limited meteorological data (see Allen et al, 1998).
    The FAO-56 Penman-Monteith equation requires site location, air temperature, humidity, radiation and
    wind speed data for daily, weekly, ten-day or monthly ETo calculations. It is important to verify the
    units of all input data.

    Alternatives methods to compute ETo exist (Hargreaves-Samani, Blaney-Criddle), based on fewer parameters
    but are far less precise and hence not recommended.

    Args:
        net_rad: Net radiation at crop surface [MJ m-2 day-1].
        t: Mean daily air temperature at 2 m height [deg Celcius].
        ws: Wind speed at 2 m height [m s-1]. If not measured at 2m, convert using ``wind_speed_at_2m()``.
        svp: Saturation vapour pressure [kPa]. Can be estimated using ``svp_from_t()''.
        avp: Actual vapour pressure [kPa]. Can be estimated using a range of functions, in order of preference:
            1 - If dewpoint temperature data are available use ``avp_from_tdew()``.
            2 - If dry and wet bulb temperatures are available from a psychrometer
            use ``avp_from_twet_tdry()``.
            3 - If reliable minimum and maximum relative humidity data available
            use ``avp_from_rhmin_rhmax()``.
            4 - If measurement errors of relative humidity are large then use only maximum relative humidity
            using ``avp_from_rhmax()``.
            5 - If minimum and maximum relative humidity are not available but mean relative humidity is available
            then use ``avp_from_rhmean()`` (but this is less reliable than options 3 or 4).
            6 - If no data for the above are available then use ``avp_from_tmin()``.
            This function is less reliable in arid areas where it is recommended that 2 degrees Celsius is
            subtracted from the minimum temperature before it is passed to the function (following advice
            given in Annex 6 of Allen et al (1998).
        delta_svp: Slope of saturation vapour pressure curve [kPa degC-1]. Can be
        estimated using ``delta_svp()``.
        psy: Psychrometric constant [kPa degC-1]. Can be estimated using, in order of preference:
        ``psy_constant_of_psychrometer()`` or ``psy_constant()``.
        shf: Soil heat flux (G) [MJ m-2 day-1] (default is 0.0, which is reasonable for a daily or 10-day time
        steps). For monthly time steps ``shf`` can be estimated using ``monthly_soil_heat_flux()``.

    Returns:
        Reference evapotranspiration (ETo) from a hypothetical grass reference surface [mm day-1]
    """
    if shf is None:
        shf = 0.0

    # Check all required parameters are given
    for name, variable in zip(
        ["net_rad", "t", "ws", "svp", "avp", "delta_svp", "psy", "shf"], [net_rad, t, ws, svp, avp, delta_svp, psy, shf]
    ):
        if variable is None:
            raise ValueError(f"Parameter {name} is not given")

    numerator = (0.408 * (net_rad - shf) * delta_svp) + ((psy * 891.3 * ws * (svp - avp)) / (t + 273))
    denominator = delta_svp + (psy * (1 + 0.3365 * ws))

    return numerator / denominator


def etp_from_gfs(ds_path: T.Union[str, os.PathLike],
                 station_lat: T.Union[int, float],
                 station_lon: T.Union[int, float],
                 altitude: T.Union[int, float] = 100
                 ) -> xr.DataArray:
    """
    Compute ETP using GFS Data as input parameters.

    Args:
        ds_path: Path of the GFS file containing all parameters for all steps.
        station_lat: Latitude of the location.
        station_lon: Longitude of the location.
        altitude: altitude of the station [m], by default 100 meters

    Returns:
        DataArray containing daily forecasted ETo values
    """
    net_rad = preprocess_gfs(ds_path, 'dswrf', station_lat, station_lon, convert=True)
    t = preprocess_gfs(ds_path, 'tmean', station_lat, station_lon, convert=True)
    tdew = preprocess_gfs(ds_path, '2d', station_lat, station_lon, convert=True)

    # get wind speed using u and v components, and estimates it at 2m height
    # no conversion; etp function requires wind speed in m/s
    ws = wind_speed_2m(wind_speed(preprocess_gfs(ds_path, '10u', station_lat, station_lon),
                                  preprocess_gfs(ds_path, '10v', station_lat, station_lon)), 2)

    etp = fao56_penman_monteith(
        net_rad=net_rad,
        t=t,
        ws=ws,
        svp=thermo.svp_from_t(t),
        avp=thermo.avp_from_tdew(tdew),
        delta_svp=thermo.delta_svp(t),
        psy=thermo.psy_constant(altitude),
        shf=0.0
    )

    return xr.DataArray(etp).round(1)
