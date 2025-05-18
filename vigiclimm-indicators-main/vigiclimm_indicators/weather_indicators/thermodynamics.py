"""
Module containing all weather parameter functions related to thermodynamics, e.g temperature,
pressure, relative humidity...
These functions can be used to estimate input variables when computing the ETP (Penman Mointeith method).

List of abbreviations used in the following function names:

atm_pressure: atmospheric pressure
avp: actual vapour pressure
psy_constant: psychrometric constant
rh: relative humidity
rhmax: maximum relative humidity
rhmin: minimum relative humidity
svp: saturation vapour pressure
t: temperature
tmax: maximum temperature
tmin: minimum temperature
tdew: dew point
tdry: dry bulb temperature
twet: wet bulb temperature

"""

import numpy as np
import typing as T
import pandas as pd
import xarray as xr


def svp_from_t(
    t: T.Union[pd.Series, pd.DataFrame, xr.DataArray, xr.Dataset],
    version: int = 1,
) -> T.Union[pd.Series, pd.DataFrame, xr.DataArray, xr.Dataset]:
    """
    Estimate saturation vapour pressure (**es**) from air temperature.

    `version=1` based on Alduchov & Eskridge 1996: Improved Magnus' form approximation of
    saturation vapor pressure. J. Appl. Meteor., 35, 601–609.

    `version=2` is based on equations 11 and 12 in Allen et al (1998).

    Args:
        t: Temperature [deg C]
        version: Version of approximation to use.

    Returns:
        Saturation vapour pressure [kPa]
    """
    if t is None:
        raise ValueError("`t` must be provided")

    if version == 1:
        return 0.61094 * np.exp((17.625 * t) / (t + 243.04))
    elif version == 2:
        return 0.6108 * np.exp((17.27 * t) / (t + 237.3))
    else:
        raise ValueError("`version` must be 1 or 2")


def delta_svp(
    t: T.Union[pd.Series, pd.DataFrame, xr.DataArray, xr.Dataset]
) -> T.Union[pd.Series, pd.DataFrame, xr.DataArray, xr.Dataset]:
    """
    Estimate the slope of the saturation vapour pressure curve at a given temperature.
    Based on equation 13 in Allen et al (1998). If using in the Penman-Monteith *t* should be the
    mean air temperature.

    Args:
        t: Air temperature [deg C]. Use mean air temperature for use in Penman-Monteith.

    Returns:
        Saturation vapour pressure [kPa degC-1]
    """
    if t is None:
        raise ValueError("`t` must be provided")

    numerator = 4098 * svp_from_t(t)
    demoninator = np.power((t + 237.3), 2)
    return numerator / demoninator


def rh_from_avp_and_svp(
    avp: T.Union[pd.Series, xr.DataArray],
    svp: T.Union[pd.Series, xr.DataArray]
) -> T.Union[pd.Series, xr.DataArray]:
    """
    Calculate relative humidity from the ratio of actual vapour pressure to saturation vapour pressure
    at the same temperature. See Allen et al (1998), page 67 for details.

    Args:
        avp: Actual vapour pressure [kPa]
        svp: Saturated vapour pressure [kPa]

    Returns:
        Relative humidity [%]
    """
    return 100.0 * avp / svp


def rh_from_tdew_and_t(
    tdew: T.Union[pd.Series, xr.DataArray],
    t: T.Union[pd.Series, xr.DataArray]
) -> T.Union[pd.Series, xr.DataArray]:
    """
    Calculate relative humidity from the dew point temperature and temperature.
    Converts the temperatures to vapour pressures using `saturation_vapour_pressure_from_temperature`.

    Args:
        tdew: Dew point temperature [deg C]
        t: Air temperature [deg C]

    Returns:
        Relative humidity [%]
    """
    avp = svp_from_t(tdew)
    svp = svp_from_t(t)
    return rh_from_avp_and_svp(avp, svp)


def psy_constant_of_psychrometer(
    atm_pressure: T.Union[pd.Series, pd.DataFrame, xr.DataArray, xr.Dataset],
    psychrometer: int = 1
) -> T.Union[pd.Series, pd.DataFrame, xr.DataArray, xr.Dataset]:
    """
    Calculate the psychrometric constant for different types of psychrometer at a given atmospheric pressure.
    Based on FAO equation 16 in Allen et al (1998).

    Args:
        atm_pressure: Atmospheric pressure [kPa]. Can be estimated using ``atm_pressure()``.
        psychrometer: Integer between 1 and 3 which denotes type of psychrometer:

            1. ventilated (Asmann or aspirated type) psychrometer with an air movement of approximately 5 m/s
            2. natural ventilated psychrometer with an air movement of approximately 1 m/s
            3. non ventilated psychrometer installed indoors

    Returns:
        Psychrometric constant [kPa degC-1].
    """
    # Select coefficient based on type of ventilation of the wet bulb
    if psychrometer == 1:
        psy_coeff = 0.000662
    elif psychrometer == 2:
        psy_coeff = 0.000800
    elif psychrometer == 3:
        psy_coeff = 0.001200
    else:
        raise ValueError("psychrometer should be in range 1 to 3: {0}".format(psychrometer))

    if atm_pressure is None:
        raise ValueError("`atm_pressure` must be provided")

    return psy_coeff * atm_pressure


