#!/usr/bin/env bash
#
# Simulate some CIPS DS data -- Only useful for CI or local test
#
set -e
set -x

# Daily variables configuration
export RUNDATE_YEAR="${CIPSTC_SCHED_UTC_ISODATETIME:0:4}"
export RUNDATE_MONTH="${CIPSTC_SCHED_UTC_ISODATETIME:5:2}"
export RUNDATE_DAY="${CIPSTC_SCHED_UTC_ISODATETIME:8:2}"
export RUN_DATE=${RUNDATE_YEAR}${RUNDATE_MONTH}${RUNDATE_DAY}

#
# Simulate GFS
#
# Variable set from project.yml
export CIPSDS_GFS_DIR=${CIPSDS_GFS_DIR}/${RUNDATE_YEAR}/${RUNDATE_MONTH}/${RUNDATE_DAY}/run${RUN_HOUR}
mkdir -p ${CIPSDS_GFS_DIR} && cd ${CIPSDS_GFS_DIR} || exit

# Download static files
wget -nv -nc http://data.mfi.inte/data_samples/MFI/CI_TEST_DATA/nwp/GFS/A_HGFS00KWBC190300_C_KWBC_20230719033503_gfs.t00z.pgrb2.0p25.f000_all_R20230719000000_20230719000000_20230719000000.grib2
wget -nv -nc http://data.mfi.inte/data_samples/MFI/CI_TEST_DATA/nwp/GFS/A_HGFS00KWBC230300_C_KWBC_20240123034212_gfs.t00z.pgrb2.0p25.f024_all_R20240123000000_20240124000000_20240124000000.grib2

ls -lh ${CIPSDS_GFS_DIR}


#
# Simulate ERA5 Land
#
mkdir -p ${CIPSDS_ERA5_DIR} && cd ${CIPSDS_ERA5_DIR} || exit
wget -nv -nc http://data.mfi.inte/data_samples/Ivory_Coast/VIGICLIMM/RAW_DATA/ERA5Land/ERA5Land_2024.nc
ls -lh ${CIPSDS_ERA5_DIR}


#
# Simulate TAMSAT : TODO
#
mkdir -p ${CIPSDS_TAMSAT_DIR} && cd ${CIPSDS_TAMSAT_DIR} || exit
wget -nv -nc http://data.mfi.inte/data_samples/MFI/CI_TEST_DATA/satellite/TAMSAT/tamsat_2024.nc

ls -lh $CIPSDS_TAMSAT_DIR
