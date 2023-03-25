"""
Written by Matthew Tran (tran0923@umn.edu, 3/24/2023)
Wraps all of Atik's filter wheel control methods from (C/C++) in a Pythonic object.
Broadly modelled after Atik's Python Camera SDK

See Here for general documentation for Atik's C/C++ SDK:
	(All methods that are available are documented here, making this a critical resource for working with
	 their hardware)
	https://www.atik-cameras.com/wp-content/uploads/AtikSDKDocumentation/_atik_cameras_8h.html

See Here to Download Atik's SDK: https://www.atik-cameras.com/software-downloads/

See Atik's Python SDK (__init__.py) for further reference on how this was written.
	(Downloadable here: https://www.atik-cameras.com/software-downloads/)


After proper installation, this module will allow a user to use an Atik Filter wheel in Python.
See the class for documentation on the methods.
"""

import sys
import time
from ctypes import *
import ctypes
from enum import Enum
from enum import IntEnum

import numpy as np

"""
Load the .dll/.so for ATIK
- This probably could be more robust. But, this will work most likely.
"""
try:
    # Will look for AtikCameras.dll
    dll = CDLL("AtikCameras.dll")
except Exception:
    try:
        # Will look for libatikcameras.so
        dll = CDLL("/usr/lib/atikcameras.so")
    except Exception as e:
        sys.stderr.write("Failed to load AtikCameras library. Make sure Atik SDK prerequisites or Atik Core SDK are installed\n")
        raise
"""
Status and Errors
"""
error_strings = {
    0: "ARTEMIS_OK",
    1: "ARTEMIS_INVALID_PARAMETER",
    2: "ARTEMIS_NOT_CONNECTED",
    3: "ARTEMIS_NOT_IMPLEMENTED",
    4: "ARTEMIS_NO_RESPONSE",
    5: "ARTEMIS_INVALID_FUNCTION",
    6: "ARTEMIS_NOT_INITIALIZED",
    7: "ARTEMIS_OPERATION_FAILED",
}

class ARTEMISEFWTYPE(IntEnum):
	ARTEMIS_EFW1 = 1
	ARTEMIS_EFW2 = 2

def validate_status_code(status):
	if (not status == 0):
		raise Exception(f"Failure Encountered: {error_strings[status]}")

"""
Setup Various Bindings for the Filter Wheel Functions
	This binds the C/C++ library calls to Python functions with strict typing.
	These should not be used directly by the end user, use the AtikFilterWheel class!
	See the Atik C/C++ documentation for more details.
"""
# how many devices are connected
ArtemisRefreshDevicesCount = dll.ArtemisRefreshDevicesCount
ArtemisRefreshDevicesCount.restype = c_int

ArtemisDeviceCount = dll.ArtemisDeviceCount
ArtemisDeviceCount.restype = c_int

# filter wheel methods
ArtemisEFWConnect = dll.ArtemisEFWConnect
ArtemisEFWConnect.restype = c_void_p
ArtemisEFWConnect.argtypes = [c_int]

ArtemisEFWDisconnect = dll.ArtemisEFWDisconnect
ArtemisEFWDisconnect.restpe = c_int
ArtemisEFWDisconnect.argtypes = [c_void_p]

# meta data
ArtemisEFWGetDetails = dll.ArtemisEFWGetDetails
ArtemisEFWGetDetails.restype = c_int
ArtemisEFWGetDetails.argtypes = [c_void_p, c_void_p, c_char_p]

ArtemisEFWGetDeviceDetails = dll.ArtemisEFWGetDeviceDetails
ArtemisEFWGetDeviceDetails.restype = c_int
ArtemisEFWGetDeviceDetails.argtypes = [c_int, c_void_p, c_char_p]

# connection info
#	Connect to the Filter Wheel
ArtemisEFWIsConnected = dll.ArtemisEFWIsConnected
ArtemisEFWIsConnected.restype = c_bool
ArtemisEFWIsConnected.argtypes = [c_void_p]
#	Filter Wheel is Present
ArtemisEFWIsPresent = dll.ArtemisEFWIsPresent
ArtemisEFWIsPresent.restype = c_bool
ArtemisEFWIsPresent.argtypes = [c_int]

# retrieve the number of filters in the wheel
ArtemisEFWNmrPosition = dll.ArtemisEFWNmrPosition
ArtemisEFWNmrPosition.restype = c_int
ArtemisEFWNmrPosition.argtypes = [c_void_p, POINTER(c_int)]

# get the filter wheel position
ArtemisEFWSetPosition = dll.ArtemisEFWSetPosition
ArtemisEFWSetPosition.restype = c_int
ArtemisEFWSetPosition.argtypes = [c_void_p, c_int]