def psy_constant(
    atmos_pres: T.Union[pd.Series, xr.DataArray] = None,
    altitude: T.Union[pd.Series, xr.DataArray] = None
) -> T.Union[pd.Series, xr.DataArray]:
    """
    Calculate the psychrometric constant. This method assumes that the air is saturated with water vapour at the
    minimum daily temperature. This assumption may not hold in arid areas.
    Based on equation 8, page 95 in Allen et al (1998).

    Args:
        atmos_pres: Atmospheric pressure [kPa]. Not required if `altitude` is provided.
        altitude: Elevation/altitude above sea level [m]. Not required if `atmos_pres` is provided.

    Returns:
        Psychrometric constant [kPa degC-1].
    """
    if atmos_pres is None:
        if altitude is None:
            raise ValueError("`atmos_pres` or `altitude` must be provided")
        else:
            atmos_pres = atm_pressure(altitude)
    return 0.000665 * atmos_pres


def atm_pressure(
    altitude: T.Union[pd.Series, pd.DataFrame, xr.DataArray, xr.Dataset]
) -> T.Union[pd.Series, pd.DataFrame, xr.DataArray, xr.Dataset]:
    """
    Estimate atmospheric pressure from altitude. Calculated using a simplification of the ideal gas law,
    assuming 20 degrees Celsius for a standard atmosphere. Based on equation 7, page 62 in Allen et al (1998).

    Args:
        altitude: Elevation/altitude above sea level [m]

    Returns:
        atmospheric pressure [kPa]
    """
    if altitude is None:
        raise ValueError("`altitude` must be provided")
    tmp = (293.0 - (0.0065 * altitude)) / 293.0
    return np.power(tmp, 5.26) * 101.3


def mean_svp(
    tmin: T.Union[pd.Series, xr.DataArray],
    tmax: T.Union[pd.Series, xr.DataArray]
) -> T.Union[pd.Series, xr.DataArray]:
    """
    Estimate mean saturation vapour pressure, *es* [kPa] from minimum and maximum temperature.
    Based on equations 11 and 12 in Allen et al (1998). Mean saturation vapour pressure is
    calculated as the mean of the saturation vapour pressure at tmax (maximum temperature)
    and tmin (minimum temperature).

    Args:
        tmin: Minimum temperature [deg C]
        tmax: Maximum temperature [deg C]

    Returns:
        Mean saturation vapour pressure (*es*) [kPa]
    """
    if tmax is None:
        raise ValueError("`tmax` must be provided")
    if tmin is None:
        raise ValueError("`tmin` must be provided")

    return (svp_from_t(tmin) + svp_from_t(tmax)) / 2.0


