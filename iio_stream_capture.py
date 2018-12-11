#
#
# This is a Python 2 script for receiving a continuous stream of data,
# from the following IIO sensors:
#
# "accel_3d" (3D Accelerometer)
# "gyro_3d" (3D Gyroscope)
#
# The raw data is formatted into .csv before it's sent to stdout.
#
#
# It relies on IIO the tool "iio_readdev" from package "libiio-utils",
# as well as IIO sensor drivers which are included in most modern
# Linux distributions.
#
# Usage of sudo is normally required for iio_readdev.
#
# Example:
# sudo python2 iio_stream_capture.py > measurement.csv
#
#
# If multiple IIO sensors are connected to the computer, you can
# specify the index of the desired sensor by appending a number:
#
# sudo python2 iio_stream_capture.py 0 > measurement.csv
#
#
# License: CC-BY 4.0
# Lingon Electronics, 2018.
#


import subprocess
import threading
import time
import sys
import struct
import os
from distutils.spawn import find_executable

iio_device_default = 0   # Default to device 0
iio_samples = 0          # 0 = continuous

def iio_readdev_run(stop_event, iio_device_index, arg):
    iio_device_str = ("iio:device" + str(iio_device_index))
    iio_trigger_str = ("trigger" + str(iio_device_index))
    iio_samples_str = str(iio_samples)

    path = "/sys/bus/iio/devices/" + iio_device_str +"/"
    device_type = open(path + "name","rb").read().rstrip()

    scale = 1
    if device_type == "accel_3d":
        datalen = 24
        format_str = 'iiiil'
        scale = float(open(path + "in_accel_scale", "rb").read().rstrip())
    elif device_type == "gyro_3d":
        datalen = 12
        format_str = 'iii'
        scale = float(open(path + "in_anglvel_scale", "rb").read().rstrip())
    else:
        return -1

    iio_readdev_cmd = ("iio_readdev -t " + iio_trigger_str + " -b 50 -s "
        + iio_samples_str + " " + iio_device_str)
    process = subprocess.Popen(iio_readdev_cmd, shell=True,
        stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=sys.stderr)

    out = [0, 0, 0]
    while True:
        out_raw = process.stdout.read(datalen)

        if out_raw != "":
            output_data = struct.unpack(format_str, out_raw)
            out[0] = output_data[0] * scale;
            out[1] = output_data[1] * scale;
            out[2] = output_data[2] * scale;

            out_str = ', '.join(str(x) for x in out)+";\n"
            sys.stdout.write(out_str)
            sys.stdout.flush()
        else:
            break
        if stop_event.wait(0):
            break

    return process.returncode


def main():
    iio_device = iio_device_default
    iio_readdev_executable = find_executable("iio_readdev")

    if iio_readdev_executable is None:
        exit("This script requires iio_readdev in package libiio-utils\n"+
            "    sudo apt install libiio-utils\n")

    if os.geteuid() != 0:
        exit("This script requires root privilegies for iio_readdev.")

    if len(sys.argv) > 1:
        try:
            arg1 = int(sys.argv[1])
            if arg1 < 0:
                exit("Index can not be negative")
            else:
                iio_device = arg1
        except ValueError:
            exit("Index must be an integer. Default 0 (iio:device0)")


    thread_end_event = threading.Event()

    iio_thread = threading.Thread(target=iio_readdev_run,
        args=(thread_end_event, iio_device, "task"))
    iio_thread.setDaemon(True)
    iio_thread.start()

    while iio_thread.isAlive():
        time.sleep(0.1)

    thread_end_event.set()
    iio_thread.join()


if __name__ == "__main__":
    main()
