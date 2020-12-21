"""
There we initialize the database, insert, delete, and modify data in the
database
"""
import mysql
from mysql import connector
import os
from mysql.connector import Error
from os.path import splitext
import shutil
from shutil import copy2
import logging
import ast
import numpy as np
from sensysspeed.core.exceptions import ConfigLoadingError, DatabaseConnectionError

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

class dbHandling():

    def __init__(self, configLoader):

        self.configLoader = configLoader

        try:
            self.host = configLoader.get('database', 'host')
            self.username = configLoader.get('database', 'username')
            self.password = configLoader.get('database', 'password')
            self.dbName = configLoader.get('database', 'dbName')
            self.characterSet = configLoader.get('database', 'characterSet')
            self.collation = configLoader.get('database', 'collation')
        except ConfigLoadingError as e:
            logging.info(ConfigLoadingError)
            return None            

        try:
            self.db = mysql.connector.connect(
                host=self.host,
                user=self.username,
                passwd=self.password,
                database=self.dbName
            )
        except Exception as e:
            logging.info(e)
            self.createDB()
            try:
                self.db = mysql.connector.connect(
                    host=self.host,
                    user=self.username,
                    passwd=self.password,
                    database=self.dbName
                )
            except Exception as e:
                logging.info(e)

    def createDbTables(self):
        try:
            cursor = self.db.cursor()
        except AttributeError as e:
            logging.info(f'Database not exists: {e}')
            return None
        
        # SQL for creating Cameras Table
        sqlCommand = 'CREATE TABLE IF NOT EXISTS cameras ( \
                nameEn VARCHAR(100) NOT NULL PRIMARY KEY, \
                nameFa VARCHAR(100), \
                policeCode INT(20), \
                deviceId INT(20), \
                homographyMatrice VARCHAR(200))'
        cursor.execute(sqlCommand)
        self.db.commit()

        # SQL for creating violation types
        sqlCommand = 'CREATE TABLE IF NOT EXISTS violationTypes ( \
                nameFa VARCHAR(100), \
                code INT(20) NOT NULL PRIMARY KEY, \
                lowerSpeedThreshold INT(4), \
                upperSpeedThreshold INT(4) \
                )'
        cursor.execute(sqlCommand)
        self.db.commit()


        sqlCommand = '''
                CREATE TABLE IF NOT EXISTS violations(
                id INT AUTO_INCREMENT UNIQUE KEY,
                creationDate DATETIME,
                sentDate DATETIME,
                violDate DATE,
                violTime TIME,
                state ENUM('dirInserted',
                            'infoInserted',
                            'footerAdded',
                            'sent',
                            'NotSent',
                            'rejected',
                            'archived',
                            'underProcess',
                            'notProcessed') NOT NULL,
                ocr CHAR(12),
                ocrCode INT(30),
                confidence FLOAT,
                violationCode INT(6),
                dir VARCHAR(200),
                cameraNameEn VARCHAR(100),
                responseCode INT(4),
                responseMessage VARCHAR(100),
                operatorName VARCHAR(30),
                uniqueID VARCHAR(200) UNIQUE KEY,
                FOREIGN KEY (cameraNameEn) REFERENCES cameras(nameEn) ON DELETE CASCADE,
                FOREIGN KEY (violationCode) REFERENCES violationTypes(code) ON DELETE CASCADE)
                '''
        cursor.execute(sqlCommand)
        self.db.commit()
    
    def insertViolation(self, violationInfo):
        cursur = self.db.cursor()
        sqlCommand = '''INSERT INTO violations 
                        (creationDate,
                            sentDate,
                            violDate,
                            violTime,
                            state,
                            ocr,
                            ocrCode,
                            confidence,
                            violationCode,
                            dir,
                            cameraNameEn,
                            responseCode,
                            responseMessage,
                            operatorName
                            uniqueID
                            )
                            VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            '''
        try:
            cursur.execute(sqlCommand, (
                violationInfo['creationDate'],
                violationInfo['sentDate'],
                violationInfo['date'],
                violationInfo['time'],
                violationInfo['state'],
                violationInfo['ocr'],
                violationInfo['ocrCode'],
                violationInfo['violationCode'],
                violationInfo['dir'],
                violationInfo['cameraNameEn'],
                violationInfo['responseCode'],
                violationInfo['message'],
                'Taher',
                violationInfo['uniqeID']
            ))
            
            self.db.commit()
        except Exception as e:
            logging.info(f'Insert Camera Exception: {e}')

    def insertViolations(self, violationsInfo):
        pass

    def insertCamera(self, cameraInfo):
        isCameraInserted = False
        try:
            cursor = self.db.cursor()
            sql = 'INSERT INTO cameras (nameEn, nameFa, policeCode, \
                 deviceId, homographyMatrice) VALUES (%s, %s, %s, %s, %s)'
            cursor.execute(sql, cameraInfo)
            cursor.close()
            self.db.commit()
            isCameraInserted = True
        except Exception as e:
            logging.info(f'Problem in inserting camera: {e}')
        
        return isCameraInserted

    def insertViolationType(self, violationTypeInfo):
        isViolationTypeInserted = False
        try:
            cursor = self.db.cursor()
            sqlCommand = '''
                            INSERT INTO violationTypes(nameFa,
                            code,
                            lowerSpeedThreshold,
                            upperSpeedThreshold) 
                            VALUES (%s, %s, %s, %s)
                            '''
            cursor.execute(sqlCommand, violationTypeInfo)
            cursor.close()
            self.db.commit()
            isViolationTypeInserted = True
        except Exception as e:
            logging.info(f'Problem in inserting violation type: {e}')
        
        return isViolationTypeInserted

    def getViolations(self, state='All', cameraName='All' , fromDate='2015-01-01', toDate='2030-01-01'):
        '''
        '''
        cursor = self.db.cursor()
        if state =='All':
            state = '%%'
        if cameraName =='All':
            cameraName = '%%'

        sqlCommand = 'SELECT * FROM violations \
                      WHERE state LIKE %s and \
                      cameraName LIKE %s and \
                      date > %s and \
                      date < %s and \
                      ORDER BY date DESC, time'
        cursor.execute(sqlCommand, (state, cameraName, fromDate, toDate))
        violations = cursor.fetchall()
        return violations

    def getCamerasInfo(self):
        sql = 'select * from cameras'
        cursor = self.db.cursor()
        camerasInfo = {}
        cursor.execute(sql)
        cameras = cursor.fetchall()
        if not cameras:
            return None
        for c in cameras:
            try:
                camerasInfo[c[0]] = {'nameFa': c[1],
                                    'policeCode': c[2],
                                    'deviceId': c[3],
                                    'homographyMatrice': c[4]
                                    }
            except Exception as e:
                logging.info(f'Camera info is wrong: {e}')
        return camerasInfo

    def createDB(self):
        '''it creates database dbSpeed if not exists
        '''
        try:
            dbConnection = mysql.connector.connect(
                host=self.host,
                user=self.username,
                passwd=self.password)
            dbCursor = dbConnection.cursor()
         
            # SQL for creating Database
            sql = 'CREATE DATABASE IF NOT EXISTS speedDb CHARACTER SET utf8 COLLATE utf8_general_ci'

            dbCursor.execute(sql)
            dbCursor.close()
            dbConnection.commit()
            dbConnection.close()
            logging.info('Database created. Try again')
        except Exception as e:
            logging.info(f'Problem in creating database: {e}')

    def updateCamera(self, cameraNameEn, homoMat):
        '''
        '''
        cursor = self.db.cursor()
        sqlCommand = 'update cameras set homographyMatrice = %s WHERE nameEn = %s'
        cursor.execute(sqlCommand, (homoMat, cameraNameEn))
        self.db.commit()
