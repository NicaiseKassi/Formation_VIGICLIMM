import typing as T
import pandas as pd
import xarray as xr
import numpy as np


def degree_days(base: T.Union[int, float],
                tmin: T.Union[pd.Series, pd.DataFrame, xr.DataArray, xr.Dataset] = None,
                tmax: T.Union[pd.Series, pd.DataFrame, xr.DataArray, xr.Dataset] = None,
                tmean: T.Union[pd.Series, pd.DataFrame, xr.DataArray, xr.Dataset] = None,
                index: str = "hot",
                cutoff_method: T.Optional[str] = None,
                cutoff_val: T.Optional[T.Union[int, float]] = None,
                **kwargs) -> T.Union[pd.Series, pd.DataFrame, xr.DataArray]:
    """
    Computes the growing degree days (GDD)

    Cutoff methods description:
        - The vertical cutoff method assumes that no development occurs when a temperature
        is above the upper threshold (T > cutoff T=0)

        - The horizontal cutoff method assumes that development continues at a constant
        rate at temperatures in excess of the upper threshold (T > cutoff T=cutoff)

    For further explanation, read [UC IPM - About degree-days](http://ipm.ucanr.edu/WEATHER/ddconcepts.html).

    Warning: the growing degree days should not be confused with the heating/cooling degree days, which give the
    heating/cooling requirements for a building at a specific location.

    The hot degree days are calculated in the same way as cooling degree days and refer to the heat accumulated
    above a temperature threshold (base).
    The cold degree days refer to temperatures below the threshold (same calculation as heating degree days).

    Args:
        tmin: Daily minimum temperature [°C]
        tmax: Daily maximum temperature [°C]
        tmean: Daily mean temperature [°C]. If tmin and tmax exist, no need to use tmean.
        base: Base temperature [°C]
        index: "hot" or "cold" for Hot/Cold needs of the plant, by default 'hot'
        cutoff_method: Choose between (None, ("h" or "horizontal"), ("v" or "vertical"))
        cutoff_val: Cutoff value
    Returns:
        Growing Degree Days (GDD)

    """
    cutoff_map = {"h": "horizontal", "v": "vertical"}
    cutoff_method = cutoff_map[cutoff_method] if cutoff_method in cutoff_map.keys() else cutoff_method

    # Metadata will only be included on xr.DataArray or xr.Dataset.
    metadata = {"Parameter": f"{index.capitalize()} degree days",
                "Base temperature": base,
                "Cutoff method": cutoff_method,
                "Cutoff value": cutoff_val, }

    assert not all((par is None for par in [tmean, tmax, tmin])), "Please enter valid data for (tmax and tmin) or tmean"

    if tmin is not None and tmax is not None:
        assert tmean is None, "Use either tmax and tmin or only tmean"
        tmin_val = _get_data_values(tmin)
        tmax_val = _get_data_values(tmax)
        tmean_val = (tmax_val + tmin_val) / 2
        tmean = _make_dataset_from_data(data=tmean_val, index_ds=tmax, name="tmean")

    dd_values = _degree_days_from_tmean(tmean=tmean, base=base, index=index,
                                        cutoff_method=cutoff_method, cutoff_val=cutoff_val)
    return _make_dataset_from_data(data=dd_values, index_ds=tmean, name="dd", attrs=metadata)


def _degree_days_from_tmean(tmean: T.Union[pd.Series, pd.DataFrame, xr.DataArray, xr.Dataset],
                            base: T.Union[int, float],
                            index: str = "hot",
                            cutoff_method: T.Optional[str] = None,
                            cutoff_val: T.Optional[T.Union[int, float]] = None,
                            **kwargs) -> T.Union[np.ndarray, pd.Series, pd.DataFrame, xr.DataArray]:
    """
    Computes the cold/hot degree days based on mean temperature
    Args:
        tmean: Daily mean temperature
        base: Base temperature
        index: "hot" or "cold" for Hot/Cold Degree Days
        cutoff_method: Choose between (None, ("h" or "horizontal"), ("v" or "vertical"))
        cutoff_val: Cutoff value
    Returns:
        Cold/Hot Degree Days
    """
    tmean_val = _get_data_values(tmean)

    if cutoff_method is None or cutoff_val is None:
        dd_values = _no_cutoff_degree_days_from_tmean(tmean=tmean_val, base=base, index=index)
    elif cutoff_method == "vertical":
        dd_values = _cutoff_vertical_degree_days_from_tmean(
            tmean=tmean_val, base=base, cutoff_val=cutoff_val, index=index)
    elif cutoff_method == "horizontal":
        dd_values = _cutoff_horizontal_degree_days_from_tmean(
            tmean=tmean_val, base=base, cutoff_val=cutoff_val, index=index)
    else:
        raise ValueError("Please give a valid cutoff method.")

    return dd_values


