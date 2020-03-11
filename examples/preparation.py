''' 
===================================================================================================
    Cross DDM measurement preparation python example. Used for camera alignment and focus setup.
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

import cddm_experiment
from cddm_experiment.config import load_config
import cddm
from cddm.video import show_video, play
from cddm.fft import show_alignment_and_focus
from cddm_experiment.frame_grabber import frame_grabber, queued_multi_frame_grabber
cddm.conf.set_cv2(1)

trigger_config, cam_config = load_config()
   
VIDEO = frame_grabber(trigger_config,cam_config)
#VIDEO = queued_multi_frame_grabber(frame_grabber, (trigger_config,cam_config))

video = show_video(VIDEO, id=0)   

f_video = show_alignment_and_focus(video, id=0, clipfactor=0.1)
f_video = play(f_video, fps = 15)

for i,frames in enumerate(f_video):
    print ("Frame ",i)