import pickle
# import pyautogui
import xmltodict
import pathlib
import logging
import os
import tarfile
import numpy as np
import ast
from cv2 import cv2
from os.path import splitext
from pathlib import Path
from datetime import datetime
from math import ceil
from os import path
from sensysspeed.core.fileManaging import fileManaging
from sensysspeed.core.configLoading import configLoading
from sensysspeed.utils.getImageSize import get_image_size as getImageSize
from sensysspeed.utils.getImageSize import UnknownImageFormat
from sensysspeed.core.plateReader import plateReader
from sensysspeed.core.violationSending import violationSending


logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

class violationProcessing():
    def __init__(self,
                 dbHandler,
                 configLoader):
        '''it get confgi path and sets the basic data
        '''
        self.camerasInfo = dbHandler.getCamerasInfo()
        if not self.camerasInfo:
            logging.info('Problem in loading cameras information')
        self.configLoader = configLoader

        if not self.configLoader:
            return None
        self.fileManager = fileManaging(configLoader)
        try:
            self.violationSender = violationSending(configLoader)
        except Exception as e:
            logging.info(f'Problem in creating violationSender')
        if not self.fileManager:
            return None

        self.ftpPath = self.configLoader.get('main', 'ftpPath')
        self.archivePath = self.configLoader.get('main', 'archivePath')
        self.cameraNameLevel = self.configLoader.get('main', 'cameraNameLevel')
        
        self.roiStride = {'width': int(self.configLoader.get('files', 'imageRoiStrideWidth')),
                          'height': int(self.configLoader.get('files', 'imageRoiStrideHeight'))}
        try:
            self.cameraNameLevel = int(self.cameraNameLevel)-1
        except Exception as e:
            logging.info(f'TarFileLevel in config file must be an integer: {e}')

        try:
            self.plateReader = plateReader()        
        except Exception as e:
            logging.info(f'Problem in connecting to plate reader.')
            # return None

    def process(self, violationFilePath):
        # assert isinstance(violationFilePath, str), 'string is expected: %r' % violationFilePath
        # assert tarfile.is_tarfile(violationFilePath), 'Not a tar file: %r' % violationFilePath

        self.violationFilePath = os.path.normpath(violationFilePath)
        self.finalInfo = {}

        cameraNameEn = self.setCameraName(self.cameraNameLevel)
        if cameraNameEn:
            self.finalInfo['cameraNameEn'] = cameraNameEn
            try:
                self.finalInfo['cameraNameFa'] = self.camerasInfo[cameraNameEn]['nameFa'].encode('utf-8').decode('utf-8')
            except Exception as e:
                logging.info(e)
                return None
        else:
            return None
        
        extractionPath = self.fileManager.extractFiles(self.violationFilePath)
        self.finalInfo['dirName'] = extractionPath
        if not extractionPath:
            return None

        filesPath = self.fileManager.setFilesPath(extractionPath)
        if filesPath:
            self.finalInfo['xmlPath'] = filesPath['xmlPath']
            self.finalInfo['originalImagePath'] = filesPath['imagePath']
        else:
            return None

        ViolationInfo = self.getViolationInfo()
        if ViolationInfo:
            if not self.setBasicViolationInfo(ViolationInfo):
                return None
        else:
            return None

        self.finalInfo['violationCode'] = self.violationType(self.finalInfo['speed'], self.finalInfo['signSpeed'])
        if not self.finalInfo['violationCode']:
            return None

        if not self.setRoiCenteralPoint():
            return None
        print(self.finalInfo['originalImagePath'])
        print(self.finalInfo['roiCenter'])

        self.candidRoi = self.candidRoiFromRoiCenter(self.finalInfo['roiCenter'], self.roiStride)
        if not self.candidRoi:
            return None
        originalImage = cv2.imread(self.finalInfo['originalImagePath'])
        candidRoiImage = originalImage[self.candidRoi['topLeft'][1]:self.candidRoi['bottomRight'][1],
                                       self.candidRoi['topLeft'][0]:self.candidRoi['bottomRight'][0]]
        return None
        
        alprMessage = self.plateReader.run(self.finalInfo['originalImagePath'], 
                                           self.candidRoi)
        if not alprMessage:
            return None

        plateDetections = self.getDetections(alprMessage)
        if not plateDetections:
            return None
        
        plateDetections = self.mapToOriginalImage(plateDetections)
        if not plateDetections:
            return None
        
        plateData = self.fittestPlate(self.finalInfo['roiCenter'], plateDetections)

        if not plateData:
            return None
        self.finalInfo['plateRoi'] = plateData['boundingBox']
        self.finalInfo['ocr'] = plateData['ocr']

        self.finalInfo['ocrCode'] = self.toOcrCode(self.finalInfo['ocr'])
        if not self.finalInfo['ocrCode']:
            return None
        
        try:
            plateImagePath = '{0}{2}{1}'.format(*splitext(self.finalInfo['originalImagePath']),'_Plate')
            print(plateImagePath)
            plateImage = originalImage[self.finalInfo['plateRoi']['topLeft'][0]:self.finalInfo['plateRoi']['bottomRight'][0],
                                       self.finalInfo['plateRoi']['topLeft'][1]:self.finalInfo['plateRoi']['bottomRight'][1]]

        except Exception as e:
            logging.info(f'Problem in reading image and setting plate image bounding box: {e}')
        
        if self.fileManager.saveImage(plateImagePath, plateImage):
            self.finalInfo['plateImagePath'] = plateImagePath
        else:
            return None

        footerImage = self.addFooter(originalImage, self.finalInfo)
        if not footerImage:
            return None
        
        footerImagePath = '{0}{2}{1}'.format(*splitext(originalImagePath),'_Footer')

        isLarge, footerImagePath = self.fileManager.resizeImageVolume(footerImagePath)
        if isLarge:
            return None

        if self.fileManager.saveImage(footerImagePath, footerImage):
            self.finalInfo['footerImagePath'] = footerImagePath
        else:
            return None


        self.finalInfo['uniqueId'] = ''.join([self.finalInfo['cameraNameEn'],
                                              self.finalInfo['date'].replace('-',''), 
                                              self.finalInfo['time'].replace(':','')
                                              ])
        isArchived = self.fileManager.archive(self.violationFilePath, extractionPath)
        if not isArchived:
            return None
        
        responseCode, message = self.violationSender.send(self.finalInfo) # tc Response is the response we get from traffic control
        self.finalInfo['responseCode'] = responseCode
        self.finalInfo['message'] = message
        
        return self.finalInfo
               
    def setCameraName(self, cameraNameLevel):
        '''sets camera name based on violation path and camera name level
        '''
        cameraNameEn = None
        try:
            ftpLevel = len(self.ftpPath.split(os.sep))
            cameraNameLevel = ftpLevel + cameraNameLevel
            violationFilePathSeparated = self.violationFilePath.split(os.sep)
            cameraNameEn = violationFilePathSeparated[cameraNameLevel]
        except:
            logging.info(f'Camera name is not set. \n Violation path: {self.violationFilePath} \n Camera name level: {self.cameraNameLevel}')
        return cameraNameEn

    def getViolationInfo(self):
        ''' gets path of an XML file of a violation which is generated by 
        Sensys Speed Camera and returns a the useful data needed to send to Naja in a dict()
        '''
        xmlPath = self.finalInfo['xmlPath']
        if not isinstance(xmlPath, str):
            logging.info(f'String is expected: {xmlPath}')
            return None
        
        xmlPath = pathlib.Path(xmlPath)
        if not xmlPath.is_file():
            logging.info(f'File Not Exists: {xmlPath}')
            return None

        try:
            fd = open(xmlPath, 'r')
        except IOError:
            logging.info(f'Problem in opening: {xmlPath}')
            return None
        
        try:
            xmlInfo = xmltodict.parse(fd.read())
            fd.close()
        except Exception:
            fd.close()
            logging.info(f'Problem in parsing:: {xmlPath}')
            return None   

        try:
            violationInfo = xmlInfo['MC_Protocol']['Violation']
        except KeyError:
            logging.info(f'Problem in extracting violation info: {xmlPath}')
            return None   

        try:
            vehicleInfo = xmlInfo['MC_Protocol']['VehicleIdsAtReportline']['Vehicle']
        except KeyError:
            logging.info(f'Problem in extracting vehicle info: {xmlPath}')
            return None
        violationInfo['vehicleInfo'] = vehicleInfo
        return violationInfo

    def setBasicViolationInfo(self, violationInfo):
        '''it gets violation info and returns portion
        of the info suitable for inserting in database.
        '''
        basicViolationInfoSet = False
        if not isinstance(violationInfo, dict):
            logging.info(f'dict is expected: {violationInfo}')
            return None

        try:
            vDateTime = violationInfo['ViolationTime']
            self.finalInfo['triggerSpeed'] =  abs(float(violationInfo['TriggerSpeed']))
            self.finalInfo['signSpeed'] =  abs(float(violationInfo['SignSpeed']))

        except KeyError:
            logging.info(f'KeyError: {violationInfo}')
            return None

        try:
            vDateTime = datetime.strptime(vDateTime, '%Y-%m-%d %H:%M:%S.%f')
            vDate = vDateTime.strftime('%Y-%m-%d')
            vTime = vDateTime.strftime('%H:%M:%S')
            self.finalInfo['date'] = vDate
            self.finalInfo['time'] = vTime

        except Exception as e:
            logging.info(f'Couldnt convert datetime to date and time: {vDateTime}\n Date time Exception: {e}')
            return None

        vehicleInfo = violationInfo['vehicleInfo']

        try:
            if vehicleInfo['Violator']:
                self.finalInfo['distance'] = {'distX': float(vehicleInfo['DistX']),'distY': float(vehicleInfo['DistY'])}
                self.finalInfo['speed'] = abs(float(vehicleInfo['Speed']))
                basicViolationInfoSet = True
        except:
            try:
                for v in vehicleInfo:
                    if v['Violator']:
                        self.finalInfo['distance'] = {'distX': float(v['DistX']),'distY': float(v['DistY'])}
                        self.finalInfo['speed'] = abs(float(v['Speed']))
                        basicViolationInfoSet = True
                        break
            except:
                logging.info(f'No vehicle info: {vehicleInfo}')
                return None

        return basicViolationInfoSet

    def setRoiCenteralPoint(self):
        '''gets a 2D point which is coming from Radar.
        The point is in meter. This function maps the
        point to its related point in the image which
        is in pixel. It maps real world points to image
        points using a homography matrice.
        '''
        isPlatePointSet = False
        realWorldPoint = self.finalInfo['distance']
        # print(realWolrdPoint)
        # realWorldPoint = np.array([[realWolrdPoint['distWidth'], realWolrdPoint['distHeight']]], dtype='float32')
        # realWorldPoint = np.array([realWorldPoint])
        # imgPoint = cv2.perspectiveTransform(realWorldPoint, self.homographyMatrice)
        # return [ceil(imgPoint[0][0][0]), ceil(imgPoint[0][0][1])]
        realWorldPoint = [self.finalInfo['distance']['distX'], self.finalInfo['distance']['distX']]
        realWorldPoint = np.array([[realWorldPoint]], dtype='float32')
        
        try:
            homoMatFileName = self.camerasInfo[self.finalInfo['cameraNameEn']]['homographyMatrice']            
            with open (homoMatFileName, 'rb') as fp:
                homoMat = pickle.load(fp)
            homographyMat = np.array(homoMat, dtype=np.float32)
            roiPoint = cv2.perspectiveTransform(realWorldPoint, homographyMat)[0][0]
        except Exception as e:
            logging.info(f'Problem in converting real world point to image point.\n {e}')
            return isPlatePointSet
        roiPoint = [ceil(roiPoint[0]), ceil(roiPoint[1])]
        self.finalInfo['roiCenter'] = roiPoint
        isPlatePointSet = True
        return isPlatePointSet

    def candidRoiFromRoiCenter(self, roiCenter, roiStride):
        '''
        '''
        candidRoi = None

        x = roiCenter[0]
        y = roiCenter[1]
        w = roiStride['width']
        h = roiStride['height']

        try:
            imageWidth, imageHeight = getImageSize(self.finalInfo['originalImagePath'])
        except UnknownImageFormat as e:
            logging.info(f'Problem in getting image size: {e}')
            return candidRoi

        rectWidths= {'lowerBound': x-w,
                        'upperBound': x+w
        }
        if rectWidths['lowerBound'] < 1:
            rectWidths['lowerBound'] = 1
        if rectWidths['upperBound'] > imageWidth:
            rectWidths['upperBound'] = imageWidth-1

        rectHeights= {'lowerBound': y-h,
                        'upperBound': y+h
        }
        if rectHeights['lowerBound'] < 1:
            rectHeights['lowerBound'] = 1
        if rectHeights['upperBound'] > imageHeight:
            rectHeights['upperBound'] = imageHeight-1

        topLeft = [rectWidths['lowerBound'], rectHeights['lowerBound']]
        bottomRight = [rectWidths['upperBound'], rectHeights['upperBound'] ]

        candidRoi = {'topLeft': topLeft,
                     'bottomRight': bottomRight }

        return candidRoi    

    def getDetections(self, alprMessage):
        '''It get messages coming from datis alpr docker
        and returns plate detections, and ocr.
        '''
        assert isinstance(alprMessage, str), 'string is expected: %r' % alprMessage

        # ROIs = [{"label": "person", "confidence": 0.8289788365364075, "topleft": {"x": 1251, "y": 406}, "bottomright": {"x": 1448, "y": 543}}, {"label": "person", "confidence": 0.8241226673126221, "topleft": {"x": 1505, "y": 498}, "bottomright": {"x": 1730, "y": 694}}, {"label": "plate", "confidence": 0.7091344594955444, "topleft": {"x": 1556, "y": 627}, "bottomright": {"x": 1641, "y": 663}, "ocr": "27S58928"}]
        
        try:
            alprMessage = ast.literal_eval(alprMessage)
        except:
            logging.info('Couldnt convert alprMessage to dict')
            return None

        plateDetections = []
        # vehicleDetections = []
        for m in alprMessage:
            label = m['label']
            topLeft = m['topleft']
            bottomRight = m['bottomright']
            
            if label == 'plate':
                ocr = m['ocr']
                confidence = m['ocr_prob']
                boundingBox = {'topLeft':[int(topLeft['x']), int(topLeft['y'])],
                               'bottomRight': [int(bottomRight['x']), int(bottomRight['y'])]
                                }
                plateDetections.append({
                                        'ocr':ocr,
                                        'confidence': confidence,
                                        'boundingBox': boundingBox
                                       })
            # elif label == 'person':
            #     boundingBox = [int(topLeft['x']),
            #                    int(topLeft['y']), 
            #                    int(bottomRight['x']), 
            #                    int(bottomRight['y'])]
            #     vehicleDetections.append({
            #                                'boundingBox': boundingBox
            #                               })

        return plateDetections

    def mapToOriginalImage(self, detections):
        
        mappedDetections = []
        try:
            for d in detections:
                for label in ('topLeft','bottomRight'):
                    for j in range(0,2):
                        mappedDetections.append(d['boundingBox'][label][j] + self.candidRoi['topLeft'][j])
        except Exception as e:
            logging.info(f'Problem in mapping detections to original image: {e}')
            mappedDetections = []

        return mappedDetections

    def fittestPlate(self, roiCenter, plateDetections):
        
        roiCenter = tuple(roiCenter)
        minDistance = float('inf')
        targetDetection = None
        try:
            for d in plateDetections:
                roi = d['boundingBox']
                detectionCenter = ((roi['topLeft'][0] + roi['bottomRight'][0])/2,
                                   (roi['topLeft'][1] + roi['bottomRight'][1])/2)
                distance = np.linalg.norm(roiCenter - detectionCenter)
                if distance < minDistance:
                    minDistance = distance
                    targetDetection = d
        except Exception as e:
            logging.info(f'Problem in finding the nearest detection to roiCenter: {e}')
        
        return targetDetection

    def calculateHomographyMatrice(self, cameraNameEn, noOfViolations=40):
        '''it takes name of the camera and calculates the homography matrice
           of the camera. it lists all violations in ftp path and selects 
           noOfViolations of them for calculating homography matrice. n
        '''
        self.finalInfo = {}
        self.imagePoints = []
        self.realPoints = []
        self.HomographyMatrice = None
        Violations = self.fileManager.listViolations()
        selectedViolations = []
        font = cv2.FONT_HERSHEY_SIMPLEX 
        org = (50, 50) 
        fontScale = 1
        color = (255, 255, 255) 
        thickness = 2
        desktopRes = pyautogui.size() # [width, height]
        self.violationFilePath = os.path.normpath(Violations[0])
        self.finalInfo['cameraNameEn'] = self.setCameraName(self.cameraNameLevel)

        for v in Violations:
            if not self.finalInfo['cameraNameEn']:
                continue
            if cameraNameEn != self.finalInfo['cameraNameEn']:
                continue

            if len(selectedViolations) == noOfViolations:
                break
            else:
                selectedViolations.append(v)

        for v in selectedViolations:
            self.violationFilePath = os.path.normpath(v)
            extractionPath = self.fileManager.extractFiles(self.violationFilePath)
            if not extractionPath:
                return None

            filesPath = self.fileManager.setFilesPath(extractionPath)
            if filesPath:
                self.finalInfo['xmlPath'] = filesPath['xmlPath']
                self.finalInfo['originalImagePath'] = filesPath['imagePath']
            else:
                return None

            ViolationInfo = self.getViolationInfo()
            if ViolationInfo:
                if not self.setBasicViolationInfo(ViolationInfo):
                    return None
            else:
                return None
            
            realWorldPoint = [self.finalInfo['distance']['distX'], self.finalInfo['distance']['distY']]
            self.currentRealPoint = realWorldPoint
            realWorldPoint = np.array([[realWorldPoint]], dtype='float32')
            image = cv2.imread(self.finalInfo['originalImagePath'])
            try:
                self.HomographyMatrice, _ = cv2.findHomography(np.array(self.realPoints, dtype='float32'), np.array(self.imagePoints, dtype='float32'))
                EstimatedImgPoint = cv2.perspectiveTransform(realWorldPoint, self.HomographyMatrice)[0][0]
                EstimatedImgPoint = (EstimatedImgPoint[0], EstimatedImgPoint[1])
                cv2.circle(image, EstimatedImgPoint, 60, 255, -1)
            except Exception as e:
                logging.info(f'Problem in calculatin homography Mat or using it: {e}')
            imageHeight, imageWidth, _ = image.shape
            scaleFactor = [float(desktopRes[0])*0.7/imageWidth, float(desktopRes[1])*0.7/imageHeight]
            self.invScaleFactor = [1/i for i in scaleFactor]
            image = cv2.resize(image, (0, 0), fx=scaleFactor[0], fy=scaleFactor[1])
            image = cv2.putText(image, str(realWorldPoint), org, font,  
                   fontScale, color, thickness, cv2.LINE_AA)
            windowName = 'Image'
            cv2.namedWindow(windowName)
            cv2.setMouseCallback(windowName, self.click)

            # display the image and wait for a keypress
            cv2.imshow(windowName, image)
            key = cv2.waitKey(0) & 0xFF

            # if the 'r' key is pressed, reset the cropping region
            if key == ord("n"):
                if self.currentImagePoint not in self.imagePoints:
                    self.imagePoints.append(self.currentImagePoint)
                    self.realPoints.append(self.currentRealPoint)

            # if the 'c' key is pressed, break from the loop
            elif key == ord("c"):
                self.HomographyMatrice, _ = cv2.findHomography(np.array(self.realPoints, dtype='float32'), np.array(self.imagePoints, dtype='float32'))
                break
        
        return self.HomographyMatrice

    def click(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONUP:
            currentImagePoint = [ceil(x*self.invScaleFactor[0]),ceil(y*self.invScaleFactor[1])]
            self.currentImagePoint = [float(x) for x in currentImagePoint]

    def addFooter(self, image, info):
        '''It adds footer to images and draws a rectangle on the violator in the images
        '''
        thickness = 8
        color = (0,0,255)
        topLeft = tuple(self.finalInfo['plateRoi']['topLeft'])
        bottomRight = tuple(self.finalInfo['plateRoi']['bottomRight'])
        image = cv2.rectangle(image, topLeft, bottomRight, color, thickness)
        image = cv2.resize(image, (400*2, 533)) 
        black_header = np.zeros((120,800,3), np.uint8)

        # put address 
        mlnr = 43
        address_text_on_image = "معبر : {}".format(info['cameraNameFa'])
        # address_text = first_cam_car["gps_address"]
        pil_img = put_text_on_image(2, mlnr, address_text_on_image, "small")
        cv_img = np.array(pil_img) 
        cv_img = cv_img[:, :, ::-1].copy()
        cv_img = cv2.resize(cv_img,(300,50))
        offset1_x = 0
        offset1_y = 70
        y1, y2 = offset1_y, offset1_y + cv_img.shape[0]
        x1, x2 = offset1_x, offset1_x + cv_img.shape[1]

        for c in range(3):
            black_header[y1:y2, x1:x2, c] = cv_img[:, :, c]


        # put violation title
        violation_text_on_image = "تخلف : سرعت غیرمجاز"
        # violation_text = first_cam_car["violation_title"]
        pil_img = put_text_on_image(2, mlnr, violation_text_on_image , "small")
        cv_img = np.array(pil_img) 
        cv_img = cv_img[:, :, ::-1].copy()
        cv_img = cv2.resize(cv_img,(300,50))
        offset1_x = 0
        offset1_y = 20
        y1, y2 = offset1_y, offset1_y + cv_img.shape[0]
        x1, x2 = offset1_x, offset1_x + cv_img.shape[1]
        for c in range(3):
            black_header[y1:y2, x1:x2, c] = cv_img[:, :, c]

        car_violationTime = info['time']
        violDate = car_violationTime[0].split("-")
        year = violDate[0]
        month = violDate[1]
        day = violDate[2]

        #Put Date
        y, m, d = jalali.Gregorian(year, month, day).persian_tuple()
        date_time_on_image = "تاریخ : {}/{}/{}".format(y, m, d) 
        # print(date_time_on_image)                                                       
        pil_img = put_text_on_image(2, mlnr, date_time_on_image, "small")
        cv_img = np.array(pil_img) 
        cv_img = cv_img[:, :, ::-1].copy()
        cv_img = cv2.resize(cv_img,(300,50))
        offset1_x = 490
        offset1_y = 70
        y1, y2 = offset1_y, offset1_y + cv_img.shape[0]
        x1, x2 = offset1_x, offset1_x + cv_img.shape[1]
        for c in range(3):
            black_header[y1:y2, x1:x2, c] = cv_img[:, :, c]

        #Put Time
        violHour = car_violationTime[1].split(":")
        hour = violHour[0]
        minute = violHour[1]
        second = violHour[2]
        y, m, d = jalali.Gregorian(year, month, day).persian_tuple()
        time_on_image = "زمان : {}:{}:{}".format(hour, minute, second) 
        # print(time_on_image)                                                       
        pil_img = put_text_on_image(2, mlnr, time_on_image, "small")
        cv_img = np.array(pil_img) 
        cv_img = cv_img[:, :, ::-1].copy()
        cv_img = cv2.resize(cv_img,(300,50))
        offset1_x = 250
        offset1_y = 70
        y1, y2 = offset1_y, offset1_y + cv_img.shape[0]
        x1, x2 = offset1_x, offset1_x + cv_img.shape[1]
        for c in range(3):
            black_header[y1:y2, x1:x2, c] = cv_img[:, :, c]


        # put ocr
        _ocr_on_image = "حداکثر سرعت مجاز :{}".format(info['signSpeed'])
        # print(_ocr_on_image)
        # _ocr = to_persian_plate_format(first_cam_car["ocr"])
        pil_img = put_text_on_image(2, mlnr, _ocr_on_image, "small")
        cv_img = np.array(pil_img) 
        cv_img = cv_img[:, :, ::-1].copy()
        cv_img = cv2.resize(cv_img,(300,50))
        # cv_img = cv_img[100:300,::-1,::-1]
        offset1_x = 250
        offset1_y = 20
        y1, y2 = offset1_y, offset1_y + cv_img.shape[0]
        x1, x2 = offset1_x, offset1_x + cv_img.shape[1]
        for c in range(3):
            black_header[y1:y2, x1:x2, c] = cv_img[:, :, c]

        # put camera code
        camera_code_on_image = "سرعت خودرو : {}".format(info['speed'])
        pil_img = put_text_on_image(2, mlnr, camera_code_on_image, "small")
        cv_img = np.array(pil_img) 
        cv_img = cv_img[:, :, ::-1].copy()
        cv_img = cv2.resize(cv_img,(300,50))

        offset1_x = 490
        offset1_y = 20
        y1, y2 = offset1_y, offset1_y + cv_img.shape[0]
        x1, x2 = offset1_x, offset1_x + cv_img.shape[1]
        for c in range(3):
            black_header[y1:y2, x1:x2, c] = cv_img[:, :, c]

        image = np.concatenate((image,black_header), axis=0)
        return image
     
    def toOcrCode(self, ocr):
        '''gets ocr and converts it to naja code.
        '''
        ocrMapping = {
                        "A": "01",  # الف
                        "B": "02",  # ب
                        "C": "15",  # س
                        "D": "10",  # د
                        "E": "21",  # ع
                        "G": "24",  # ق
                        "H": "31",  # ه
                        "J": "06",  # ج
                        "L": "27",  # ل
                        "M": "28",  # م
                        "N": "29",  # ن
                        "P": "03",  # پ
                        "R": "12",  # ر
                        "S": "17",  # ص
                        "T": "19",  # ط
                        "V": "30",  # و
                        "#": "33",  # , دیپلمات
                        "X": "02",  # , unknown
                        "Y": "32",  # ی
                        "Z": "13",  # ز
                        "t": "04",  # ت
                        "Q": "16",  # ش
                        "$": "15",  # س
                        "%": "34",  # siasi
                        "?": "02",  #
                        "W": "07",  # Wheelchair
                        "0": "0",
                        "1": "1",
                        "2": "2",
                        "3": "3",
                        "4": "4",
                        "5": "5",
                        "6": "6",
                        "7": "7",
                        "8": "8",
                        "9": "9",
                        }
        
        ocrCode = ''
        try:
            for c in ocr:
                ocrCode = ocrCode + ocrMapping[c]
        except Exception as e:
            ocrCode = None
            logging.info(f'Problem in converting ocr to ocrCode: {e}')
        return ocrCode

    def violationType(self, vehicleSpeed, signSpeed):
        '''Based on the violator vehicle speed and signSpeed it 
           takes decision about the violation code and returns it.
        '''
        speedDiff = vehicleSpeed - signSpeed
        thresholds = [0,30,50, 10000]
        violationCode = None
        if thresholds[0] < speedDiff <= thresholds[1]:
            violationCode = 2056
        elif thresholds[1] < speedDiff <= thresholds[2]:
            violationCode = 2008
        elif thresholds[2] < speedDiff <= thresholds[3]:
            violationCode = 2002
        else:
            logging.info(f'violation code is not set: \n Vehicle \
                    speed: {vehicleSpeed}, Sign speed: {signSpeed}')
        return violationCode