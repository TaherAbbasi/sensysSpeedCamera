from os import path
from ..core.dbHandling import dbHandling
from ..core.configLoading import configLoading
from ..core.infoProcessing import violationProcessing
from ..core.fileManaging import fileManaging
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