def avp(
    tdew: T.Union[pd.Series, xr.DataArray] = None,
    twet: T.Union[pd.Series, xr.DataArray] = None,
    tdry: T.Union[pd.Series, xr.DataArray] = None,
    atm_pressure: T.Union[pd.Series, xr.DataArray] = None,
    psychrometer: T.Optional[int] = None,
    tmin: T.Union[pd.Series, xr.DataArray] = None,
    tmax: T.Union[pd.Series, xr.DataArray] = None,
    rh_min: T.Union[pd.Series, xr.DataArray] = None,
    rh_max: T.Union[pd.Series, xr.DataArray] = None,
    rh_mean: T.Union[pd.Series, xr.DataArray] = None,
) -> T.Union[pd.Series, xr.DataArray]:
    """
    Estimate actual vapour pressure [kPa] (*ea*) from multiple methods, in order of preference, based on the
    provided input parameters:

    1 - Based on `tdew` - If dewpoint temperature data are available.
    2 - Based on `twet`, `tdry`, `atm_pressure` - If dry and wet bulb temperatures are available from
    a psychrometer.
    3 - Based on `tmin`, `tmax`, `rh_min`, `rh_max` - If  minimum and maximum relative humidity data available.
    4 - Based on `tmin`, `rh_max` - If measurement errors of relative humidity are large then use only
    maximum relative humidity    .
    5 - Based on `tmin`, `tmax`, `rh_mean` - If minimum and maximum relative humidity are not available but mean
    relative humidity is available (less reliable than options 3 or 4).
    6 - Based on `tmin` - If no data for the above. This function is less reliable in arid areas where it is
    recommended that 2 degrees Celsius is subtracted from the minimum temperature before it is passed to the
    function (following advice given in Annex 6 of Allen et al (1998).

    Args:
        tdew: Dewpoint temperature [deg C].
        twet: Wet bulb temperature [deg C].
        tdry: Dry bulb temperature [deg C].
        atm_pressure: Atmospheric pressure [kPa]
        psychrometer: Integer between 1 and 3 which denotes type of psychrometer -
        see `psychrometric_constant_of_psychrometer()`.
        tmin: Daily minimum temperature [deg C]
        tmax: Daily maximum temperature [deg C].
        rh_min: Minimum relative humidity [%]
        rh_max: Maximum relative humidity [%]
        rh_mean: Mean relative humidity [%] (mean of RH min and RH max).

    Returns:
        Actual vapour pressure [kPa]
    """
    if tdew is not None:
        return avp_from_tdew(tdew)
    elif all(i is not None for i in [twet, tdry, atm_pressure]):
        return avp_from_twet_tdry(twet, tdry, atm_pressure=atm_pressure, psychrometer=psychrometer)
    elif all(i is not None for i in [tmin, tmax, rh_min, rh_max]):
        return avp_from_rhmin_rhmax(rh_min=rh_min, rh_max=rh_max, tmin=tmin, tmax=tmax)
    elif all(i is not None for i in [tmin, rh_max]):
        return avp_from_rhmax(rh_max=rh_max, tmin=tmin)
    elif all(i is not None for i in [tmin, tmax, rh_mean]):
        return avp_from_rhmean(rh_mean=rh_mean, tmin=tmin, tmax=tmax)
    elif tmin is not None:
        return avp_from_tmin(tmin)
    else:
        raise ValueError("at least `tmin` must be provided")


def avp_from_tmin(
    tmin: T.Union[pd.Series, pd.DataFrame, xr.DataArray, xr.Dataset]
) -> T.Union[pd.Series, pd.DataFrame, xr.DataArray, xr.Dataset]:
    """
    Estimate actual vapour pressure (*ea*) from minimum temperature. This method is to be used where humidity data
    are lacking or are of questionable quality. The method assumes that the dewpoint temperature is approximately
    equal to the minimum temperature (*tmin*), i.e. the air is saturated with water vapour at *tmin*.
    **Note**: This assumption may not hold in arid/semi-arid areas.
    In these areas it may be better to subtract 2 deg C from the minimum temperature (see Annex 6 in FAO paper).
    Based on equation 48 in Allen et al (1998).

    Args:
        tmin: Daily minimum temperature [deg C]

    Returns:
        Actual vapour pressure [kPa]
    """
    if tmin is None:
        raise ValueError("`tmin` must be provided")

    return svp_from_t(tmin)


def avp_from_rhmin_rhmax(
    svp_tmin: T.Union[pd.Series, xr.DataArray] = None,
    svp_tmax: T.Union[pd.Series, xr.DataArray] = None,
    rh_min: T.Union[pd.Series, xr.DataArray] = None,
    rh_max: T.Union[pd.Series, xr.DataArray] = None,
    tmin: T.Union[pd.Series, xr.DataArray] = None,
    tmax: T.Union[pd.Series, xr.DataArray] = None
) -> T.Union[pd.Series, xr.DataArray]:
    """
    Estimate actual vapour pressure (*ea*) from saturation vapour pressure and relative humidity.
    For periods of a week, ten days or a month, `rh_max` and `rh_min` are obtained by dividing
    the sum of the daily values by the number of days in that period.
    Based on FAO equation 17 in Allen et al (1998).

    Args:
        svp_tmin: Saturation vapour pressure at daily minimum temperature [kPa]. Not required if `tmin` is provided.
        svp_tmax: Saturation vapour pressure at daily maximum temperature [kPa]. Not required if `tmax` is provided.
        rh_min: Minimum relative humidity [%]
        rh_max: Maximum relative humidity [%]
        tmin: Daily minimum temperature [deg C]. Required if `svp_tmin` is not provided.
        tmax: Daily maximum temperature [deg C]. Required if `svp_tmax` is not provided.

    Returns:
        Actual vapour pressure [kPa]
    """
    # Use `svp` if provided, otherwise use `tmin` and `tmax` to calculate `svp`
    if svp_tmin is None:
        if tmin is None:
            raise ValueError("`svp_tmin` or `tmin` must be provided")
        else:
            svp_tmin = svp_from_t(tmin)
    if svp_tmax is None:
        if tmax is None:
            raise ValueError("`svp_tmax` or `tmax` must be provided")
        else:
            svp_tmax = svp_from_t(tmax)
    tmp1 = svp_tmin * rh_max / 100.0
    tmp2 = svp_tmax * rh_min / 100.0
    return (tmp1 + tmp2) / 2.0


