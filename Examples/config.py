''' 
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
'''

import configparser
import argparse
try:
    import PySpin
except:
    print("WARNING: PySpin not imported. Setting only triggering parameters.")

TRIGGER_CONFIG_DEFAULT = {
        "triggering_scheme": 0,     # 0 for basic triggering scheme, 1 for modified scheme
        "count" : 2048,             # total number of trigger signals for each of the cameras
        "deltat" : 256,             # in microsecond minimum time delay between two triggers
        "n" : 16,                   # the 'n' parameter 
        "twidth" : 32,              # in microseconds trigger pulse width - must be lower than deltat
        "swidth" : 0,               # in microseconds strobe pulse width - must be lower than deltat
        "sdelay" : 0                # in microseconds strobe delay, can be negative or positive
        }

TRIGGER_CONFIG_DESCRIPTION = {
        "triggering_scheme": "0 for basic triggering scheme, 1 for modified scheme",
        "count" : "total number of trigger signals for each of the cameras",
        "deltat" : "minimum time delay between two triggers in microseconds",
        "n" : "the \'n\' parameter" ,
        "twidth" :  "trigger pulse width in microseconds - must be lower than deltat",
        "swidth" : "strobe pulse width in microseconds, SET 0 FOR NO STROBE, must be lower than deltat",
        "sdelay" : "strobe delay in microseconds, can be negative or positive",
        }

CAM_CONFIG_DEFAULT={
        "exposure": 50,             # exposure time in microseconds
        "framerate" : 100,          # frame rate in Hz
        "pixelformat" : 0,          # pixel format, 0 for Mono8, 1 for Mono16
        "adcbitdepth" : 0,          # ADC bit depth, 0 for Bit8, 1 for Bit10, 2 for Bit12
        "imgwidth" : 512,           # image width in pixels
        "imgheight" : 512,          # image height in pixels
        "xoffset": 0,               # x offset in pixels
        "yoffset" : 0,              # y offset in pixels
        "blacklevelclamping" : 0,   # black level clamping, 0 for OFF, 1 for ON
        "autogain" : 0,             # auto gain, 0 for Off, 1 for Once, 2 for Continuous
        "gain" : 0,                 # gain
        "gammaenable" : 0,          # enable gamma, 0 for OFF, 1 for ON
        "triggermode" : 0,          # 1 for Trigger mode ON, 0 for trigger mode OFF
        "triggersource" : 1,        # 0 for software, 1 for Line0, 2 for Line1, 3 for Line2, 4 for Line3
        "cam1serial": 0,            # camera 1 serial number,
        "cam2serial": 0,            # camera 2 serial number
        }

CAM_CONFIG_DESCRIPTION = {
        "exposure": "exposure time in microseconds",
        "framerate" : "frame rate in Hz",
        "pixelformat" : "pixel format, 0 for Mono8, 1 for Mono16",
        "adcbitdepth" : "ADC bit depth, 0 for Bit8, 1 for Bit10, 2 for Bit12", 
        "imgwidth" : "image width in pixels",
        "imgheight" : "image height in pixels", 
        "xoffset": "x offset in pixels", 
        "yoffset" : "y offset in pixels", 
        "blacklevelclamping" : "black level clamping, 0 for OFF, 1 for ON", 
        "autogain" : "auto gain, 0 for Off, 1 for Once, 2 for Continuous", 
        "gain" : "gain", 
        "gammaenable" : "enable gamma, 0 for OFF, 1 for ON",
        "triggermode" : "1 for Trigger mode ON, 0 for trigger mode OFF", 
        "triggersource" : "0 for software, 1 for Line0, 2 for Line1, 3 for Line2, 4 for Line3",
        "cam1serial": "camera 1 serial number",
        "cam2serial": "camera 2 serial number",
        }

    
