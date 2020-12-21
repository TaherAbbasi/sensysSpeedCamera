# sensysSpeed

A package for managaing sensys speed cameras.

## Authors

- Taher Abbasi

## Dependencies
Python 3.6 or later with all [requirements.txt](https://github.com/TaherAbbasi/redlightmanager/blob/main/requirements.txt). To install run:
```bash
$ pip install -r requirements.txt
```

## What is Sensys speed camera 
Sensys speed camera is a speed violation detection camera. It detects speed violations by using a radar and a camera. The radar detects the violator and then triggers the camera to capture. then the violation info are inserted in an xml file. afterwards, the xml file and the captured image will be zipped and will be FTPed to an ftp serevr. 

##In this project
We process the xml file and based on the xml file information we do some processing and sends them to a traffic control center. The processing include:
1- Since the radar give the violator information in the real world(in meters), We Transform the real world coordination to image coordination. Then we know where is the violator in the image. In order ro do that, firstly, for every camera a homography matrix have to be calculated.
2- Since sensys camera doesn't read plate number, we developed an alpr engine and dockerized it. (it is no included in this project yet.)
3- Add footer or header to the image.

## How to use
1- Installing Python, XAMPP, and other requirement.
2- set the configs in /resource/config.ini
3- set the camera information in an excel file in resources in an excel file. A sample file named cameraInfo.xlsx in in resources.
4- in the root directory:
```bash
$ python start.py
```