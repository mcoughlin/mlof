
# Environment

source /root/anaconda3/bin/activate spectro
export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH
export PATH=/opt/PrincetonInstruments/picam/samples/projects/gcc/objlin/x86_64/debug:$PATH

sudo insmod /home/labuser/Code/Spectrograph/fliusb

# ATIK Filter Wheel

(Matthew Tran, tran0923@umn.edu) wrote a small python module to wrap Atik’s C/C++ SDK for the filter wheel. All core methods available in Atik’s C/C++ SDK are exposed through this module. A simple Python class (AtikFilterWheel) has been implemented for convenience.

Here are some useful resources about the Atik SDK in general:
- Download the C/C++ SDK: https://www.atik-cameras.com/software-downloads/
- See Atik’s C/C++ Documentation: https://www.atik-cameras.com/wp-content/uploads/AtikSDKDocumentation/_atik_cameras_8h.html
- Download the Python SDK (this is for Atik cameras ONLY! See my script for filter wheel control.) https://www.atik-cameras.com/software-downloads/

## Install
This should already be installed on the computer in the lab (the acer one).
1. Download the SDK from here: https://www.atik-cameras.com/software-downloads/
2. Navigate to lib/linux and read the README
3. Copy atik.rules to /usr/lib/udev/rules.d
sudo cp atik.rules /usr/lib/udev/rules.d
4. Copy the 64 bit library (no fly capture) into /usr/lib/
`sudo cp libatikcameras.so /usr/lib/AtikCameras`
The renaming here is critical!
5. Make another copy of the library
`sudo cp /usr/lib/AtikCameras /usr/lib/libatikcameras.so`
- For some reason, Python’s ctypes library cannot find the device when this isn’t present.
- This is CRITICAL for the filter wheel control module I wrote atik_filter_wheel.py
6. Copy the file `atik_filter_wheel.py` into that the script you’re working on is in

