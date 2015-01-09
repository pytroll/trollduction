#!/bin/bash

# $1 = Satellite
# $2 = Orbit number
# $3 = yyyymmdd
# $4 = hhmm
# $5 = lvl1_dir

. /local_disk/opt/acpg/cfg/.profile_pps

if [ "x$5" != "x" ]; then
    SM_AAPP_DATA_DIR=$5
    export SM_AAPP_DATA_DIR
    echo "Level 1 dir = $SM_AAPP_DATA_DIR"
fi

if [ "x$3" == "x0" ] && [ "x$4" == "x0" ]; then
    python /local_disk/opt/acpg/scr/ppsRunAllParallel.py -p $1 $2
else
    python /local_disk/opt/acpg/scr/ppsRunAllParallel.py -p $1 $2 --satday $3 --sathour $4
fi
