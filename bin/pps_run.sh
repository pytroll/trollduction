#!/bin/bash

# $1 = Satellite
# $2 = Orbit number
# $3 = yyyymmdd
# $4 = hhmm

. /local_disk/opt/ACPG/current/cfg/.profile_pps
SM_PRODUCT_DIR=/data/proj/safutv/data/polar_out/direct_readout; export SM_PRODUCT_DIR
#PPS_LOG_FILE=${HOME}/src/pps_runner/pps_logfile.log; export PPS_LOG_FILE

python /local_disk/opt/ACPG/current/scr/ppsRunAllParallel.py -p $1 $2 --satday $3 --sathour $4