def print_device_info(cam):

    print("\n*** DEVICE INFORMATION ***\n")
    try:
        result = True
        nodemap = cam.GetTLDeviceNodeMap()
        node_device_information = PySpin.CCategoryPtr(nodemap.GetNode("DeviceInformation"))
        if PySpin.IsAvailable(node_device_information) and PySpin.IsReadable(node_device_information):
            features = node_device_information.GetFeatures()
            for feature in features:
                node_feature = PySpin.CValuePtr(feature)
                print("%s: %s" % (node_feature.GetName(),
                                  node_feature.ToString() if PySpin.IsReadable(node_feature) else "Node not readable"))
        else:
            print("Device control information not available.")
    except PySpin.SpinnakerException as ex:
        print("Error: %s" % ex.message)
        return False
    return result


def configure_exposure(cam,config):

    print("\n*** CONFIGURING EXPOSURE ***\n")
    try:
        result=True
        if cam.ExposureAuto.GetAccessMode() != PySpin.RW:
            print("Unable to disable automatic exposure. Aborting...")
            return False
        cam.ExposureAuto.SetValue(PySpin.ExposureAuto_Off)
        print("Automatic exposure disabled.")
        if cam.ExposureTime.GetAccessMode() != PySpin.RW:
            print("Unable to set exposure time. Aborting...")
            return False
        exposure_time_to_set = config["exposure"]
        exposure_time_to_set = min(cam.ExposureTime.GetMax(), exposure_time_to_set)
        cam.ExposureTime.SetValue(exposure_time_to_set)
        print("Exposure time set to %d microseconds." % exposure_time_to_set)
    except PySpin.SpinnakerException as ex:
        print("Error: %s" % ex)
        result = False
    return result


def configure_framerate(cam,config):

    print("\n*** CONFIGURING FRAMERATE ***\n")
    try:
        result=True
        if cam.AcquisitionFrameRateEnable.GetAccessMode() != PySpin.RW:
            print("Unable to enable manual frame rate. Aborting...")
            return False
        cam.AcquisitionFrameRateEnable.SetValue(True)
        print("Manual frame rate enabled.")
        if cam.AcquisitionFrameRate.GetAccessMode() != PySpin.RW:
            print("Unable to set frame rate. Aborting...")
            return False
        framerate_to_set=config["framerate"]
        framerate_to_set=min(cam.AcquisitionFrameRate.GetMax(),framerate_to_set)
        cam.AcquisitionFrameRate.SetValue(framerate_to_set)
        print("Frame rate set to %d fps." % framerate_to_set)
    except PySpin.SpinnakerException as ex:
        print("Error: %s" % ex)
        result = False
    return result


def configure_image_format(cam,config):

    print("\n*** CONFIGURING CUSTOM IMAGE SETTINGS ***\n")
    try:
        result=True
        if cam.PixelFormat.GetAccessMode() == PySpin.RW:
            cam.PixelFormat.SetValue(config["pixelformat"])
            print("Pixel format set to %s." % cam.PixelFormat.GetCurrentEntry().GetSymbolic())
        else:
            print("Pixel format not available...")
            result = False
        if cam.AdcBitDepth.GetAccessMode() == PySpin.RW:
            cam.AdcBitDepth.SetValue(config["adcbitdepth"])
            print("ADC Bit Depth set to %s." % cam.AdcBitDepth.GetCurrentEntry().GetSymbolic())
        else:
            print("ADC Bit Depth not available...")
            result = False
        if cam.OffsetX.GetAccessMode() == PySpin.RW:
            xoff_to_set=config["xoffset"]
            xoff_to_set=min(cam.OffsetX.GetMax(),xoff_to_set)
            cam.OffsetX.SetValue(xoff_to_set)
            print("Offset X set to %d px." % cam.OffsetX.GetValue())
        else:
            print("Offset X not available...")
            result = False
        if cam.OffsetY.GetAccessMode() == PySpin.RW:
            yoff_to_set=config["yoffset"]
            yoff_to_set=min(cam.OffsetY.GetMax(),yoff_to_set)
            cam.OffsetY.SetValue(yoff_to_set)
            print("Offset Y set to %d px." % cam.OffsetY.GetValue())
        else:
            print("Offset Y not available...")
            result = False
        if cam.Width.GetAccessMode() == PySpin.RW and cam.Width.GetInc() != 0 and cam.Width.GetMax != 0:
            width_to_set=config["imgwidth"]
            width_to_set=min(cam.Width.GetMax(),width_to_set)
            cam.Width.SetValue(width_to_set)
            print("Width set to %i px." % cam.Width.GetValue())
        else:
            print("Width not available...")
            result = False
        if cam.Height.GetAccessMode() == PySpin.RW and cam.Height.GetInc() != 0 and cam.Height.GetMax != 0:
            height_to_set=config["imgheight"]
            height_to_set=min(cam.Height.GetMax(),height_to_set)
            cam.Height.SetValue(height_to_set)
            print("Height set to %i px." % cam.Height.GetValue())
        else:
            print("Height not available...")
            result = False
    except PySpin.SpinnakerException as ex:
        print("Error: %s" % ex)
        return False
    return result


