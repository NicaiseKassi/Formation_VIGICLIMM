"""
This module gathers most of the functions that computes the agro indicators.
The disease risk ('risque de maladie') indicator is developed in another module.

The indicators give a daily state of conditions for the next 10 forecasted days:
    - favorable (returns "2)
    - intermediate (returns "1")
    - not favorable (returns "0")
"""

import pandas as pd

from vigiclimm_indicators.weather_indicators.daily_forecast import wet_days
from vigiclimm_indicators.weather_indicators.utils import cdd_max


def land_preparation(tp_histo: pd.Series,
                     tp: pd.Series,
                     gust: pd.Series,
                     ) -> pd.Series:
    """
    "Préparation du sol" indicator.

    It aims to provide guidance to farmers on land preparation practices.
    Typically, the land preparation period is in April or May, just before the rainy season.

    The soil must be slighlty moist (necessary to look at recent historical rainfall data).
    Calm weather conditions required (no strong winds or heavy rain).

    Args:
        tp_histo: recent history (last month) of daily rainfall.
            The data are from observations or rainfall estimates (TAMSAT) depending the data avaibility [mm]
        tp: daily rainfall forecast data [mm]
        gust: daily gust forecast data [km/h]

    Returns:
        Condition values, either 0, 1, or 2.
    """
    # need at least 4 wet days during the last month + forecasted days
    if wet_days(tp_histo).sum() >= 4 or (wet_days(tp_histo).sum() + wet_days(tp).sum()) >= 4:
        # define masks for ideal and critical conditions
        ideal_condition = (tp < 10) & (tp > 1) & (gust < 30)
        critical_condition = (tp > 30) | (gust > 50)

        neutral_condition = ~ideal_condition & ~critical_condition

        # Map boolean arrays to condition values
        condition_values = ideal_condition.astype(int) * 2 + neutral_condition.astype(int)

        # create empty conditions file, with forecast index
        condition = pd.Series(condition_values, index=tp.index, dtype="int")
    else:
        condition = pd.Series(index=tp.index, dtype="int")
        condition = condition.fillna(False)

    return condition


def sowing(tp_histo: pd.Series,
           tp: pd.Series,
           gust: pd.Series,
           ) -> pd.Series:
    """
    "Semis" indicator.

    Guidance for sowing activities.

    Args:
        tp_histo: recent history (last month) of daily rainfall.
            The data are from observations or rainfall estimates (TAMSAT) depending the data avaibility [mm]
        tp: daily rainfall forecast data [mm]
        gust: daily gust forecast data [km/h]

    Returns:
        Condition values, either 0, 1, or 2.
    """
    # merging historical and forecast rainfall
    tp_merged = pd.concat([tp_histo, tp]).iloc[-17:]  # 10 days of forecasts + last 7 historical days = 17 days

    condition_values = []

    for i in range(0, len(tp)):
        # ideal conditions
        if (tp.iloc[i] <= 10) & (tp.iloc[i] >= 1) & (gust.iloc[i] <= 30) & (cdd_max(tp_merged.iloc[i: 7 + i]) <= 5):
            result = 2
        # critical conditions
        elif (tp.iloc[i] > 30) | (gust.iloc[i] > 50) | (cdd_max(tp_merged.iloc[i: 7 + i]) >= 7):
            result = 0
        # neutral conditions
        else:
            result = 1

        condition_values.append(result)

    return pd.Series(condition_values, index=tp.index, dtype="int")


def fertilization(tp_histo: pd.Series,
                  tp: pd.Series,
                  tmax: pd.Series,
                  rhmean: pd.Series,
                  gust: pd.Series,
                  ) -> pd.Series:
    """
    Fertilization indicator. Guidance for fertilizer spreading activities.

    Args:
        tp_histo: Recent daily rainfall. The data are from observations or rainfall estimates (TAMSAT)
            depending the data avaibility [mm]
        tp: daily rainfall forecast data [mm]
        tmax: daily temperature forecast data [°C]
        rhmean: daily mean relative humidity [%]
        gust: daily gust forecast data [km/h]

    Returns:
        Condition values, either 0, 1, or 2.
    """
    conditions_values = []

    for i in range(0, len(tp)):
        # for first step, it requires the last observation.
        if i == 0:
            if (wet_days(tp_histo.iloc[-1])) & (wet_days(tp.iloc[i])) & (tmax.iloc[i] < 35) & \
                    (rhmean.iloc[i] >= 70) & (tp.iloc[i] > 5) & (tp.iloc[i] < 10):
                # ideal conditions
                result = 2
            elif (tp.iloc[i] >= 30) | (tmax.iloc[i] >= 38):
                # critical conditions
                result = 0
            else:
                # intermediate conditions
                result = 1
        else:
            if (wet_days(tp.iloc[i - 1: i + 1]).sum() >= 1) & (rhmean.iloc[i] >= 70) & (tmax.iloc[i] < 35) & \
                    (tp.iloc[i] > 5) & (tp.iloc[i] < 10):
                # ideal conditions
                result = 2
                # critical conditions
            elif (tp.iloc[i] >= 30) | (tmax.iloc[i] >= 38):
                result = 0
                # intermediate conditions
            else:
                result = 1

        conditions_values.append(result)

    return pd.Series(conditions_values, index=tp.index, dtype="int")


