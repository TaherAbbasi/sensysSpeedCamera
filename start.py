import sys
from os import path
from sensysspeed.core.dbHandling import dbHandling
from sensysspeed.core.configLoading import configLoading
from sensysspeed.core.infoProcessing import violationProcessing
from sensysspeed.core.fileManaging import fileManaging

configPath = path.abspath(path.join(path.dirname(__file__), 'sensysspeed', 'configs', 'configs.ini'))

configLoader = configLoading(configPath)
dbHandler = dbHandling(configLoader)
dbHandler.createDbTables()
fileManager = fileManaging(configLoader)
files = fileManager.listViolations()
    
processor = violationProcessing(dbHandler, configLoader)

for f in files:
    processor.process(f)

