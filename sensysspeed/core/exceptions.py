# -*- coding: utf-8 -*-

# This work is licensed under the MIT License.
# To view a copy of this license, visit https://www.gnu.org/licenses/

# Written by Taher Abbasi
# Email: abbasi.taher@gmail.com
from mysql.connector import Error

class ALPRConnectionError(Exception):
    """Exception raised when ALPR engine is not responding."""


    def __init__(self, message="can\'t connect to the ALPR"):
        self.message = message
        super().__init__(self.message)

class DatabaseConnectionError(Error):
    """Exception raised when can\'t connect to the database."""
    

    def __init__(self, message="can\'t connect to the the database"):
        self.message = message
        super(DatabaseConnectionError).__init__(self.message)

class WrongSideError(Exception):
    """Exception raised when the side is wrong. i.e. is neither TOP,
       nor BOTTOM, nor RIGHT, nor LEFT"""


    def __init__(self, message="side have to be either TOP or BOTTM\
                                or RIGHT, or LEFT."):
        self.message = message
        super().__init__(self.message)

class ConfigLoadingError(Exception):
    """Raised when can\'t load config file."""


    def __init__(self, message="Can\'t load config file"):
        self.message = message
        super().__init__(self.message)
