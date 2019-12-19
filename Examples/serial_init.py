# -*- coding: utf-8 -*-

'''
===================================================================================================
    Cross DDM arduino control

    Copyright (C) 2019; Matej Arko, Andrej Petelin

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
===================================================================================================
'''

import serial
import argparse
import time
import sys, traceback
import numpy as np

def get_args():
    
    parser = argparse.ArgumentParser(description="A simple argument parser")
 
    parser.add_argument('-mode', action="store", dest='mode',required=True, help='(T/S) Triggering/Simulation',type=str, default="T")
    parser.add_argument('-port', action="store", dest='port', required=True, help='COM port number',type=str, default="COM1")
    
    return parser.parse_args()
    
def run(arduino,mode):
    
    if mode in ["t","T"]:
        print ("Triggering started.")
        arduino.write(str.encode('T'))
        arduino.close()
        return None
    
    else:
        lines=[]
        arduino.write(str.encode('S'))
        while True:
            line=arduino.readline().decode("utf-8")
            print (line) 
            if line=='':
                break
            lines.append(line)
        out=np.zeros((len(lines),2))
        for i in range(len(lines)):
            out[i]=np.array([s.strip() for s in lines[i].split('\t')]).astype(int)
        np.savetxt('times.txt', out, delimiter='\t', newline='\n')
        arduino.close()
    
if __name__ == "__main__":
    
    arguments=get_args()
    mode=arguments.mode
    port=arguments.port
    
    if mode not in ["t","T","s","S"]:
        raise ValueError("Wrong mode input, please insert (T/S) for Triggering/Simulation mode.")
    
    try:
        arduino = serial.Serial(port, 115200, timeout=1) #(port, baud rate)
        time.sleep(2) #waiting the initialization...
        run(arduino,mode)
    except:
        print (traceback.print_exc(file=sys.stdout))