def harvesting(tp_histo: pd.Series,
               tp: pd.Series,
               rhmean: pd.Series
               ) -> pd.Series:
    """
    "Récolte" indicator. Guidance for harvesting activites.

    Args:
        tp_histo: recent history (last 2 weeks) of daily rainfall.
            The data are from observations or rainfall estimates (TAMSAT) depending their avaibility [mm]
        tp: daily rainfall forecast data [mm]
        rhmean: daily mean relative humidity data [%]
    Returns:
        Condition values, either 0, 1, or 2.
    """

    list_conditions = []

    # iterating over forecast
    for i in range(0, len(tp)):

        if (tp.iloc[i:i + 2].sum() == 0) & (rhmean.iloc[i] < 80) & (tp_histo.sum() == 0):
            # ideal conditions
            result = 2
        elif (tp.iloc[i:i + 2].sum() > 5):
            # critical conditions
            result = 0
        else:
            # intermediate conditions
            result = 1

        list_conditions.append(result)

    return pd.Series(list_conditions, index=tp.index, dtype="int")


def drying(tp: pd.Series,
           tmax: pd.Series,
           rhmean: pd.Series,
           rhmin: pd.Series,
           ) -> pd.Series:
    """
    "Séchage" indicator. It aims to give guidance to farmers to dry rice.

    Ideal conditions:
        t < 42 °C
        tp = 0 mm
        rhmean < 50 %
        rhmin > 10 %

    Reference: https://africasoilhealth.cabi.org/wpcms/wp-content/uploads/2016/06/French-Rice-Guide-A4-BW-lowres.pdf

    Args:
        tp: daily rainfall forecast data [mm]
        tmax: daily temperature forecast data [°C]
        rhmean: daily mean relative humidity forecast data [%]
        rhmin: daily minimum relative humidity forecast data [%]

    Returns:
         "Condition" values (either 0, 1 or 2).
    """

    # define masks for ideal and critical conditions
    ideal_condition = (tp <= 1) & (tmax < 42) & (rhmean < 50) & (rhmin > 10)
    critical_condition = (tmax > 42) | (tp > 1) | (rhmin < 10)

    neutral_condition = ~ideal_condition & ~critical_condition

    # Map boolean arrays to condition values
    condition_values = ideal_condition.astype(int) * 2 + neutral_condition.astype(int)

    return pd.Series(condition_values, index=tp.index, dtype="int")


def protection(tp_histo: pd.Series,
               tp: pd.Series,
               tmax: pd.Series,
               gust: pd.Series,
               cloud_cover: pd.Series
               ) -> pd.Series:
    """

    Protection indicator. Guidance for spreading insecticides.

    Args:
        tp_histo: recent history (last month) of daily rainfall
            The data are from observations or rainfall estimates (TAMSAT) depending their avaibility [mm]
        tp: daily rainfall forecast data [mm]
        tmax: daily temperature forecast data [°C]
        gust: daily gust forecast data [km/h]

    Returns:
        Condition values, either 0, 1, or 2.
    """

    list_conditions = []

    for i in range(0, len(tp)):
        # for first step, it requires the last observation.
        if i == 0:
            if (wet_days(tp_histo.iloc[-1])) & (wet_days(tp.iloc[i])) & (tmax.iloc[i] < 35) & (tp.iloc[i] < 15) & \
                    (cloud_cover.iloc[i] >= 50):
                # ideal conditions
                result = 2
            elif (gust.iloc[i] >= 50) | (tmax.iloc[i] >= 38) & (cloud_cover.iloc[i] <= 20):
                # critical conditions
                result = 0
            else:
                # intermediate conditions
                result = 1
        else:
            if (wet_days(tp.iloc[i - 1: i + 1]).sum() >= 1) & (tmax.iloc[i] < 35) & (tp.iloc[i] < 15) &\
                    (cloud_cover.iloc[i] >= 50):
                result = 2
            elif (gust.iloc[i] >= 50) | (tmax.iloc[i] >= 38) & (cloud_cover.iloc[i] <= 20):
                # critical conditions
                result = 0
            else:
                # intermediate conditions
                result = 1

        list_conditions.append(result)

    return pd.Series(list_conditions, index=tp.index, dtype="int")


def irrigation(tp_histo: pd.Series,
               tp: pd.Series,
               etp: pd.Series,
               ) -> pd.Series:
    """

    Irrigation indicator. Guidance for irrigation activities.

    Args:
        tp_histo: recent history (last month) of daily rainfall
            The data are from observations or rainfall estimates (TAMSAT) depending their avaibility [mm]
        tp: daily rainfall forecast data [mm]
        etp: daily evapotranspiration forecast data [mm]

    Returns:
        Condition values, either 0, 1, or 2.
    """

    list_conditions = []

    for i in range(0, len(tp)):
        # for first step, it requires the last observation.
        if i == 0:
            if (tp_histo.iloc[-1] <= 1) & (tp.iloc[i] <= 1) & (etp.iloc[i] >= 10) & (tp.iloc[i:i + 5].sum() <= 10):
                # ideal conditions
                result = 2
            elif (tp.iloc[i] >= 10) | (etp.iloc[i] <= 5) | (tp.iloc[i:i + 5].sum() >= 50):
                # critical conditions
                result = 0
            else:
                # intermediate conditions
                result = 1
        else:
            if (tp.iloc[i-1] <= 1) & (tp.iloc[i] <= 1) & (etp.iloc[i] >= 10) & (tp.iloc[i:i + 5].sum() <= 10):
                # ideal conditions
                result = 2
            elif (tp.iloc[i] >= 10) | (etp.iloc[i] <= 5) | (tp.iloc[i:i + 5].sum() >= 50):
                # critical conditions
                result = 0
            else:
                # intermediate conditions
                result = 1

        list_conditions.append(result)

    return pd.Series(list_conditions, index=tp.index, dtype="int")