ArtemisEFWGetPosition = dll.ArtemisEFWGetPosition
ArtemisEFWGetPosition.restype = c_int
ArtemisEFWGetPosition.argtypes = [c_void_p, POINTER(c_int), POINTER(c_bool)]

"""
Methods
"""
def get_available_atik_devices():
	"""! Retrieve the number of available ATIK devices
	@return	An integer number of conencted and available devices
	"""
	ArtemisRefreshDevicesCount()
	
	return ArtemisDeviceCount()

"""
Filter Wheel Class
"""
class AtikFilterWheel:
	"""!
	Atik Filter Wheel for controlling a filter wheel
	
	Typical usage:
	1) Initialize the class
		fw = AtikFilterWheel()
	2) Connect to a specific focus wheel
		fw.connect(0)
	3) Run any operations you want from there
	"""
	def __init__(self):
		"""! Initialize the filter wheel class
		"""
		self._handle = None
		self.device_index = None
	
	def __del__(self):
		"""! Disconnect from the filter wheel
		"""
		self.disconnect()

	def _check_connected(func):
		# decorator for functions which require valid handles
		def wrapper(self, *args, **kwargs):
			if not self.is_connected():
				raise Exception("Filter wheel is not connected. Use connect() before using the filter wheel.")
			
			return func(self, *args, **kwargs)

		return wrapper

	def connect(self, filter_wheel_index: int=0):
		"""! Connect to an AtikFilterWheel
		@param 	filter_wheel_index	Which filter wheel to connect to
		"""
		if filter_wheel_index == self.device_index and self.is_connected():
			return
		
		# attempt to connect to the filter wheel
		attempts = 0
		
		while not ArtemisEFWIsPresent(filter_wheel_index):
			time.sleep(0.1)
			attempts += 1
			if attempts > 10:
				raise Exception(f"Could not detect Atik Camera at index {camera_index}")
		
		self._handle = ArtemisEFWConnect(filter_wheel_index)
		
		if not self._handle:
			raise Exception(f"Could not conenct to the Atik Filter Wheel at {filter_wheel_index}")
		else:
			# successfully connected
			self.device_index = filter_wheel_index

	def disconnect(self):
		"""! Disconnect from the current filter wheel
		"""
		if self.is_connected():
			status = ArtemisEFWDisconnect(self._handle)
			try:
				validate_status_code(status)
			except Exception as e:
				raise Exception(f"Failed to disconnect from the filter wheel. Status Code: {status}")

	def is_connected(self) -> bool:
		"""! Whether the current filter wheel is connected
		@return	Whether the filter wheel is connected
		"""
		return bool(self._handle) and ArtemisEFWIsConnected(self._handle)

	@_check_connected
	def get_number_of_filters(self):
		"""! Retrieve the number of available filter slots. 
			 This is the number of possible positions that can be reached using the wheel.
		@return	The number of wheel/filter positions
		"""
		number_of_filters = c_int()
		
		status = ArtemisEFWNmrPosition(self._handle, byref(number_of_filters))
		validate_status_code(status)
		
		return number_of_filters.value
	
	
	@_check_connected
	def get_position(self):
		"""! Retrieve the current position index of the filter wheel
		@return	The position index of the filter wheel
		"""
		current_position = c_int()
		is_moving = c_bool()
		
		status = ArtemisEFWGetPosition(self._handle, byref(current_position), byref(is_moving))
		validate_status_code(status)
		
		return current_position.value

	@_check_connected
	def is_moving(self):
		"""! Check whether the filter wheel is currently moving
		@return	Whether the filter wheel is moving
		"""
		current_position = c_int()
		is_moving = c_bool()
		
		status = ArtemisEFWGetPosition(self._handle, byref(current_position), byref(is_moving))
		validate_status_code(status)
		
		return is_moving.value

	@_check_connected
	def set_position(self, position, delay=0.01):
		"""! Set the position of the filter wheel
		@param position	The desired position index for the filter wheel. Must be in range.
		@param delay	The time to wait while polling whether the filter wheel is moving
		"""
		number_of_filters = self.get_number_of_filters()
		if (position < 0 or number_of_filters <= position):
			raise IndexError(f"Invalid focus wheel position selected. Valid range: [0, {number_of_filters})")
		desired_position = c_int(position)
		
		status = ArtemisEFWSetPosition(self._handle, desired_position)
		validate_status_code(status)
		
		# busy wait until the move has completed
		if delay and delay > 0.0:
			while self.is_moving():
				time.sleep(delay)
	
	@_check_connected
	def get_details(self):
		"""! Retrieve various details about the filter wheel including type and serial number
		@return	(filter_wheel_type, serial_number)
		"""
		filter_wheel_type = c_uint()
		serial_number = create_string_buffer(100)
		
		status = ArtemisEFWGetDetails(self._handle, byref(filter_wheel_type), serial_number)
		validate_status_code(status)
		
		return ARTEMISEFWTYPE(filter_wheel_type.value), int(serial_number.value.decode("UTF-8"))
	
	"""
	Static Methods
	"""
	def get_device_details(filter_index):
		"""! Retrieve various details from a filter wheel including type and serial number
		@param filter_index	The filter to query for details
		@return	(filter_wheel_type, serial_number)
		"""
		index = c_int(filter_index)
		filter_wheel_type = c_uint()
		serial_number = create_string_buffer(100)
		
		status = ArtemisEFWGetDeviceDetails(index, byref(filter_wheel_type), serial_number)
		validate_status_code(status)
		
		return ARTEMISEFWTYPE(filter_wheel_type.value), int(serial_number.value.decode("UTF-8"))
	
	def get_available_filter_wheels():
		"""! Retrieve a list of the filter wheel indecies that are available for use
		@return	A list of filter wheel indecies from all connected AtikDevices
		"""
		number_of_devices = get_available_atik_devices()

		"""
		BUG: not sure why but the number of detected devices is zero with only the Filter Wheel attached.
		Not sure if ArtemisDeviceCount counts filter wheels or not
		"""
		if (number_of_devices == 0):
			# set the number of devices to 10 just so we can definitely query whether there are devices available
			number_of_devices = 10
		
		found_device_indecies = []
		for i in range(number_of_devices):
			if ArtemisEFWIsPresent(i):
				found_device_indecies.append(i)
		
		return found_device_indecies
	
	def connect_to_filter_wheel_by_serial(serial_number):
		"""! Connect to a filter wheel by its serial number
		@param serial_number	The serial number of the filter wheel
		"""
		wheel_indecies = AtikFilterWheel.get_available_filter_wheels()
		for index in wheel_indecies:
			filter_wheel_type, found_serial_number = AtikFilterWheel.get_device_details(index)
			if found_serial_number == serial_number:
				fw = AtikFilterWheel()
				fw.connect(index)
				return fw
		raise Exception(f"Filter Wheel with serial number {serial_number} is not connected")

