"""
Starts Sensysspeed
"""

from sensysspeed.core.dbHandling import dbHandling
from sensysspeed.core.configLoading import configLoading
from os import path

configPath = path.abspath(path.join(path.dirname(__file__), "configs", "configs.ini"))

configLoader = configLoading(configPath)
dbHandler = dbHandling(configLoader)

def run(configPath):
    """
    Run createTables
    """

    app = dbHandling(configLoader)
    app.createDbTables()
