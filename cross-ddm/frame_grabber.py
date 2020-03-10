'''
===================================================================================================
    Cross DDM frame grabber.
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

#numpy needs to be imported before Pyspin or an error is shown: The ordinal 242 could not be located in the dynamic link library
import numpy as np
import PySpin
import traceback
import sys
from multiprocessing import Queue, Process
from trigger import run_arduino
import time


def print_device_info(cam):
    '''
    Prints device info of a given camera.

    Parameters
    ----------
    cam : PySpin.PySpin.CameraPtr
        Camera Object.

    Returns
    -------
    None.

    '''

    print("\n*** DEVICE INFORMATION ***\n")
    try:
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


def configure_exposure(cam,config):
    '''
    Sets exposure for the given camera and settings.

    Parameters
    ----------
    cam : PySpin.PySpin.CameraPtr
        Camera Object.
    config : dict
        Camera settings.

    Returns
    -------
    None.

    '''

    print("\n*** CONFIGURING EXPOSURE ***\n")
    try:
        if cam.ExposureAuto.GetAccessMode() != PySpin.RW:
            print("Unable to disable automatic exposure. Aborting...")
        cam.ExposureAuto.SetValue(PySpin.ExposureAuto_Off)
        print("Automatic exposure disabled.")
        if cam.ExposureTime.GetAccessMode() != PySpin.RW:
            print("Unable to set exposure time. Aborting...")
        exposure_time_to_set = config["exposure"]
        exposure_time_to_set = min(cam.ExposureTime.GetMax(), exposure_time_to_set)
        cam.ExposureTime.SetValue(exposure_time_to_set)
        print("Exposure time set to %d microseconds." % exposure_time_to_set)
    except PySpin.SpinnakerException as ex:
        print("Error: %s" % ex)


def configure_framerate(cam,config):
    '''
    Sets framerate for the given camera and settings.
    If framerate setting is larger than possible, fastest possible framerate is set.

    Parameters
    ----------
    cam : PySpin.PySpin.CameraPtr
        Camera Object.
    config : dict
        Camera settings.

    Returns
    -------
    None.

    '''

    print("\n*** CONFIGURING FRAMERATE ***\n")
    try:
        if cam.AcquisitionFrameRateEnable.GetAccessMode() != PySpin.RW:
            print("Unable to enable manual frame rate. Aborting...")
        cam.AcquisitionFrameRateEnable.SetValue(True)
        print("Manual frame rate enabled.")
        if cam.AcquisitionFrameRate.GetAccessMode() != PySpin.RW:
            print("Unable to set frame rate. Aborting...")
        framerate_to_set=config["framerate"]
        framerate_to_set=min(cam.AcquisitionFrameRate.GetMax(),framerate_to_set)
        cam.AcquisitionFrameRate.SetValue(framerate_to_set)
        print("Frame rate set to %d fps." % framerate_to_set)
    except PySpin.SpinnakerException as ex:
        print("Error: %s" % ex)


def configure_image_format(cam,config):
    '''
    Sets pixel format, ADC bit depth, image width, height and offset for the given camera and settings.

    Parameters
    ----------
    cam : PySpin.PySpin.CameraPtr
        Camera Object.
    config : dict
        Camera settings.

    Returns
    -------
    None.

    '''

    print("\n*** CONFIGURING CUSTOM IMAGE SETTINGS ***\n")
    try:
        if cam.PixelFormat.GetAccessMode() == PySpin.RW:
            cam.PixelFormat.SetValue(config["pixelformat"])
            print("Pixel format set to %s." % cam.PixelFormat.GetCurrentEntry().GetSymbolic())
        else:
            print("Pixel format not available...")
        if cam.AdcBitDepth.GetAccessMode() == PySpin.RW:
            cam.AdcBitDepth.SetValue(config["adcbitdepth"])
            print("ADC Bit Depth set to %s." % cam.AdcBitDepth.GetCurrentEntry().GetSymbolic())
        else:
            print("ADC Bit Depth not available...")
        if cam.OffsetX.GetAccessMode() == PySpin.RW:
            xoff_to_set=config["xoffset"]
            xoff_to_set=min(cam.OffsetX.GetMax(),xoff_to_set)
            cam.OffsetX.SetValue(xoff_to_set)
            print("Offset X set to %d px." % cam.OffsetX.GetValue())
        else:
            print("Offset X not available...")
        if cam.OffsetY.GetAccessMode() == PySpin.RW:
            yoff_to_set=config["yoffset"]
            yoff_to_set=min(cam.OffsetY.GetMax(),yoff_to_set)
            cam.OffsetY.SetValue(yoff_to_set)
            print("Offset Y set to %d px." % cam.OffsetY.GetValue())
        else:
            print("Offset Y not available...")
        if cam.Width.GetAccessMode() == PySpin.RW and cam.Width.GetInc() != 0 and cam.Width.GetMax != 0:
            width_to_set=config["imgwidth"]
            width_to_set=min(cam.Width.GetMax(),width_to_set)
            cam.Width.SetValue(width_to_set)
            print("Width set to %i px." % cam.Width.GetValue())
        else:
            print("Width not available...")
        if cam.Height.GetAccessMode() == PySpin.RW and cam.Height.GetInc() != 0 and cam.Height.GetMax != 0:
            height_to_set=config["imgheight"]
            height_to_set=min(cam.Height.GetMax(),height_to_set)
            cam.Height.SetValue(height_to_set)
            print("Height set to %i px." % cam.Height.GetValue())
        else:
            print("Height not available...")
    except PySpin.SpinnakerException as ex:
        print("Error: %s" % ex)


def configure_blacklevel(cam,config):
    '''
    Enables or disables black level clamping for the given cameras.

    Parameters
    ----------
    cam : PySpin.PySpin.CameraPtr
        Camera Object.
    config : dict
        Camera settings.

    Returns
    -------
    None.

    '''

    print("\n*** CONFIGURING BLACK LEVEL ***\n")
    try:
        if cam.BlackLevelClampingEnable.GetAccessMode() != PySpin.RW:
            print("Unable to access Black Level Clamping settings. Aborting...")
        cam.BlackLevelClampingEnable.SetValue(bool(config["blacklevelclamping"]))
        print("Black level clamping set to %r." % config["blacklevelclamping"])
    except PySpin.SpinnakerException as ex:
        print("Error: %s" % ex)


def configure_gain(cam,config):
    '''
    Enables or disables auto gain or sets gain value for the given camera.

    Parameters
    ----------
    cam : PySpin.PySpin.CameraPtr
        Camera Object.
    config : dict
        Camera settings.

    Returns
    -------
    None.

    '''

    print("\n*** GAIN ***\n")
    try:
        if cam.GainAuto.GetAccessMode() != PySpin.RW:
            print("Unable to access Auto Gain settings. Aborting...")
        cam.GainAuto.SetValue(config["autogain"])
        print("Auto gain set to %s." % cam.GainAuto.GetCurrentEntry().GetSymbolic())
        if cam.Gain.GetAccessMode() != PySpin.RW:
            print("Unable to set gain. Aborting...")
        cam.Gain.SetValue(config["gain"])
        print("Gain set to %f." % config["gain"])
    except PySpin.SpinnakerException as ex:
        print("Error: %s" % ex)


def configure_gamma(cam,config):
    '''
    Enables or disables gamma for the given camera.

    Parameters
    ----------
    cam : PySpin.PySpin.CameraPtr
        Camera Object.
    config : dict
        Camera settings.

    Returns
    -------
    None.

    '''

    print("\n*** CONFIGURING GAMMA ***\n")
    try:
        if cam.GammaEnable.GetAccessMode() != PySpin.RW:
            print("Unable to access Gamma settings. Aborting...")
        cam.GammaEnable.SetValue(bool(config["gammaenable"]))
        print("Gamma Enable set to %r." % config["gammaenable"])
    except PySpin.SpinnakerException as ex:
        print("Error: %s" % ex)


def configure_trigger(cam,config):
    '''
    Enables or disables triggering for the given camera and sets trigger source.

    Parameters
    ----------
    cam : PySpin.PySpin.CameraPtr
        Camera Object.
    config : dict
        Camera settings.

    Returns
    -------
    None.

    '''

    print("\n*** CONFIGURING TRIGGER ***\n")
    try:
        if cam.TriggerMode.GetAccessMode() != PySpin.RW:
            print("Unable to disable trigger mode (node retrieval). Aborting...")
        cam.TriggerMode.SetValue(PySpin.TriggerMode_Off)
        print("Trigger mode disabled.")
        if config["trigger"] == PySpin.TriggerMode_On:
            if cam.TriggerSource.GetAccessMode() != PySpin.RW:
                print("Unable to get trigger source (node retrieval). Aborting...")
            if config["triggersource"]==PySpin.TriggerSource_Software:
                print("Software trigger chosen...")
            elif config["triggersource"]==PySpin.TriggerSource_Line0:
                print("Hardware trigger chosen...")
            cam.TriggerSource.SetValue(config["triggersource"])
            cam.TriggerMode.SetValue(PySpin.TriggerMode_On)
            print("Trigger mode turned back on.")
    except PySpin.SpinnakerException as ex:
        print("Error: %s" % ex)

def configure_image_reverse(cam, i, config):
    '''
    Function reverses the image on a specified camera either in X or Y direction.

    Parameters
    ----------
    cam : PySpin.PySpin.CameraPtr
        Camera object.
    i : int
        Camera index.
    config : dict
        Camera settings.

    Returns
    -------
    None.

    '''
    
    if (i+1) == config["reversecam"]:
        if config["reversedirection"]==1:
            print("\n*** CONFIGURING CUSTOM IMAGE SETTINGS on camera"+str(i)+": Reversing Y ***\n")
            try:
                result=True
                if cam.ReverseY.GetAccessMode() == PySpin.RW:
                    reverse_y_to_set = True;
                    cam.ReverseY.SetValue(reverse_y_to_set)
            except PySpin.SpinnakerException as ex:
                print("Error: %s" % ex)
        else:
            print("\n*** CONFIGURING CUSTOM IMAGE SETTINGS on camera"+str(i)+": Reversing X ***\n")
            try:
                result=True
                if cam.ReverseX.GetAccessMode() == PySpin.RW:
                    reverse_x_to_set = True;
                    cam.ReverseX.SetValue(reverse_x_to_set)
            except PySpin.SpinnakerException as ex:
                print("Error: %s" % ex)
    else: pass


def configure_camera(cam,i,config):
    '''
    Function configures a camera with given configuration and prints the device info.

    Parameters
    ----------
    cam : PySpin.PySpin.CameraPtr
        Camera object.
    i : int
        Camera index.
    config : dict
        Camera settings.

    Returns
    -------
    None.

    '''

    print_device_info(cam)
    configure_image_format(cam,config)
    configure_gain(cam,config)
    configure_gamma(cam,config)
    configure_blacklevel(cam,config)
    configure_exposure(cam,config)
    configure_framerate(cam,config)
    configure_trigger(cam,config)
    configure_image_reverse(cam, i, config)


def run_cameras(conf):
    '''
    Generator function that initiates the connected cameras with the specified configuration
    and yields a tuple of captured frames.

    Parameters
    ----------
    conf : dict
        Camera configuration dictionary.

    Yields
    ------
    tuple
        Tuple of captured ndarray frames.

    '''

    serials=[conf["cam1serial"],conf["cam2serial"]]

    system=PySpin.System.GetInstance()
    cam_list = system.GetCameras()
    num_cameras = cam_list.GetSize()
    cams=[]
    
    for i, serial in enumerate(serials):
        try:
            cam=cam_list.GetBySerial(str(serial))
            cam.Init()
            configure_camera(cam,i,conf)
            cams.append(cam)
            cam.AcquisitionMode.SetValue(PySpin.AcquisitionMode_Continuous)
            cam.BeginAcquisition()
        except:
            print(sys.exc_info())
            print("Could not open and configure camera " +str(i+1)+" with serial: "+str(serial))
            print("Exiting...")
            sys.exit()

    # if len(cams) == 0:
    #     for i in range(num_cameras):
    #         try:
    #             cam=cam_list.GetByIndex(i)
    #             cam.Init()
    #             configure_camera(cam,conf)
    #             cams.append(cam)
    #             cam.AcquisitionMode.SetValue(PySpin.AcquisitionMode_Continuous)
    #             cam.BeginAcquisition()
    #         except:
    #             print("WARNING: Failed to open and set camera "+str(i+1)+ " by index.")

    def f(system,cams,cam_list):
        def _get_frame(cam):
            image_result = cam.GetNextImage()
            image_converted = image_result.Convert(conf["pixelformat"], PySpin.HQ_LINEAR)

            im = image_converted.GetNDArray()
            image_result.Release()
            return im

        try:
            for i in range(conf["count"]):
                yield tuple((_get_frame(cam) for cam in cams))
        except KeyboardInterrupt:
            print('Keyboard Interrupt')
        except Exception:
            exc_info = sys.exc_info()
            traceback.print_exception(*exc_info)

        finally:
            print("Closing cameras...")
            for cam in cams:
                cam.EndAcquisition()
                cam.DeInit()
                del cam
            cam_list.Clear()
            print("Finished.")
            #system.ReleaseInstance()

    return f(system,cams,cam_list)



def _queued_frame_grabber(f,server_queue,  args = (), kwargs = {}):
    '''
    Function grabs frames from the video generator function and puts them into a multiprocessing queue.

    Parameters
    ----------
    f : function
        A generator function that yields frames that are put into the queue.
    server_queue : multiprocessing.queues.Queue
        The multiprocessing queue for transfer of data between processes.
    args : optional
        Variable length argument list.
    kwargs : optional
        Arbitrary keyword arguments.

    Returns
    -------
    None.

    '''

    video = f(*args,**kwargs) #f is the _frame_grabber function in our case

    try:
        i = 0
        for frames in video:
            server_queue.put(frames)
            i+=1

            #loop needs to be to be stopped by force or program crashes
            if i == args[0]["count"]:
                break

    except Exception as ex:
        print('Error: {}'.format(ex))

    finally:
        server_queue.put(None)
        #program has to wait for the queue to empty
        while server_queue.qsize():
            time.sleep(1)


def queued_multi_frame_grabber(f,args = (), kwargs = {}):
    '''
    Generator function that starts multiprocessing Process() and Queue(),
    retrieves frames from the multiprocessing queue and yields them.

    Parameters
    ----------
    f : function
        A generator function that yields frames which are put into the queue.
    args : TYPE, optional
        DESCRIPTION. The default is ().
    kwargs : TYPE, optional
        DESCRIPTION. The default is {}.

    Yields
    ------
    frames : tuple
        Tuple of captured ndarray frames.

    '''

    server_queue = Queue()
    p = Process(target=_queued_frame_grabber, args=(f,server_queue), kwargs = {"args" : args, "kwargs" : kwargs})
    p.daemon=True
    p.start()
    i = 0
    while True:
        try:
            frames = server_queue.get()
            #print("qsize", server_queue.qsize())
            i+=1
            if frames is None:
                #print("Exiting...")
                #no more frames... so exit
                break
            yield frames
        except Exception as e:
            print(e)
            break
    try:
        print('joining...')
        p.join()

    except KeyboardInterrupt:
        print('Terminating...')
        p.terminate()


def frame_grabber(trigger_config, cam_config):
    '''
    Generator function that grabs the frames from the run_cameras function and yields them.
    If triggering is activated, it also starts the triggering, otherwise capturing is continuous.

    Parameters
    ----------
    trigger_config : dict
        Triggering settings.
    cam_config : dict
        Camera settings.

    Yields
    ------
    frames : tuple
        Tuple of captured ndarray frames.

    '''

    video = run_cameras(cam_config)

    if cam_config['trigger']==1:
        run_arduino(trigger_config)
    #else capturing is continuous

    for i,frames in enumerate(video):
        yield frames


if __name__ == '__main__':

    import config
    from cddm.video import show_video, play
    import cddm
    from cddm.fft import show_alignment_and_focus
    cddm.conf.set_cv2(1)

    trigger_config, cam_config = config.load_config()

    VIDEO = frame_grabber(trigger_config,cam_config)
    #VIDEO = queued_multi_frame_grabber(frame_grabber, (trigger_config,cam_config))

    video = show_video(VIDEO, id=0)

    f_video = show_alignment_and_focus(video, id=0, clipfactor=0.1)
    f_video = play(f_video, fps = 15)

    for i,frames in enumerate(f_video):
        print ("Frame ",i)
