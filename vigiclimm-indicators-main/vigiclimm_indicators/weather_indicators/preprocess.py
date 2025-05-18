import os
import xarray as xr
import typing as T


def preprocess_gfs(ds_path: T.Union[str, os.PathLike],
                   par_name: str,
                   lat_station: T.Union[int, float],
                   lon_station: T.Union[int, float],
                   convert: bool = False
                   ) -> xr.DataArray:
    """
    Extract GFS forecast data for a specific location and apply a unit conversion and a resampling.

     Args:
         ds_path: Path of the GFS NetCDF file
         par_name: Name of the parameter that we are interested in
         lat_station: Latitude of the station
         lon_station: Longitude of the station
         convert: If True, convert to an appropriate units. Set to False by default

    Returns:
        A DataArray containg the daily values of the selected parameter at the station.
    """

    ds = xr.open_dataset(ds_path)

    ds = ds.rename({"valid_time": "time"})

    if par_name in ['tmax', 'tmin', 'tmean']:
        ds_par_name = '2t'
    elif par_name in ['rhmax', 'rhmin', 'rhmean']:
        ds_par_name = '2r'
    else:
        ds_par_name = par_name

    # get the data at the station
    data = ds[ds_par_name].sel(latitude=lat_station, longitude=lon_station, method='nearest')
    # get daily resampled values
    data = _daily_resample(data, par_name)
    # Only up to the D+10 forecasts
    data = data.head(time=10)

    # units conversion if needed
    if convert:
        data = _convert_units(data, par_name)

    return data.round(1)


def _daily_resample(ds: xr.DataArray, par_name: str) -> xr.DataArray:
    method = {
        'tmax': 'max',
        'tmin': 'min',
        'tmean': 'mean',
        'tp': 'sum',
        'gust': 'max',
        '10ws': 'mean',
        '10u': 'mean',
        '10v': 'mean',
        'dswrf': 'mean',
        '2d': 'mean',
        'rhmax': 'max',
        'rhmin': 'min',
        'rhmean': 'mean',
        'lcc': 'mean',
        'mcc': 'mean'
    }
    return getattr(ds.resample(time='D'), method[par_name])()


def _convert_units(ds: xr.DataArray, par_name: str) -> xr.DataArray:
    if par_name in ['gust', '10u', '10v', '10ws']:
        ds = ds * 3.6  # m/s tp km/h
    if par_name in ['tmean', 'tmax', 'tmin', '2d']:
        ds = ds - 273.15  # K to °C
    if par_name == 'dswrf':
        ds = ds * 0.0864  # W/m2 tp MJ/m2
    return ds
