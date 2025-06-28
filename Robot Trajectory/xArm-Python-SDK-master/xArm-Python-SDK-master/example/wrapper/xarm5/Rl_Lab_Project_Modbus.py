#!/usr/bin/env python3
# Software License Agreement (BSD License)
#
# Copyright (c) 2019, UFACTORY, Inc.
# All rights reserved.
#
# Author: Vinman <vinman.wen@ufactory.cc> <vinman.cub@gmail.com>

"""
Description: Move Joint and Poll Modbus Registers
"""

import os
import sys
import time
import math

sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

import serial  # Import pyserial for serial communication

from xarm.wrapper import XArmAPI
from xarm.core.wrapper.uxbus_cmd_ser import UxbusCmdSer

# Setup serial communication with the peripheral device (using pyserial)
baudrate = 115200
serial_port = serial.Serial(port='/dev/ttyUSB0', baudrate=baudrate, timeout=1)  # Initialize serial port

# Initialize Modbus communication with the slave device
uxbus_cmd_ser = UxbusCmdSer(serial_port)  # Pass the serial port object, not a string

# Set Modbus IDs (Master -> xArm, Slave -> peripheral)
uxbus_cmd_ser.fromid = 1  # Master ID (xArm)
uxbus_cmd_ser.toid = 9    # Slave ID (connected device)

#######################################################
"""
Just for test example
"""
if len(sys.argv) >= 2:
    ip = sys.argv[1]
else:
    try:
        from configparser import ConfigParser
        parser = ConfigParser()
        parser.read('../robot.conf')
        ip = parser.get('xArm', 'ip')
    except:
        ip = '192.168.1.222'  # Default xArm IP address
        if not ip:
            print('input error, exit')
            sys.exit(1)
########################################################

arm = XArmAPI(ip)

arm.motion_enable(enable=True)
arm.set_mode(0)
arm.set_state(state=0)
error = arm.get_err_warn_code(show=True, lang='en')
print(error)
# arm.clean_error()
pos = arm.get_position(is_radian=False)
print(pos)

# Function to poll the slave device for Modbus registers
def poll_slave_registers(register_address, num_registers, timeout=2):
    # Send request to the slave
    uxbus_cmd_ser.send_modbus_request(register_address, [], 0)
    
    # Receive the response
    response = uxbus_cmd_ser.recv_modbus_response(0x03, None, num_registers, timeout)
    
    if response[0] == XCONF.UxbusState.ERR_TOUT:
        print("Timeout: No response from the slave device.")
    else:
        print(f"Received data from register {register_address}: {response[1:num_registers+1]}")
    
    return response

while 1:
    # Poll slave device before moving the xArm
    poll_slave_registers(0x0100, 2)  # Example: reading 2 registers starting at address 0x0100

    # Move the xArm to a new position
    speed = 750
    arm.set_position(x=-320.910126, y=-456.700107, z=400.215912, roll=180.00, pitch=0, yaw=-89.990814, is_radian=False, wait=True, speed=speed)
    pos = arm.get_position(is_radian=False)
    print(pos)

    # Poll again after the movement
    poll_slave_registers(0x0100, 2)

    # Move to another position
    speed = 50
    arm.set_position(x=-320.910126, y=-26.700107, z=400.215912, roll=180.00, pitch=0, yaw=-89.990814, is_radian=False, wait=True, speed=speed)
    pos = arm.get_position(is_radian=False)
    print(pos)

    # Poll again after the second movement
    poll_slave_registers(0x0100, 2)
