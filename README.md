# c-DDM experiment
In this repository you will find instructions, a python package, arduino code and python examples for performing a Cross-Differential Dynamic Microscopy experiment. Repository is accompanying the article on [Cross-Differential Dynamic Microscopy](https://pubs.rsc.org/en/content/articlelanding/2019/sm/c9sm00121b#!divAbstract).

### The method

In the article we demonstrate the use of a dual-camera-equipped microscope for the study of the wavevector-dependent dynamics of soft matter. We use two randomly triggered cameras to acquire two sequences of images of the same region in the sample. From the two data sets we calculate cross-image differences and Fourier analyze them as a function of time delay between the two images. We show that this technique can greatly decrease the time delay, which allows us to measure fast dynamics at larger wavevectors that could not have been performed with a single camera setup.

### What is inside

In the repository we included:
* Arduino code for the random triggering of cameras and its simulation,
* An installable Python package called cddm_experiment that consists of three modules:
	* trigger.py (arduino communication, triggering and random times simulation)
	* frame_grabber.py (camera communication and capturing with FLIR USB cameras)
	* config.py (camera and triggering configuration)
* cddm_experiment documentation
* A series of standalone example python scripts

## Instructions

### Prerequisites

Software requirements:
* Python 3.7 with packages numpy, numba, multiprocessing, pyserial, [cddm](https://github.com/IJSComplexMatter/cddm)
* Arduino Software (IDE)

### Table of contents

- [01 - Experimental setup](/01-experimental-setup.md)
- [02 - Triggering the cameras](/02-camera-triggering.md)
- [03 - Image acquistion and analysis](/03-acquisition-and-analysis.md)

## License

This project is licensed under the  GNU GENERAL PUBLIC LICENSE (GPLv3) - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

For an accurate triggering we used a replacement of the Arduino built-in function micros() from the library [**eRCaGuy_TimerCounter** ](https://github.com/ElectricRCAircraftGuy/eRCaGuy_TimerCounter) by [ElectricRCAircraftGuy](https://github.com/ElectricRCAircraftGuy).
