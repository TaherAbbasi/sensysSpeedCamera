from os import path
from dbHandling import dbHandling
from configLoading import configLoading
from infoProcessing import violationProcessing
from fileManaging import fileManaging
configPath = path.abspath(path.join(path.dirname(__file__), "..", "configs", "configs.ini"))

configLoader = configLoading(configPath)
dbHandler = dbHandling(configLoader)
# dbHandler.createDbTables()
fileManager = fileManaging(configLoader)
files = fileManager.listViolations()
    
processor = violationProcessing(dbHandler, configLoader)
testPath = ''
# processor.process(files[0])
for f in files:
    processor.process(f)