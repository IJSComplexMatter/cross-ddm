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

if __name__ == "__main__":


    from cddm.video import show_video, play, apply_window, show_diff, asarrays, fromarrays
    from cddm.window import blackman
    from cddm.fft import rfft2, show_fft
    from cddm import conf, iccorr_multi, normalize, log_merge, k_select, ccorr_multi
    
    from trigger import run_arduino
    from frame_grabber import _frame_grabber, queued_multi_frame_grabber
    from config import load_config
    
    
    conf.set_verbose(2)
    w1 = blackman((512,512))
    w2 = blackman((512,512))

    trigger_config, cam_config = load_config()
    
    dual_video = queued_multi_frame_grabber(_frame_grabber(cam_config))

    run_arduino(trigger_config)

    dual_video = apply_window(dual_video, (w1,w2))

    fdual_video = rfft2(dual_video, kisize = 64, kjsize = 64)

    f1,f2 = asarrays(fdual_video,trigger_config["count"])

    f1 = f1/(f1[...,0,0][...,None,None])
    f2 = f2/(f2[...,0,0][...,None,None])

    f1 = f1 - f1.mean(axis = 0)[None,...]
    f2 = f2 - f2.mean(axis = 0)[None,...]

    fdual_video = fromarrays((f1,f2))

    data, bg = iccorr_multi(fdual_video, t1, t2, period = PERIOD, level = 5,
                             chunk_size = 256, show = True, auto_background = False, binning =  True, return_background = True)

    cfast, cslow = normalize(data)
    x, logdata = log_merge(cfast,cslow)

    #kdata = k_select(logdata, phi = 10, sector = 180, kstep = 1)
    

