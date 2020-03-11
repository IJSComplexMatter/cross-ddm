'''
===================================================================================================
    Cross DDM measurement python example.
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

import numpy as np

if __name__ == "__main__":
    
    import cddm_experiment
    import matplotlib.pyplot as plt
    from cddm.video import apply_window, asarrays, fromarrays
    from cddm.window import blackman
    from cddm import conf, iccorr_multi, normalize, log_merge
    from cddm.fft import rfft2
    from cddm_experiment.frame_grabber import frame_grabber, queued_multi_frame_grabber
    from cddm_experiment.config import load_config
    from cddm_experiment.trigger import run_simulation

    def norm_fft(video):
        for frames in video:
            f1,f2 = frames
            f1 = f1/(f1[0,0])
            f2 = f2/(f2[0,0])
            yield f1,f2

    conf.set_verbose(2)
    w1 = blackman((512,512))
    w2 = blackman((512,512))

    trigger_config, cam_config = load_config()

    t1,t2=run_simulation(trigger_config)

    PERIOD=trigger_config['n']*2

    dual_video = queued_multi_frame_grabber(frame_grabber, (trigger_config,cam_config))

    dual_video = apply_window(dual_video, (w1,w2))

    fdual_video = rfft2(dual_video, kisize = 96, kjsize = 96)

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

    np.save('x.npy',x)
    np.save('logdata.npy',logdata)

    plt.show()
