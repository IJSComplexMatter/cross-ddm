'''
===================================================================================================
    
Cross DDM triggering and camera configuration.

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

import configparser
import argparse
import datetime

s = '''
[TRIGGERING SETTINGS]
# triggering mode, 0 - random t2, 1 - random t2 + zero modification, 2 - modulo t2, 3 - modulo t2 + zero modification
mode = {mode}
# count, total number of trigger signals for each of the cameras
count = {count}
# deltat, in microsecond minimum time delay between two triggers
deltat = {deltat}
# the 'n' parameter
n = {n}
# twidth, in microseconds trigger pulse width - must be lower than deltat
twidth = {twidth}
# swidth, in microseconds strobe pulse width - must be lower than deltat
swidth = {swidth}
# sdelay, in microseconds strobe delay, can be negative or positive
sdelay = {sdelay}

[CAMERA SETTINGS]
# exposure time in microseconds
exposure = {exposure}
# frame rate in Hz
framerate = {framerate}
# pixel format, 0 for Mono8, 1 for Mono16
pixelformat = {pixelformat}
# ADC bit depth, 0 for Bit8, 1 for Bit10, 2 for Bit12
adcbitdepth = {adcbitdepth}
# image width in pixels
imgwidth = {imgwidth}
# image height in pixels
imgheight = {imgheight}
# x offset in pixels
xoffset = {xoffset}
# y offset in pixels
yoffset = {yoffset}
# black level clamping, 0 for OFF, 1 for ON
blacklevelclamping = {blacklevelclamping}
# auto gain, 0 for Off, 1 for Once, 2 for Continuous
autogain = {autogain}
# gain
gain = {gain}
# enable gamma, 0 for OFF, 1 for ON
gammaenable = {gammaenable}
# 1 for Trigger ON, 0 for trigger OFF
trigger = {trigger}
# 0 for software, 1 for Line0, 2 for Line1, 3 for Line2, 4 for Line3
triggersource = {triggersource}
# camera 1 serial number
cam1serial = {cam1serial}
# camera 2 serial number
cam2serial = {cam2serial}
# camera to reverse: 0 for none, 1 for camera 1, 2 for camera 2 
reversecam = {reversecam}
# x for reverse in x direction, y for reverse in y direction
reversedirection = {reversedirection}

