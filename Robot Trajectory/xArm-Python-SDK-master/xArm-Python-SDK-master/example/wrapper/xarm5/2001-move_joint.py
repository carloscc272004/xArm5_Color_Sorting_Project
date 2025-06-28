from pymodbus.client.sync import ModbusSerialClient

from time import sleep
from random import uniform



client = ModbusSerialClient(
    method='rtu',
    port='/dev/ttyUSB0',
    baudrate=115200,
    timeout=3,
    parity='N',
    stopbits=1,
    bytesize=8
)

try:


    if client.connect():  # Trying for connect to Modbus RTU Server/Slave
        while True:


                '''Reading from a holding register with the below content.'''
                res = client.read_holding_registers(address=0, count=5, unit=1)
                print(res.registers)
                '''Reading from a discrete register with the below content.'''
                # res = client.read_discrete_inputs(address=1, count=1, unit=1)

                if not res.isError():
                    print(res.registers)
                   
                    sleep(0.5)
                 
                  ##    
                     

                   

                else:
                    print(res)
               





           

    else:
        print('Cannot connect to the Modbus Server/Slave')                      
except:
    print('Shutdown client')
    client.stop()