if __name__ == "__main__":
	"""	
	Short demo of how to use the AtikFilterWheel class
	"""
	# this is not working for some reason but is not critical
	# connected_devices = get_available_atik_devices()
	# print(f"Connected Atik Devices: {connected_devices}")
	
	# List All Available Filter Wheels (by device index)
	# available_filter_wheel_indecies = AtikFilterWheel.get_available_filter_wheels()
	# print(available_filter_wheel_indecies)
	
	"""
	1) Connect to the filter wheel
	"""
	print("Connecting to the filter wheel")
	# connect to a filter wheel directly
	my_filter_wheel = AtikFilterWheel() # when initializing, make sure to connect afterwards
	my_filter_wheel.connect(0)
	
	# connect to a filter wheel by serial number
	# device_serial_number = 1210320
	# my_filter_wheel = AtikFilterWheel.connect_to_filter_wheel_by_serial(device_serial_number)
	print("Connected to the filter wheel")
	print()

	"""
	2) Filter Wheel Properties (position, serial number, etc.)
	"""
	# retrieve the filter wheel position
	print("Filter Wheel Properties:")
	filter_wheel_type, serial_number = my_filter_wheel.get_details()

	# static call to get the filter wheel type and serial number
	# filter_wheel_type, serial_number = AtikFilterWheel.get_details(0)

	print(f"Filter Wheel Type: {filter_wheel_type} Serial Number: {serial_number}")
	
	position = my_filter_wheel.get_position()
	is_moving = my_filter_wheel.is_moving()
	print(f"Filter Wheel Position: {position} Is Moving: {is_moving}")
	
	# retrieve the number of filters available
	number_of_filters = my_filter_wheel.get_number_of_filters()
	print(f"Number of Filters: {number_of_filters}")
	print()
	
	"""
	Demo Setting the Filter Wheel Position to All Possible States
	"""
	print("Setting the Filter Wheel's Position")
	for i in range(number_of_filters):
		try:
			print(f"\t Moving to position {i}")
			my_filter_wheel.set_position(i)
			time.sleep(1.0)
		except Exception as e:
			print(f"Failed to set the filter wheel position to {i}")
			print(e)

	print()
	print("Returning to the initial position")
	my_filter_wheel.set_position(position)

	# Disconnecting from the filter is managed by AtikFilterWheel's deconstructor
	
