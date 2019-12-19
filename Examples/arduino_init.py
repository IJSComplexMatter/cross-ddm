"""Arduino triggering.

This script is used to configure arduiono CDDM trigger, read trigger times, and
start the triggering.
"""

import serial
import numpy as np
import struct
import configparser
import argparse
   
DEFAULT_TRIGGER = {
        "triggering_scheme": 0, # 0 for basic triggering scheme, 1 for modified scheme
        "count" : 2048, # total number of trigger signals for each of the cameras
        "deltat" : 256, # in microsecond minimum time delay between two triggers
        "n" : 16, # the 'n' parameter 
        "twidth" : 32, # in microseconds trigger pulse width - must be lower than deltat
        "swidth" : 0, # in microseconds strobe pulse width - must be lower than deltat
        "sdelay" : 0 # in microseconds strobe delay, can be negative or positive
        }

DESCRIPTION = {
        "triggering_scheme": "0 for basic triggering scheme, 1 for modified scheme",
        "count" : "total number of trigger signals for each of the cameras",
        "deltat" : "minimum time delay between two triggers in microseconds",
        "n" : "the \'n\' parameter" ,
        "twidth" :  "trigger pulse width in microseconds - must be lower than deltat",
        "swidth" : "strobe pulse width in microseconds, SET 0 FOR NO STROBE, must be lower than deltat",
        "sdelay" : "strobe delay in microseconds, can be negative or positive",
        }
        

def read_trigger(arduino, config = DEFAULT_TRIGGER):
    """Reads trigger times from arduino, given the configuration parameters.
    
    Parameters
    ----------
    arduino : serial
       An instance of serial.Serial, an opened serial port as returned by the
       open_arduino function.
    config : dict
       A dictionary of configuration parameters for the trigger. See DEFAULT_TRIGGER
       for details.
    
    Returns
    -------
    t1, t2 : ndarray, ndarray 
       A tuple of two ndarrays of trigger times for camera 1 and 2. Dtype of
       the output arrays is 'int' and describes real times in units of microseconds.
    """
    data = 0, config["triggering_scheme"], config["count"], config["deltat"], config["n"], config["twidth"], config["swidth"], config["sdelay"]
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

def start_trigger(arduino,config = DEFAULT_TRIGGER):
    """Starts triggering."""
    data = 1, config["triggering_scheme"], config["count"], config["deltat"], config["n"], config["twidth"], config["swidth"], config["sdelay"]
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

def load_config():
    """Loads settings from the configuration file if it exists, otherwise creates a file with default parameters."""
    
    conf = configparser.ConfigParser()
    
    try:
        conf.read_file(open('config.ini'))
                
    except FileNotFoundError:
        
       print("WARNING: Configuration file not found. Created a configuration file with default settings.")       
       conf['DESCRIPTION'] = DESCRIPTION
       conf['SETTINGS'] = DEFAULT_TRIGGER
       
       with open('config.ini', 'w') as configfile:
           conf.write(configfile)
           
    c=conf._sections['SETTINGS'] 
    
    return  {key: int(value) for key, value in c.items()}     


def get_args():
    """Creates argument parser and returns input data."""
    
    parser = argparse.ArgumentParser(argument_default=argparse.SUPPRESS, description="Arduino initialization for c-DDM triggering and time simulation. Set optional parameters to override configuration file.") 
    parser.add_argument('-m','--mode', action="store", dest='mode', required=False, help='(t/s/b) triggering/simulation/both (default: both)',type=str, default='b')    
    parser.add_argument('--scheme', action="store", dest='triggering_scheme', required=False, help='Triggering scheme: 0 for basic triggering scheme, 1 for modified scheme.',type=str) 
    parser.add_argument('--count', action="store", dest='count', required=False, help='Total count of frames.',type=str)
    parser.add_argument('--deltat', action="store", dest='deltat', required=False, help='Minimum time delay in microseconds.',type=str)
    parser.add_argument('--n', action="store", dest='n', required=False, help='The \'n\' parameter.',type=str)
    parser.add_argument('--tw', action="store", dest='twidth', required=False, help='Trigger pulse width in microseconds.',type=str)
    parser.add_argument('--sw', action="store", dest='swidth', required=False, help='Strobe pulse width in microseconds. Set 0 for no strobe.',type=str)
    parser.add_argument('--sdelay', action="store", dest='sdelay', required=False, help='Strobe delay in microseconds.',type=str)
    
    return parser.parse_args()      

if __name__ == '__main__':
    
    import time
    
    arguments=get_args()
    mode=arguments.mode
    
    arduino = open_arduino(baudrate= 115200) 
    config=load_config() #dictionary from config file
    
    override_keys=list(vars(arguments).keys())[1:]
    override=vars(arguments)
    
    for key in override_keys:
        config[key]=int(override.get(key))

    if mode not in ["t","T","s","S","b","B"]:
        raise ValueError("Wrong mode input, please insert (t/s) for triggering/simulation mode.")
    
    if mode in ["t","T"]:
        start_trigger(arduino,config)
        arduino.close()
        duration = 2*(config["count"] * config["n"] * config["deltat"])/1e6 
        for i in range(100):
            _print_progress(i,100)
            time.sleep(duration/100)
        _print_progress(100,100)
    
    elif mode in ["s","s"]:
        t1,t2 = read_trigger(arduino,config)    
        np.savetxt("t1.txt",t1//config["deltat"],fmt = "%d")
        np.savetxt("t2.txt",t2//config["deltat"],fmt = "%d")
        arduino.close()
        
    else:
        t1,t2 = read_trigger(arduino,config)    
        np.savetxt("t1.txt",t1//config["deltat"],fmt = "%d")
        np.savetxt("t2.txt",t2//config["deltat"],fmt = "%d")
        
        start_trigger(arduino,config)
        arduino.close()
        duration = 2*(config["count"] * config["n"] * config["deltat"])/1e6 
        for i in range(100):
            _print_progress(i,100)
            time.sleep(duration/100)
        _print_progress(100,100)

     


    


