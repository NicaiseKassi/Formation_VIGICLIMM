#!/bin/bash

set -e

##################################
# Dynamic variable configuration #
##################################
# Daily variables configuration
export RUNDATE_YEAR="${CIPSTC_SCHED_UTC_ISODATETIME:0:4}"
export RUNDATE_MONTH="${CIPSTC_SCHED_UTC_ISODATETIME:5:2}"
export RUNDATE_DAY="${CIPSTC_SCHED_UTC_ISODATETIME:8:2}"
export RUN_DATE=${RUNDATE_YEAR}${RUNDATE_MONTH}${RUNDATE_DAY}

export INPUT_DIR=${CIPDS_GFS_DIR}/${RUNDATE_YEAR}/${RUNDATE_MONTH}/${RUNDATE_DAY}/run${RUN_HOUR}/

printenv | sort

###################
# Data fetching   #
###################
# TODO