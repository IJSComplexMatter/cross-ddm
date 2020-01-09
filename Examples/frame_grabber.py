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


import PySpin
import importlib
importlib.reload(PySpin)
import traceback
import sys
from multiprocessing import Queue, Process

def run_cameras(conf):
    
    serials=[conf["cam1serial"],conf["cam1serial"]]
    
    system=PySpin.System.GetInstance()
    cam_list = system.GetCameras()
    num_cameras = cam_list.GetSize()
    cams=[]
    
    for i in range(num_cameras):
        try:
            cam=cam_list.GetBySerial(str(serials[i]))
            cam.Init()
            config.configure_all(cam,conf)
            cams.append(cam)
            cam.AcquisitionMode.SetValue(PySpin.AcquisitionMode_Continuous)
            cam.BeginAcquisition()
        except:
            print("WARNING: Failed to open camera "+str(i+1)+" by serial number.")
    
    if len(cams) == 0:
        for i in range(num_cameras):
            try:
                cam=cam_list.GetByIndex(i)
                cam.Init()
                config.configure_camera(cam,conf)
                cams.append(cam)
                cam.AcquisitionMode.SetValue(PySpin.AcquisitionMode_Continuous)
                cam.BeginAcquisition()
            except:
                print("WARNING: Failed to open and set camera "+str(i+1)+ " by index.") 

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
        except Exception as e:
            exc_info = sys.exc_info()
            traceback.print_exception(*exc_info)

        finally:
            for cam in cams:             
                cam.EndAcquisition()
                cam.DeInit()
                del cam
            cam_list.Clear()
            system.ReleaseInstance()

    return f(system,cams,cam_list)

def _queued_frame_grabber(f,server_queue,  args = (), kwargs = {}):

    video = f(*args,**kwargs)

    try:
        for frames in video:
            server_queue.put(frames)
        print("All images captured...")

    except Exception as ex:
        print('Error: {}'.format(ex))
    finally:
        server_queue.put(None)


def queued_multi_frame_grabber(f,args = (), kwargs = {}):
    server_queue = Queue()
    p = Process(target=_queued_frame_grabber, args=(f,server_queue), kwargs = {"args" : args, "kwargs" : kwargs})
    p.start()
    while True:
        frames = server_queue.get()
        if frames is None:
            #no more frames... so exit
            break
        yield frames
    p.join()
    

def _frame_grabber(conf):
    
    video = run_cameras(conf)
    
    for i,frames in enumerate(video):
        yield frames

if __name__ == '__main__':
    
    import config
    from cddm.video import show_video, play, show_diff
    import cddm
    
    trigger_config, cam_config = config.load_config()
    
    cddm.conf.set_cv2(1)
    video = _frame_grabber(cam_config)

    def multiply(video, factor):
        for f1 in video:
            yield f1*factor

    #video = queued_multi_frame_grabber(frame_grabber)
    video = multiply(video,5)
    video = show_video(video)
    #video = show_diff(video)
    video = play(video, fps = 5)
    for i,frames in enumerate(video):
         print (i)
    # #