def _no_cutoff_degree_days_from_tmean(tmean: T.Union[np.ndarray, pd.Series, pd.DataFrame, xr.DataArray],
                                      base: T.Union[int, float],
                                      index: str = "hot",
                                      **kwargs) -> T.Union[np.ndarray, pd.Series, pd.DataFrame, xr.DataArray]:
    """
    Computes the cold/hot degree days
    Args:
        tmean: Daily mean temperature
        base: Index base
        index: "hot" or "cold"
    Returns:
        Array containing the Cold/Hot Degree Days
    """
    if index == "cold":
        diff = base - tmean
    elif index == "hot":
        diff = tmean - base
    neg_diff_mask = diff <= 0
    diff[neg_diff_mask] = 0
    return diff


def _cutoff_vertical_degree_days_from_tmean(tmean: T.Union[np.ndarray, pd.Series, pd.DataFrame, xr.DataArray],
                                            base: T.Union[int, float],
                                            cutoff_val: T.Union[int, float],
                                            index: str = "hot",
                                            **kwargs) -> T.Union[np.ndarray, pd.Series, pd.DataFrame, xr.DataArray]:
    """
    Computes the cold/hot degree days
    Args:
        tmean: Daily mean temperature
        base: Index base
        index: "hot" or "cold"
        cutoff_val: cutoff value
    Returns:
        Array containing the Cold/Hot Degree Days
    """
    if index == "cold":
        diff = base - tmean
        cutoff_diff = base - cutoff_val
    elif index == "hot":
        diff = tmean - base
        cutoff_diff = cutoff_val - base
    neg_diff_mask = diff <= 0
    diff[neg_diff_mask] = 0
    pos_diff_mask = diff >= cutoff_diff
    diff[pos_diff_mask] = 0
    return diff


def _cutoff_horizontal_degree_days_from_tmean(tmean: T.Union[np.ndarray, pd.Series, pd.DataFrame, xr.DataArray],
                                              base: T.Union[int, float],
                                              cutoff_val: T.Union[int, float],
                                              index: str = "hot",
                                              **kwargs) -> T.Union[np.ndarray, pd.Series, pd.DataFrame, xr.DataArray]:
    """
    Computes the cold/hot degree days
    Args:
        tmean: Daily mean temperature
        base: Index base
        index: "hot" or "cold"
        cutoff_val: cutoff value
    Returns:
        Array containing the Cold/Hot Degree Days
    """
    if index == "cold":
        diff = base - tmean
        cutoff_diff = base - cutoff_val
    elif index == "hot":
        diff = tmean - base
        cutoff_diff = cutoff_val - base
    neg_diff_mask = diff <= 0
    diff[neg_diff_mask] = 0
    pos_diff_mask = diff >= cutoff_diff
    diff[pos_diff_mask] = cutoff_diff
    return diff


def _get_data_values(data: T.Union[pd.Series, pd.DataFrame, xr.DataArray,
                                   xr.Dataset]) -> np.ndarray:
    """ Get data values as a np.ndarray """
    if isinstance(data, (pd.Series, pd.DataFrame)):
        return data.to_numpy()
    elif isinstance(data, (xr.DataArray,)):
        return data.values
    elif isinstance(data, (xr.Dataset,)):
        return _to_xr_DataArray(data).values
    else:
        raise TypeError("Wrong data format, must be a pd.Series, pd.DataFrame, xr.DataArray or xr.Dataset")


def _to_xr_DataArray(data: xr.Dataset) -> xr.DataArray:
    """
    Takes a xarray dataset with a single variable and returns
    a xarray dataArray
    """
    ds_variables = list(data.var())
    assert len(ds_variables) == 1, AssertionError(
        "Invalid for multivariable Datasets.")
    var = ds_variables[0]
    return data[var]


def _make_dataset_from_data(data: np.typing.ArrayLike,
                            index_ds: T.Union[pd.Series, pd.DataFrame, xr.DataArray, xr.Dataset],
                            name: str = "",
                            attrs: T.Optional[dict] = None,
                            **kwargs) -> T.Union[pd.Series, pd.DataFrame, xr.DataArray, xr.Dataset]:
    """
    Generate (pd.Series, pd.DataFrame, xr.DataArray, xr.Dataset) with data in `data` arg and index/coords
    in `index_ds`. `data` and `index_ds` must have the same shape.
    """
    if isinstance(index_ds, pd.Series):
        return pd.Series(data, name=name, index=index_ds.index, **kwargs)
    elif isinstance(index_ds, pd.DataFrame):
        return pd.DataFrame(data={name: data}, index=index_ds.index, **kwargs)
    elif isinstance(index_ds, (xr.DataArray)):
        return xr.DataArray(data=data,
                            dims=index_ds.dims,
                            coords=index_ds.coords,
                            name=name,
                            attrs=attrs,
                            **kwargs)
    elif isinstance(index_ds, (xr.Dataset)):
        return xr.DataArray(data=data,
                            dims=index_ds.dims,
                            coords=index_ds.coords,
                            name=name,
                            attrs=attrs,
                            **kwargs).to_dataset()
    else:
        raise TypeError("Wrong data format, must be a pd.Series, pd.DataFrame, xr.DataArray or xr.Dataset")
