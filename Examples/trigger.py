"""
===================================================================================================
    Cross DDM random triggering and calculation of triggering times.
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
"""

import serial
import numpy as np
import struct
import time
import config  


def read_trigger(arduino, conf = config.TRIGGER_CONFIG_DEFAULT):
    """Reads trigger times from arduino, given the configuration parameters.
    
    Parameters
    ----------
    arduino : serial
       An instance of serial.Serial, an opened serial port as returned by the
       open_arduino function.
    conf : dict
       A dictionary of configuration parameters for the trigger. See DEFAULT_TRIGGER
       for details.
    
    Returns
    -------
    t1, t2 : ndarray, ndarray 
       A tuple of two ndarrays of trigger times for camera 1 and 2. Dtype of
       the output arrays is 'int' and describes real times in units of microseconds.
    """
    data = 0, conf["triggering_scheme"], conf["count"], conf["deltat"], conf["n"], conf["twidth"], conf["swidth"], conf["sdelay"]
    count = data[2]
    arduino.write(struct.pack('<bbihhhhh',*data))
    #arduino should write down the parameters in a single line
    line=arduino.readline().decode("utf-8").strip()
    print("Reading trigger times.")    
    print(line)
    
    def read():
        i=0
        while True:
            line = arduino.read(5)
            if line:
                out = struct.unpack("<BI", line)
                if out[0] in (0,1):
                    i+=1
                    _print_progress(i,count)
                yield out
            else:
                break
    #next we read binary data and convert to numpy array    

    out = [d for d in read()]
    out = np.asarray(out)
    
    mask0 = out[:,0] == 0
    mask1 = out[:,0] == 1
    mask2 = out[:,0] == 2
    
    mask1 = np.logical_or(mask0, mask1)
    mask2 = np.logical_or(mask0, mask2)
    
    t1,t2 = out[mask1,1], out[mask2,1]
    
    return t1,t2

def start_trigger(arduino,conf = config.ARD_CONFIG_DEFAULT):
    """Starts triggering."""
    data = 1, conf["triggering_scheme"], conf["count"], conf["deltat"], conf["n"], conf["twidth"], conf["swidth"], conf["sdelay"]
    arduino.write(struct.pack('<bbihhhhh',*data))
    line=arduino.readline().decode("utf-8").strip()#we should see a single line answer from arduino
    print("Trigger started.")
    print(line)

    
def open_arduino(port = None, baudrate = 115200, timeout = 2):
    """Opens serial port and looks for arduino."""
    if port is None:
        from serial.tools.list_ports import comports
        ports = comports()
        
        for port in ports:
            try:
                arduino = open_arduino(port.device, baudrate, timeout=timeout) 
                print("Arduino found on port '{}'".format(port.device))
                return arduino
            except:
                pass
        raise Exception("No arduino found on any available port!")
        
    arduino = serial.Serial(port, baudrate, timeout=timeout) 
    line=arduino.readline().decode("utf-8").strip()#we should see a single line answer from arduino, if it exists on a given port 
    
    if line.startswith("CDDM Trigger"):
        print(line)
        return arduino
    else:
        raise Exception("Unknown device '{}'".format(line))
        
def _print_progress (iteration, total, prefix = '', suffix = '', decimals = 1, length = 50, fill = '='):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
    """

    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end = '\r')
#        sys.stdout.write(s)
#        sys.stdout.flush()
    # Print New Line on Complete
    if iteration == total: 
        print()


def run_arduino(conf):
    
    arduino = open_arduino(baudrate= 115200)
    time.sleep(2)
    
    mode=conf["mode"]
    
    if mode not in ["t","T","s","S","b","B"]:
        raise ValueError("Wrong mode input, please insert (t/s/b) for triggering/simulation/both mode.")
    
    if mode in ["t","T"]:
        start_trigger(arduino,conf)
        arduino.close()
        duration = 2*(conf["count"] * conf["n"] * conf["deltat"])/1e6 
        for i in range(100):
            _print_progress(i,100)
            time.sleep(duration/100)
        _print_progress(100,100)
    
    elif mode in ["s","s"]:
        t1,t2 = read_trigger(arduino,conf)    
        np.savetxt("t1.txt",t1//conf["deltat"],fmt = "%d")
        np.savetxt("t2.txt",t2//conf["deltat"],fmt = "%d")
        arduino.close()
        return t1,t2
        
    else:
        t1,t2 = read_trigger(arduino,conf)    
        np.savetxt("t1.txt",t1//conf["deltat"],fmt = "%d")
        np.savetxt("t2.txt",t2//conf["deltat"],fmt = "%d")
        
        start_trigger(arduino,conf)
        arduino.close()
        duration = 2*(conf["count"] * conf["n"] * conf["deltat"])/1e6 
        for i in range(100):
            _print_progress(i,100)
            time.sleep(duration/100)
        _print_progress(100,100)
        return t1,t2

if __name__ == '__main__':
    
    trigger_config, cam_config = config.load_config()
    
    run_arduino(trigger_config)

     


    


