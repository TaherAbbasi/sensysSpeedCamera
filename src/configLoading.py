from configparser import ConfigParser
import logging
import os

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

class configLoading():

    def __init__(self, configPath):
        '''
        '''
        assert isinstance(configPath, str), 'string is expected: %r' % configPath
        assert os.path.exists(configPath), 'File not exists: %r' % configPath
        self.config = ConfigParser()
        self.config.read(configPath)

    def get(self, configSection, configName):

        try:
            config = self.config.get(configSection, configName)
        except Exception as e:
            logging.info(f'problem in reading config: {e}')
            return None
        return config
    
    def write(self, configSection, configName):
        
        isConfigSet = False
        try:
            self.config.set(configSection, configName)
            isConfigSet = True    
        except Exception as e:
            logging.info(f'problem in setting config: {e}')
        return isConfigSet

