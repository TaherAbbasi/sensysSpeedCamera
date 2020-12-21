from pathlib import Path
from PIL import Image
import shutil
import logging
from shutil import copy2
import re
import glob
import os
import itertools
import tarfile
import cv2

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

class fileManaging():

    def __init__(self, configLoader):

        try:
            self.configLoader = configLoader
            self.ftpPath = self.configLoader.get('main','ftpPath')
            self.archivePath = self.configLoader.get('main','archivePath')
            self.tarFileLevel = self.configLoader.get('main','tarFileLevel')
            self.sizeLimit = self.configLoader.get('files','colorImageSizeLimit')
            self.imageNamePattern = self.configLoader.get('files', 'imageNamePattern')
            self.xmlNamePattern = self.configLoader.get('files', 'xmlNamePattern')
        except Exception as e:
            logging.info(f'Problem in loading configs: {e}')
            return None

        try:
            self.tarFileLevel = int(self.tarFileLevel)
        except Exception as e:
            logging.info(f'TarFileLevel in config file must be an integer: {e}')
            return None


    def archive(self, srcFilePath, extractionPath):
        '''It moves files from srcpath to extractionPath
        '''        
        isArchived = False
        tarFileName = srcFilePath.split(os.sep)[-1]
        dstFilePath = os.path.join(extractionPath, tarFileName)
        try:
            shutil.move(srcFilePath, dstFilePath, copy_function=copy2)
            isArchived = True
        except Exception as e:
            logging.info(f'Problem in archiving file: {e}')
        return isArchived


    def setFilesPath(self, extractionPath):
        '''It set xml file path and image file path and
            returns them in a dictionary
        '''
        filesPath = {'xmlPath': '',
                     'imagePath': ''}
        fileNames = glob.glob(os.path.join(extractionPath,'*'))
        for f in fileNames:
            if re.findall(self.imageNamePattern, f):
                filesPath['imagePath'] = f
            elif re.findall(self.xmlNamePattern, f):
                filesPath['xmlPath'] = f

        if filesPath['xmlPath'] and filesPath['imagePath']:
            return filesPath
        else:
            return None

    def resizeImageVolume(self, largeImagePath):
        '''Resizes image to a lower volume. for example
           it resizes an 500 Kbyte image to a 300 Kbyte image
        '''
        sizeScale = 0.9
        isLarge = True

        kbyteToByte = 1024
        sizeLimit = self.sizeLimit * kbyteToByte
        while isLarge is True:
            try:
                imageSize = Path(largeImagePath).stat().st_size
                sizeScale = sizeLimit / imageSize
            except Exception as e:
                logging.info(f'Problem in calculating image size: {e}')
                return isLarge, largeImagePath

            if sizeScale > 1:
                isLarge = False
                return isLarge, largeImagePath
                
            if sizeScale > 0.9:
                sizeScale = 0.9
            elif sizeScale < 0.7:
                sizeScale = 0.7
            image = Image.open(largeImagePath)
            width = image.size[0] * sizeScale 
            height = image.size[1] * sizeScale
            dim = (int(width), int(height))
            image = image.resize(dim, Image.ANTIALIAS)
            try:
                image.save(largeImagePath, optimize=False, quality=50)
            except Exception as e:
                print(f'Problem in saving image: {e}')
            return isLarge, largeImagePath
    
    def listViolations(self):
        '''lists all violations in the ftpPath'''
        filesPath = self.ftpPath
        for _ in itertools.repeat(None, self.tarFileLevel):
            filesPath = os.path.join(filesPath,'*')
        files = glob.glob(filesPath)

        return files

    def extractFiles(self, violationFilePath):
        ''' extract violaionPath which is the path of a
            tar file and sets xmlPath and imagePath
        '''
        extractionPath = None
        try:
            tarFile = tarfile.open(violationFilePath)
            violationDirName, _ = os.path.splitext(violationFilePath)
            extractionPath = Path(violationDirName.replace(self.ftpPath,
                                     self.archivePath))
            tarFile.extractall(extractionPath)
            tarFile.close()
        except:
            logging.info(f'Problem in extracting tar file: \
                {violationFilePath}\n Extraction Path: {extractionPath}')
        
        return extractionPath

    def saveImage(self, path, image):
        '''It get a path and an image and save the image in the path
        '''
        isSaved = False
        try:
            cv2.imwrite(path, image)
            isSaved = True
        except Exception as e:
            logging.info(f'Problem in saving image: {e}')
        return isSaved

