"""
===================================================================================================
    Cross DDM random triggering and simulation of triggering times - python example.
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

import config 
from trigger import run_arduino, run_simulation

#loading configuration using both config parser and argument parser
#both camera and triggering configuration is read
trigger_config, cam_config = config.load_config()

#simulating times, times are saved on the disk automatically, t1 and t2 are not used here   
t1,t2=run_simulation(trigger_config)
    
#triggering signal is started
run_arduino(trigger_config)