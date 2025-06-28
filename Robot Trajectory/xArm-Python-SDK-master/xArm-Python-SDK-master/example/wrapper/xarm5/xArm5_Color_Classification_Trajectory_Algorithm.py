
import os
import sys
import time
import math

sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from xarm.wrapper import XArmAPI
from pymodbus.client.sync import ModbusSerialClient

ip = '192.168.0.222'
arm = XArmAPI(ip)

arm.motion_enable(enable=True)
arm.set_mode(0)
arm.set_state(state=0)
arm.set_gripper_mode(0)
arm.set_gripper_enable(True)
arm.set_gripper_speed(5000)

y = -220
z = 175
tracking_speed = 50
mvacc = 500
x_red = -128
x_green = -128
green_tracker = 0
red_tracker = 0

def validate_position(x, y, z):
    limits = {'x': (-500, 500), 'y': (-500, 500), 'z': (0, 500)}
    return limits['x'][0] <= x <= limits['x'][1] and limits['y'][0] <= y <= limits['y'][1] and limits['z'][0] <= z <= limits['z'][1]
    
arm.set_position(x=-320.910126, y=y, z=400.215912, roll=180.00, pitch=0, yaw=-89.990814, is_radian=False, wait=True, speed=tracking_speed, mvacc=mvacc)
arm.set_gripper_position(850, wait=True)

# Modbus Client initialization
client = ModbusSerialClient(
    method='rtu',
    port='/dev/ttyS0',
    baudrate=115200,
    timeout=1,
    parity='N',
    stopbits=1,
    bytesize=8
)

def ModbusCommunications():
    '''Read data from Modbus.'''
    if client.connect():
        res = client.read_holding_registers(address=0, count=4, unit=1)
        client.close()
        return res
    else:
        print("Modbus connection failed.")
        return None

def wait_until_stopped():
    while arm.get_is_moving():
        time.sleep(0.1) 

# Continuous tracking loop
while True:
    res = ModbusCommunications()
    if res is not None and not res.isError():
        print(res)
        object_detect = res.registers[0]
        color = res.registers[1]
        x_coord = res.registers[2]
        y_coord = res.registers[3]

        if object_detect == 0 and 115 <= x_coord <= 125:
            print("Object in range. Picking up...")
            if validate_position(-320.91, y - 10, 245):
                arm.set_position(x=-320.910126, y=y - 10, z=245, roll=180.0, pitch=0, yaw=-89.99, is_radian=False, wait=False, speed=tracking_speed * 5)
                wait_until_stopped()  

                arm.set_gripper_position(300, wait=True)

                
                if color == 1:  # Red
                    red_tracker +=1
                    target_x, target_y = x_red, -227
                    if red_tracker == 3:
                      x_red = -128
                    x_red += 100
                else:  # Green
                    green_tracker +=1
                    target_x, target_y = x_green, -327
                    if green_tracker == 3:
                      x_green = 0
                    x_green += 100

                if validate_position(target_x, target_y, 400):
                    arm.set_position(x=target_x, y=target_y, z=400, roll=180.0, pitch=0, yaw=-89.99, is_radian=False, wait=False, speed=tracking_speed * 5)
                    wait_until_stopped()

                 
                    arm.set_position(x=target_x, y=target_y, z=175, roll=180.0, pitch=0, yaw=-89.99, is_radian=False, wait=True, speed=tracking_speed*5)

                    
                    arm.set_gripper_position(850, wait=True)

                    
                    arm.set_position(x=target_x, y=target_y, z=400, roll=180.0, pitch=0, yaw=-89.99, is_radian=False, wait=True, speed = tracking_speed *5)

            
            y = -220
            if validate_position(-320.91, y, 400):
                arm.set_position(x=-320.910126, y=y, z=400.215912, roll=180.0, pitch=0, yaw=-89.99, is_radian=False, wait=True, speed = tracking_speed *5)

        
        elif object_detect == 0:
          if abs(x_coord - 120) > 5: 
            adjustment = 10 + (abs(x_coord - 120) // 10)  
            
          
          if x_coord < 120:  
            y -= adjustment  
          else:  
            y += adjustment  
          
          if validate_position(-320.91, y, 400):
            arm.set_position(x=-320.910126, y=y, z=400.215912, roll=180.0, pitch=0, yaw=-89.99, is_radian=False, wait=False)
            wait_until_stopped()
            
            
            
            
            
            
            