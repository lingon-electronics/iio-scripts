#!/bin/bash
#
# This is a script which periodically calls a single-shot
# readout from a connected 3d Accelerometer sensor that
# communicates with the Linux IIO sensor driver "accel_3d".
#
# When the sensor isn't vertical (with some margin of error),
# the user is automatically logged out.
#
# This script should not be run with sudo privilegies.
#
#
# License: CC-BY 4.0
# Lingon Electronics, 2018.
#

LIMIT=$(echo "0.4")
USER=$(whoami)

if [ "$USER" = "root" ]; then
  echo ""
  echo " Error: This script should not be run by root!"
  echo ""
  echo " HINT: You might need to set the executable flag for your user:"
  echo "    sudo chmod +x filename.sh"
  echo ""
  exit
fi

while [ "1" ];
do
  IIO_DEVICE_ACCELEROMETER=$(echo | find -O3 -L /sys/bus/iio/devices -maxdepth 2 -name "in_accel_scale" | grep -o -E '/sys/bus/iio/devices/iio:device[0-9]+/' | head -n1 | cat)

  X=$(echo | cat $IIO_DEVICE_ACCELEROMETER"in_accel_x_raw" | grep -o -E '[+-]?[0-9]+')
  Y=$(echo | cat $IIO_DEVICE_ACCELEROMETER"in_accel_y_raw" | grep -o -E '[+-]?[0-9]+')
  Z=$(echo | cat $IIO_DEVICE_ACCELEROMETER"in_accel_z_raw" | grep -o -E '[+-]?[0-9]+')

  XZ=$(echo "a($X/($Z+0.001))" | bc -l)
  YZ=$(echo "a($Y/($Z+0.001))" | bc -l)

  if (( $(echo "$XZ >  $LIMIT" | bc -l) )) ||
     (( $(echo "$XZ < -$LIMIT" | bc -l) )) ||
     (( $(echo "$YZ >  $LIMIT" | bc -l) )) ||
     (( $(echo "$YZ < -$LIMIT" | bc -l) ));
  then
    pkill -KILL -u $USER
  fi

  sleep 0.1
done
