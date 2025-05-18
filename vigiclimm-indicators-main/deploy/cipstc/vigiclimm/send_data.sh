#!/bin/bash

###################
# General variables configuration #
###################################

set -e	# Exit on any error

if [ -z "$TTAAII" ];      then echo "Missing env var TTAAII"; exit 1; fi
if [ -z "$CCCC" ];        then echo "Missing env var CCCC"; exit 1; fi
if [ -z "$RESULTS_DIR" ]; then echo "Missing env var RESULTS_DIR"; exit 1; fi
if [ -z "$OUTNAME" ];     then OUTNAME=out; fi

DATE=$(date +"%d%H%M")
DATESEND=$(date +"%Y%m%d%H%M%S")
TRANSMET_HEADER=A_${TTAAII}${CCCC}${DATE}_C_${CCCC}_${DATESEND}

###################
# Data processing #
###################

echo "Starting data processing..."
mkdir -p "${RESULTS_DIR}/${OUTNAME}"

# Rename output files for TRANSMET
cd $RESULTS_DIR
for f in $(find . -maxdepth 1 -type f)
do
    f=`basename $f`
    clean_f=$(echo "$f" | iconv -c -f UTF-8 -t ASCII//TRANSLIT)
    echo "$clean_f"
    ln -vs $PWD/$f ${RESULTS_DIR}/${OUTNAME}/${TRANSMET_HEADER}_${clean_f}
done
cd -

# Send the files to TRANSMET
lftp -u $FTP_USER:$FTP_PASSWD $FTP_DESTINATION <<EOF
set log:enabled/xfer yes
set log:file/xfer ""
set xfer:use-temp-file true
set xfer:temp-file-name *.tmp

cd $FTP_REPOSITORY
mput $RESULTS_DIR/${OUTNAME}/${TRANSMET_HEADER}_*
EOF


echo "Cleaning up ${PD_WORKING_DIR} ..."
rm -rf ${PD_WORKING_DIR}
