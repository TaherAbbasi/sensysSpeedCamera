from dbHandling import dbHandling
from configLoading import configLoading
from os import path
import xlrd

configPath = path.abspath(path.join(path.dirname(__file__), "..", "configs", "configs.ini"))

configLoader = configLoading(configPath)
dbHandler = dbHandling(configLoader)
cameraInfoPath = configLoader.get('main', 'cameraInfoPath')


workbook = xlrd.open_workbook(cameraInfoPath)
sheet = workbook.sheet_by_index(0)
for rowx in range(1,sheet.nrows):
    cameraInfo = sheet.row_values(rowx)
    dbHandler.insertCamera(tuple(cameraInfo))

