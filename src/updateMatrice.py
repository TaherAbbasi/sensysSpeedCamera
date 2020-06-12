from os import path
from dbHandling import dbHandling
from configLoading import configLoading
from infoProcessing import violationProcessing
from fileManaging import fileManaging
import pickle

configDirPath = path.abspath(path.join(path.dirname(__file__), "..", "configs"))
configPath = path.abspath(path.join(configDirPath, "configs.ini"))
configLoader = configLoading(configPath)
dbHandler = dbHandling(configLoader)

processor = violationProcessing(dbHandler, configLoader)
cameraNameEn = 'RATASHE'
homoMat = processor.calculateHomographyMatrice(cameraNameEn)
homoMatFileName = path.join(configDirPath, cameraNameEn)
# print(homoMat)

with open(homoMatFileName, 'wb+') as fp:
    pickle.dump(homoMat, fp)
dbHandler.updateCamera(cameraNameEn, homoMatFileName)