def avp_from_rhmax(
    svp_tmin: T.Union[pd.Series, xr.DataArray] = None,
    rh_max: T.Union[pd.Series, xr.DataArray] = None,
    tmin: T.Union[pd.Series, xr.DataArray] = None
) -> T.Union[pd.Series, xr.DataArray]:
    """
    Estimate actual vapour pressure (*ea*) from saturation vapour pressure at daily minimum temperature
    and maximum relative humidity. Based on FAO equation 18 in Allen et al (1998).

    Args:
        svp_tmin: Saturation vapour pressure at daily minimum temperature [kPa]. Not required if `tmin` is provided.
        rh_max: Maximum relative humidity [%]
        tmin: Daily minimum temperature [deg C]. Required if `svp_tmin` is not provided.

    Returns:
        Actual vapour pressure [kPa]
    """
    if svp_tmin is None:
        if tmin is None:
            raise ValueError("`svp_tmin` or `tmin` must be provided")
        else:
            svp_tmin = svp_from_t(tmin)

    return svp_tmin * rh_max / 100.0


def avp_from_rhmean(
    svp_tmin: T.Union[pd.Series, xr.DataArray] = None,
    svp_tmax: T.Union[pd.Series, xr.DataArray] = None,
    rh_mean: T.Union[pd.Series, xr.DataArray] = None,
    tmin: T.Union[pd.Series, xr.DataArray] = None,
    tmax: T.Union[pd.Series, xr.DataArray] = None
) -> T.Union[pd.Series, xr.DataArray]:
    """
    Estimate actual vapour pressure (*ea*) from saturation vapour pressure at daily minimum and maximum
    temperature, and mean relative humidity. Based on FAO equation 19 in Allen et al (1998).

    Args:
        svp_tmin: Saturation vapour pressure at daily minimum temperature [kPa]. Not required if `tmin` is provided.
        svp_tmax: Saturation vapour pressure at daily maximum temperature [kPa]. Not required if `tmax` is provided.
        rh_mean: Mean relative humidity [%] (average of RH min and RH max).
        tmin: Daily minimum temperature [deg C]. Required if `svp_tmin` is not provided.
        tmax: Daily maximum temperature [deg C]. Required if `svp_tmax` is not provided.

    Returns:
        Actual vapour pressure [kPa]
    """
    # Use `svp` if provided, otherwise use `tmin` and `tmax` to calculate `svp`
    if svp_tmin is None:
        if tmin is None:
            raise ValueError("`svp_tmin` or `tmin` must be provided")
        else:
            svp_tmin = svp_from_t(tmin)
    if svp_tmax is None:
        if tmax is None:
            raise ValueError("`svp_tmax` or `tmax` must be provided")
        else:
            svp_tmax = svp_from_t(tmax)
    return (rh_mean / 100.0) * ((svp_tmax + svp_tmin) / 2.0)


def avp_from_tdew(
    tdew: T.Union[pd.Series, pd.DataFrame, xr.DataArray, xr.Dataset]
) -> T.Union[pd.Series, pd.DataFrame, xr.DataArray, xr.Dataset]:
    """
    Estimate actual vapour pressure (*ea*) from dewpoint temperature.
    Based on equation 14 in Allen et al (1998). As the dewpoint temperature is the temperature to which air
    needs to be cooled to make it saturated, the actual vapour pressure is the saturation vapour pressure at
    the dewpoint temperature. This method is preferable to calculating vapour pressure from minimum temperature.

    Args:
        tdew: Dewpoint temperature [deg C]

    Returns:
        Actual vapour pressure [kPa]
    """
    if tdew is None:
        raise ValueError("`tdew` must be provided")

    return svp_from_t(tdew)


