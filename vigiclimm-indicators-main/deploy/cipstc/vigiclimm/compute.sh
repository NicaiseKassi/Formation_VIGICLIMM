#!/bin/bash
set -e
set -x


# Daily variables configuration
export RUNDATE_YEAR="${CIPSTC_SCHED_UTC_ISODATETIME:0:4}"
export RUNDATE_MONTH="${CIPSTC_SCHED_UTC_ISODATETIME:5:2}"
export RUNDATE_DAY="${CIPSTC_SCHED_UTC_ISODATETIME:8:2}"
export RUN_DATE=${RUNDATE_YEAR}${RUNDATE_MONTH}${RUNDATE_DAY}

mkdir -p ${WORKING_DIR}
mkdir -p ${WORKING_DIR}/input/ ${WORKING_DIR}/output/


#
# Convert GFS from grib to netcdf
#
nwp-convert-grib-extractor --config-file ${CIPSDS_STATIC}/gfs_to_nc.yml \
  --input-dir ${CIPSDS_GFS_DIR}/${RUNDATE_YEAR}/${RUNDATE_MONTH}/${RUNDATE_DAY}/run${RUN_HOUR} \
  --output-dir ${WORKING_DIR}/gfs \
  --input-filename-template *gfs*grib \
  --output-filename gfs.nc

#
# Run forecast
#
vi-run-forecast --yml-path ${CIPSDS_STATIC}/station_list.yaml \
  --ds-path ${WORKING_DIR}/gfs/gfs.nc \
  --outdir ${WORKING_DIR}/output/

#
# Compute indicators
#
vi-run-historical --yml-path ${CIPSDS_STATIC}/station_list.yaml  \
  --obs-path /tmp/ \
  --era5land-path ${CIPSDS_ERA5_DIR}/${RUNDATE_YEAR}/ERA5Land_${RUNDATE_YEAR}.nc \
  --tamsat-path ${CIPSDS_TAMSAT_DIR}/${RUNDATE_YEAR}/TAMSAT_${RUNDATE_YEAR}.nc \
  --gfs-path ${WORKING_DIR}/gfs/gfs.nc \
  --outdir ${WORKING_DIR}/output/


#
# Compute agro indicators
#
vi-run-agro --yml-path ${CIPSDS_STATIC}/station_list.yaml  \
  --input-path ${WORKING_DIR}/output \
  --outdir ${WORKING_DIR}/output

ls -Rlh ${WORKING_DIR}/output