'''

#Default settings
TRIGGER_CONFIG_DEFAULT = {
        "mode": 0,                  # 0 - random t2, 1 - random t2 + zero modification, 2 - modulo t2, 3 - modulo t2 + zero modification
        "count" : 8192,             # total number of trigger signals for each of the cameras
        "deltat" : 30000,             # in microsecond minimum time delay between two triggers
        "n" : 1,                   # the 'n' parameter
        "twidth" : 30,              # in microseconds trigger pulse width - must be lower than deltat
        "swidth" : 80,               # in microseconds strobe pulse width - must be lower than deltat
        "sdelay" : -20                # in microseconds strobe delay, can be negative or positive
        }

CAM_CONFIG_DEFAULT={
        "exposure": 50,             # exposure time in microseconds
        "framerate" : 100,          # frame rate in Hz
        "pixelformat" : 0,          # pixel format, 0 for Mono8, 1 for Mono16
        "adcbitdepth" : 0,          # ADC bit depth, 0 for Bit8, 1 for Bit10, 2 for Bit12
        "imgwidth" : 720,           # image width in pixels
        "imgheight" : 540,          # image height in pixels
        "xoffset": 0,               # x offset in pixels
        "yoffset" : 0,              # y offset in pixels
        "blacklevelclamping" : 0,   # black level clamping, 0 for OFF, 1 for ON
        "autogain" : 0,             # auto gain, 0 for Off, 1 for Once, 2 for Continuous
        "gain" : 0,                 # gain
        "gammaenable" : 0,          # enable gamma, 0 for OFF, 1 for ON
        "trigger" : 1,              # 1 for Trigger mode ON, 0 for trigger mode OFF
        "triggersource" : 1,        # 0 for software, 1 for Line0, 2 for Line1, 3 for Line2, 4 for Line3
        "cam1serial": 20045478,     # camera 1 serial number,
        "cam2serial": 20045476,     # camera 2 serial number
        "reversecam": 0,            # 0 for none, 1 for camera1, 2 for camera 2   
        "reversedirection": 0,      # 0 for reverse in x direction, 1 for reverse in y direction
        }

def get_args():
    '''
    Creates argument parser and returns input data.

    Returns
    -------
    Namespace
        A Namespace object containing input data.

    '''

    parser = argparse.ArgumentParser(argument_default=argparse.SUPPRESS, description="Arduino initialization for c-DDM triggering and time simulation. Set optional parameters to override configuration file.")

    group1 = parser.add_argument_group('Configuration file path')
    group1.add_argument('-c','--conf', action="store", dest='cpath', required=False, help='Configuration file path',type=str)

    group2 = parser.add_argument_group('Triggering settings')
    group2.add_argument('-m','--mode', action="store", dest='mode', required=False, help='Triggering mode: 0 - random t2, 1 - random t2 + zero modification, 2 - modulo t2, 3 - modulo t2 + zero modification.',type=int)
    group2.add_argument('--count', action="store", dest='count', required=False, help='Total count of frames.',type=int)
    group2.add_argument('--deltat', action="store", dest='deltat', required=False, help='Minimum time delay in microseconds.',type=int)
    group2.add_argument('-n','--n', action="store", dest='n', required=False, help='The \'n\' parameter.',type=int)
    group2.add_argument('--tw', action="store", dest='twidth', required=False, help='Trigger pulse width in microseconds.',type=int)
    group2.add_argument('--sw', action="store", dest='swidth', required=False, help='Strobe pulse width in microseconds. Set 0 for no strobe.',type=int)
    group2.add_argument('--sdelay', action="store", dest='sdelay', required=False, help='Strobe delay in microseconds.',type=int)

    group3 = parser.add_argument_group('Camera settings')
    group3.add_argument('--exp', action="store", dest='exposure', required=False, help='Exposure time in microseconds', type=int)
    group3.add_argument('--fps', action="store", dest='framerate', required=False, help='Frame rate in Hz', type=int)
    group3.add_argument('--pixelformat', action="store", dest='pixelformat', required=False, help='Pixel format, 0 for Mono8, 1 for Mono16', type=int)
    group3.add_argument('--adc', action="store", dest='adcbitdepth', required=False, help='ADC bit depth, 0 for Bit8, 1 for Bit10, 2 for Bit12', type=int)
    group3.add_argument('--imgwidth', action="store", dest='imgwidth', required=False, help='Image width in pixels', type=int)
    group3.add_argument('--imgheight', action="store", dest='imgheight', required=False, help='Image height in pixels', type=int)
    group3.add_argument('--xoffset', action="store", dest='xoffset', required=False, help='X offset in pixels', type=int)
    group3.add_argument('--yoffset', action="store", dest='yoffset', required=False, help='Y offset in pixels', type=int)
    group3.add_argument('--blc', action="store", dest='blacklevelclamping', required=False, help='Black level clamping, 0 for OFF, 1 for ON', type=str)
    group3.add_argument('--autogain', action="store", dest='autogain', required=False, help='Auto gain, 0 for Off, 1 for Once, 2 for Continuous', type=int)
    group3.add_argument('--gain', action="store", dest='gain', required=False, help='Gain', type=int)
    group3.add_argument('--gammaenable', action="store", dest='gammaenable', required=False, help='Enable gamma, 0 for OFF, 1 for ON', type=int)
    group3.add_argument('--trigger', action="store", dest='trigger', required=False, help='1 for Trigger ON, 0 for trigger OFF', type=int)
    group3.add_argument('--triggersource', action="store", dest='triggersource', required=False, help='0 for software, 1 for Line0, 2 for Line1, 3 for Line2, 4 for Line3',type=int)
    group3.add_argument('--cam1serial', action="store", dest='cam1serial', required=False, help='Camera 1 serial number', type=int)
    group3.add_argument('--cam2serial', action="store", dest='cam2serial', required=False, help='Camera 2 serial number', type=int)
    group3.add_argument('--revcam', action="store", dest='reversecam', required=False, help='Camera to reverse: 0 for none, 1 for camera1, 2 for camera 2 ', type=int)
    group3.add_argument('--revdir', action="store", dest='reversedirection', required=False, help='0 for reverse in X direction, 1 for reverse in Y direction', type=int)
    
    return parser.parse_args()


def load_config():
    '''
    Loads settings from the specified configuration file if it exists. If file is not specified or if it doesnt exist, it creates a file
    with default parameters. Read parameters are overriden and saved when the user inputs different parameters in the console.

    Returns
    -------
    TRIGGER_CONFIG : dict
        Triggering configuration.
    CAM_CONFIG : dict
        Camera configuration.

    '''

    args=get_args()

    override_keys=list(vars(args).keys())
    override=vars(args)

    conf = configparser.ConfigParser()

    now = datetime.datetime.now()
    dtfile=now.strftime("_%d.%m.%Y_%H-%M-%S")
    dtstr="# Date and time : "+now.strftime("%Y-%m-%d %H:%M:%S")+"\n"

    try:
        cpath=args.cpath
        conf.read_file(open(cpath))


    except:
        try:
            cpath=args.cpath
            print("Configuration file does not yet exist. Created a configuration file with default settings.")
            TRIGGER_CONFIG=TRIGGER_CONFIG_DEFAULT.copy()
            CAM_CONFIG=CAM_CONFIG_DEFAULT.copy()
        except:
            print("Created a default configuration file with default settings.")
            TRIGGER_CONFIG=TRIGGER_CONFIG_DEFAULT.copy()
            CAM_CONFIG=CAM_CONFIG_DEFAULT.copy()
            cpath="config"+dtfile+".ini"
    else:
        c_trigger=conf._sections['TRIGGERING SETTINGS']
        c_cam=conf._sections['CAMERA SETTINGS']
        TRIGGER_CONFIG={key: int(value) for key, value in c_trigger.items()}
        CAM_CONFIG={key: int(value) for key, value in c_cam.items()}

    #configuration gets overriden with user input parsed arguments
    for key in override_keys:
        if key in TRIGGER_CONFIG.keys():
            TRIGGER_CONFIG[key]=int(override.get(key))
        elif key in CAM_CONFIG.keys():
            CAM_CONFIG[key]=int(override.get(key))
        else:
            pass

    config=TRIGGER_CONFIG.copy()
    config.update(CAM_CONFIG)

    #saving the configuration to cpath
    with open(cpath, 'w') as configfile:
        configfile.write(dtstr+s.format(**config))
        print("Configuration file saved/updated.")

    TRIGGER_CONFIG["cpath"]=cpath[:-4]   #used to name random times files
    CAM_CONFIG["count"]=TRIGGER_CONFIG["count"]

    return TRIGGER_CONFIG, CAM_CONFIG

if __name__ == '__main__':

    trigger_config, cam_config = load_config()

    print(trigger_config)
    print(cam_config)