def configure_blacklevel(cam,config):

    print("\n*** CONFIGURING BLACK LEVEL ***\n")
    try:
        result=True
        if cam.BlackLevelClampingEnable.GetAccessMode() != PySpin.RW:
            print("Unable to access Black Level Clamping settings. Aborting...")
            return False
        cam.BlackLevelClampingEnable.SetValue(config["blacklevelclamping"])
        print("Black level clamping set to %r." % config["blacklevelclamping"])
    except PySpin.SpinnakerException as ex:
        print("Error: %s" % ex)
        return False
    return result


def configure_gain(cam,config):

    print("\n*** GAIN ***\n")
    try:
        result=True
        if cam.GainAuto.GetAccessMode() != PySpin.RW:
            print("Unable to access Auto Gain settings. Aborting...")
            return False
        cam.GainAuto.SetValue(config["autogain"])
        print("Auto gain set to %s." % cam.GainAuto.GetCurrentEntry().GetSymbolic())
        if cam.Gain.GetAccessMode() != PySpin.RW:
            print("Unable to set gain. Aborting...")
            return False
        cam.Gain.SetValue(config["gain"])
        print("Gain set to %f." % config["gain"])
    except PySpin.SpinnakerException as ex:
        print("Error: %s" % ex)
        return False
    return result


def configure_gamma(cam,config):

    print("\n*** CONFIGURING GAMMA ***\n")
    try:
        result=True
        if cam.GammaEnable.GetAccessMode() != PySpin.RW:
            print("Unable to access Gamma settings. Aborting...")
            return False
        cam.GammaEnable.SetValue(config["gammaenable"])
        print("Gamma Enable set to %r." % config["gammaenable"])
    except PySpin.SpinnakerException as ex:
        print("Error: %s" % ex)
        return False
    return result


def configure_trigger(cam,config):
    
    print("\n*** CONFIGURING TRIGGER ***\n")
    try:
        result=True
        if cam.TriggerMode.GetAccessMode() != PySpin.RW:
            print("Unable to disable trigger mode (node retrieval). Aborting...")
            return False
        cam.TriggerMode.SetValue(PySpin.TriggerMode_Off)
        print("Trigger mode disabled.")
        if config["triggermode"] == PySpin.TriggerMode_On:
            if cam.TriggerSource.GetAccessMode() != PySpin.RW:
                print("Unable to get trigger source (node retrieval). Aborting...")
                return False
            if config["triggersource"]==PySpin.TriggerSource_Software:
                print("Software trigger chosen...")
            elif config["triggersource"]==PySpin.TriggerSource_Line0:
                print("Hardware trigger chosen...")
            cam.TriggerSource.SetValue(config["triggersource"])
            cam.TriggerMode.SetValue(PySpin.TriggerMode_On)
            print("Trigger mode turned back on.")
    except PySpin.SpinnakerException as ex:
        print("Error: %s" % ex)
        return False
    return result
   
def configure_camera(cam,config=CAM_CONFIG_DEFAULT):
    
    print_device_info(cam)
    configure_image_format(cam,config)
    configure_gain(cam,config)
    configure_gamma(cam,config)
    configure_blacklevel(cam,config)
    configure_exposure(cam,config)
    configure_framerate(cam,config)
    configure_trigger(cam,config)
    
    

    