def avp_from_twet_tdry(
    twet: T.Union[pd.Series, xr.DataArray],
    tdry: T.Union[pd.Series, xr.DataArray],
    svp_twet: T.Union[pd.Series, xr.DataArray] = None,
    psy_const: T.Union[pd.Series, xr.DataArray] = None,
    psychrometer: T.Optional[int] = None,
    atm_pressure: T.Union[pd.Series, xr.DataArray] = None
):
    """
    Estimate actual vapour pressure (*ea*) from wet and dry bulb temperature.
    Based on equation 15 in Allen et al (1998). As the dewpoint temperature is the temperature to which air needs
    to be cooled to make it saturated, the actual vapour pressure is the saturation vapour pressure at the dewpoint
    temperature. This method is preferable to calculating vapour pressure from minimum temperature.
    Values for the psychrometric constant of the psychrometer ``psy_const`` can be calculated using
    ``psyc_const_of_psychrometer()``.

    Args:
        twet: Wet bulb temperature [deg C]
        tdry: Dry bulb temperature [deg C]
        svp_twet: Saturated vapour pressure at the wet bulb temperature [kPa]. Not required if `twet` is provided.
        psy_const: Psychrometric constant of the pyschrometer [kPa deg C-1].  Not required if
        both `atm_pressure` and `psychrometer` or just `atm_pressure` are provided.
        psychrometer: Integer between 1 and 3 which denotes type of psychrometer
        - see `psy_constant_of_psychrometer()`
        atm_pressure: Atmospheric pressure [kPa]

    Returns:
        Actual vapour pressure [kPa]
    """
    if twet is None:
        raise ValueError("`twet` must be provided")
    if tdry is None:
        raise ValueError("`tdry` must be provided")

    if svp_twet is None:
        svp_twet = svp_from_t(twet)

    if psy_const is None:
        if atm_pressure is None:
            raise ValueError("`atm_pressure` must be provided")
        if psychrometer is None:
            psy_const = psy_constant(atm_pressure)
        else:
            psy_const = psy_constant_of_psychrometer(atm_pressure, psychrometer)
    return svp_twet - psy_const * (tdry - twet)


def tdew_from_rh_and_t(
    rh: T.Union[pd.Series, xr.DataArray],
    t: T.Union[pd.Series, xr.DataArray]
) -> T.Union[pd.Series, xr.DataArray]:
    """
    Computation of the dew point from the relative humidity and the temperature.
    It uses the Magnus Formula (1844) which gives a good estimation of tdew.
    The constants values given in the equation are from Tetens (1930).

    Args:
        rh: Relative humidity [%]
        t: Air temperature [deg C]

    Returns:
        Dew point [deg C]
    """
    # Tetens contants
    a = 17.27
    b = 237.7

    phi = (a * t) / (b + t) + np.log(rh / 100)
    tdew = (b * phi) / (a - phi)
    return tdew


def monthly_soil_heat_flux(
    t_month_prev: T.Union[pd.Series, xr.DataArray],
    t_month: T.Union[pd.Series, xr.DataArray],
    next_month: bool = False
) -> T.Union[pd.Series, xr.DataArray]:
    """
    Estimate monthly soil heat flux (Gmonth) from the mean air temperature of the previous and current or
    next month, assuming a grass crop.
    When `next_month==True`, `t_month` is for the next month, based on equation 43 in Allen et al (1998).
    WHen `next_month==False` `t_month` is for the current month, based on equation 44 in Allen et al (1998).
    The resulting heat flux can be converted to equivalent evaporation [mm day-1] using ``energy_to_evap()``.

    Args:
        t_month_prev: Mean air temperature of the previous month [deg Celsius]
        t_month: Mean air temperature of the current/next month [deg Celsius]
        next_month: If `True` then `t_month` is assumed to be the mean temperature of the next month,
        otherwise `t_month` is assumed to be the mean for the current month.

    Returns:
        Monthly soil heat flux (Gmonth) [MJ m-2 day-1]
    """
    if next_month:
        factor = 0.07
    else:
        factor = 0.14
    return factor * (t_month - t_month_prev)


def energy_to_evap(
    energy: T.Union[pd.Series, pd.DataFrame, xr.DataArray, xr.Dataset]
) -> T.Union[pd.Series, pd.DataFrame, xr.DataArray, xr.Dataset]:
    """
    Convert energy (e.g. radiation energy) in MJ m-2 day-1 to the equivalent evaporation, assuming
    a grass reference crop. Energy is converted to equivalent evaporation using a conversion factor
    equal to the inverse of the latent heat of vapourisation (1 / lambda = 0.408).
    Based on FAO equation 20 in Allen et al (1998).

    Args:
        energy: Energy e.g. radiation or heat flux [MJ m-2 day-1].

    Returns:
        Equivalent evaporation [mm day-1].
    """
    if energy is None:
        raise ValueError("`energy` must be provided")

    return 0.408 * energy
