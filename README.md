# c-DDM triggering

In this repository you will find code to accompany the article on Cross-Differential Dynamic Microscopy (DOI). 

### Summary

In the article we demonstrate the use of a dual-camera-equipped microscope for the study of the wavevector-dependent dynamics of soft matter. We use two randomly triggered cameras to acquire two sequences of images of the same region in the sample. From the two data sets we calculate cross-image differences and Fourier analyze them as a function of time delay between the two images. We show that this technique can greatly decrease the time delay, which allows us to measure fast dynamics at larger wavevectors that could not have been performed with a single camera setup.

### What is inside

In the repository we included:
* Arduino code for the random triggering of cameras and its simulation,
* A Python script for controlling the arduino via serial port

## Instructions

### Prerequisites

Software requirements:
* Python 3 with packages Numpy, Numba, PySerial
* Arduino Software (IDE)
* [**eRCaGuy_TimerCounter** ](https://github.com/ElectricRCAircraftGuy/eRCaGuy_TimerCounter) Arduino library

### Triggering the cameras

Before uploading the sketch cddm_triggering.ino to the Arduino, all the necessary parameters should be set inside the sketch. This includes serial baud rate, total number of frames to capture N, triggering pulse width pw, number of allowed random trigger times in one period n (see equations 3 and 4 in the article) and average frame rate on one camera fps. Mind that because the way the random triggering is written, the average frame rate should not exceed one half of the camera maximum framerate at the current settings.

When the sketch is uploaded, the Arduino can be controlled from the console with the Python script serial_init.py. It can be used for random triggering or for the simulation of the triggering times, used in the analysis. 

Random triggering can be started with the following command, where one should input T for triggering and the appropriate serial port.
```
>python serial_init.py -mode T -port COM1
```
Arduino will output pulses at random times on either one or the other pin or both. During triggering, the built in LED on the Arduino is turned on. After it stops, the LED is blinking. The times of the pulses must be known for the calculation of the cross image differences. For the simulation of these times, the same Python script can be re-run with mode S like so:
```
>python serial_init.py -mode S -port COM1
```
The random times will be saved in a text file into two columns. The first column tells which pin was triggered (0 - both, 1- first, 2 -second) and the second column are the times.


## License

This project is licensed under the  GNU GENERAL PUBLIC LICENSE (GPLv3) - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

For an accurate triggering we used a replacement of the Arduino built-in function micros() from the library [**eRCaGuy_TimerCounter** ](https://github.com/ElectricRCAircraftGuy/eRCaGuy_TimerCounter) by [ElectricRCAircraftGuy](https://github.com/ElectricRCAircraftGuy).