def get_args():
    """Creates argument parser and returns input data."""
    
    parser = argparse.ArgumentParser(argument_default=argparse.SUPPRESS, description="Arduino initialization for c-DDM triggering and time simulation. Set optional parameters to override configuration file.") 
    
    group1 = parser.add_argument_group('Configuration file path')
    group1.add_argument('-c','--conf', action="store", dest='cpath', required=False, help='Configuration file path',type=str, default='config.ini')
    
    group2 = parser.add_argument_group('Triggering settings')
    group2.add_argument('-m','--mode', action="store", dest='mode', required=False, help='(t/s/b) triggering/simulation/both (default: both)',type=str, default='b')    
    group2.add_argument('--scheme', action="store", dest='triggering_scheme', required=False, help='Triggering scheme: 0 for basic triggering scheme, 1 for modified scheme.',type=int)
    group2.add_argument('--count', action="store", dest='count', required=False, help='Total count of frames.',type=int)
    group2.add_argument('--deltat', action="store", dest='deltat', required=False, help='Minimum time delay in microseconds.',type=int)
    group2.add_argument('--n', action="store", dest='n', required=False, help='The \'n\' parameter.',type=int)
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
    group3.add_argument('--triggermode', action="store", dest='triggermode', required=False, help='1 for Trigger mode ON, 0 for trigger mode OFF', type=int)
    group3.add_argument('--triggersource', action="store", dest='triggersource', required=False, help='0 for software, 1 for Line0, 2 for Line1, 3 for Line2, 4 for Line3',type=int)
    group3.add_argument('--cam1serial', action="store", dest='cam1serial', required=False, help='Camera 1 serial number', type=int)
    group3.add_argument('--cam2serial', action="store", dest='cam2serial', required=False, help='Camera 2 serial number', type=int) 

    return parser.parse_args()   


def load_config():
    """Loads settings from the configuration file if it exists, otherwise creates a file with default parameters."""
    
    args=get_args()
    mode=args.mode
    cpath=args.cpath
    
    override_keys=list(vars(args).keys())
    override=vars(args)
       
    conf = configparser.ConfigParser()
    
    try:
        conf.read_file(open(cpath))  
        c_trigger=conf._sections['TRIGGERING SETTINGS'] 
        c_cam=conf._sections['CAMERA SETTINGS']
        TRIGGER_CONFIG={key: int(value) for key, value in c_trigger.items()}
        CAM_CONFIG={key: int(value) for key, value in c_cam.items()}
        
    except:
        print("WARNING: Appropriate configuration file not found. Created a configuration file with default settings.") 
        TRIGGER_CONFIG=TRIGGER_CONFIG_DEFAULT.copy()
        CAM_CONFIG=CAM_CONFIG_DEFAULT.copy()
       
    for key in override_keys:
        if key in TRIGGER_CONFIG.keys():
            TRIGGER_CONFIG[key]=int(override.get(key))
        elif key in CAM_CONFIG.keys():
            CAM_CONFIG[key]=int(override.get(key))
        else:
            pass
    
    conf['TRIGGERING SETTINGS'] = TRIGGER_CONFIG
    conf['TRIGGERING SETTINGS DESCRIPTION'] = TRIGGER_CONFIG_DESCRIPTION
    conf['CAMERA SETTINGS'] = CAM_CONFIG
    conf['CAMERA SETTINGS DESCRIPTION'] = CAM_CONFIG_DESCRIPTION
    conf['DEFAULT TRIGGERING SETTINGS'] = TRIGGER_CONFIG_DEFAULT
    conf['DEFAULT CAMERA SETTINGS'] = CAM_CONFIG_DEFAULT   
    
    with open(cpath, 'w') as configfile:
        conf.write(configfile)
    
    TRIGGER_CONFIG["mode"]=mode
    CAM_CONFIG["count"]=TRIGGER_CONFIG["count"]
    
    return TRIGGER_CONFIG, CAM_CONFIG

    
if __name__ == '__main__':
    
    trigger_config, cam_config = load_config()
    print(trigger_config)
    print(cam_config)
    