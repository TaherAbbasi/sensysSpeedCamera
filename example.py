from os import path
from .core.dbHandling import dbHandling
from .core.configLoading import configLoading
from .core.infoProcessing import violationProcessing
from .core.fileManaging import fileManaging
configPath = path.abspath(path.join(path.dirname(__file__), "..", "configs", "configs.ini"))

configLoader = configLoading(configPath)
dbHandler = dbHandling(configLoader)
# dbHandler.createDbTables()
fileManager = fileManaging(configLoader)
files = fileManager.listViolations()
    
processor = violationProcessing(dbHandler, configLoader)
testPath = ''
for f in files:
    processor.process(f)