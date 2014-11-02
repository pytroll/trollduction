#!/bin/sh

if [ -f /etc/profile.d/smhi.sh ]
then
. /etc/profile.d/smhi.sh
fi

if [ $SMHI_DIST == 'linda' ]
then
SMHI_MODE='offline'
fi

case $SMHI_MODE in

################################################################################
# UTV

utv)

APPL_HOME="/data/proj6/safutv/src/pps_runner"
ACPG_HOME="/local_disk/opt/ACPG/current"
PPSRUNNER_LOG_FILE="/var/log/satellit/pps_runner.log"
PPSRUNNER_CONFIG_DIR=${APPL_HOME}
PPS_SCRIPT=${HOME}/src/pps_runner/pps_run.sh
DATA_ROOT="/san1"
LVL0_DATA_HOME="${DATA_ROOT}/polar_in"

        ;;


################################################################################
# Default

*)
echo "No SMHI_MODE set..."

   ;;

esac


export PPSRUNNER_LOG_FILE
export LVL0_DATA_HOME
export PPS_SCRIPT
export PPSRUNNER_CONFIG_DIR

. ${ACPG_HOME}/cfg/.profile_pps

PPS_LOG_FILE=/var/log/satellit/pps_runner.log
export PPS_LOG_FILE

/usr/bin/python ${APPL_HOME}/pps_runner.py
