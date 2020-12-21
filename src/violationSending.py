import json
import base64
import os, time
import requests
import logging

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

class violationSending():

    def __init__(self, configLoader):
        
        self.info = {
                    'systemId' : configLoader.get('ReceiverServer','systemId'),
                    'companyId' : configLoader.get('ReceiverServer','companyId'),
                    'Line' : 1,
                    'ImageScore' : 0,
                    'ValidInfo' : 1,
                    'WrongDirection' : 0,
                    'ExColorImage' : None,
                    'Direction' : 1,
                    'ParkometerId' : 1,
                    'Allowed' : False
                    }
        self.dataHeaders = {
                              'Content-Type': 'application/json'
                            }

        self.dataUrl = configLoader.get('ReceiverServer','receiverService')
        self.dataHeaders['x-auth-token'] = configLoader.get('ReceiverServer','token')
        if not self.dataHeaders['x-auth-token']:
            try:
                self.getTokenUrl = configLoader.get('ReceiverServer','tokenProviderService')
                self.tokenHeaders = {'Content-Type': 'application/json',
                                     'Accept':'application/json'
                                     }
                self.tokenBody = {
                                 'name' : configLoader.get('ReceiverServer','name'),
                                 'email' : configLoader.get('ReceiverServer','email'),
                                 'password' : configLoader.get('ReceiverServer','password')
                }
                self.dataHeaders['x-auth-token'] = requests.post(self.getTokenUrl, data=self.tokenBody, headers = self.tokenHeaders)
            except Exception as e:
                logging.info(f'Problem in setting token: {e}')

            configLoader.write('ReceiverServer', 'token')                


    def send(self, violationInfo):

        ResponseCode = None
        message = None
        try:
            TToInfo = self.info
            TToInfo['UniqueId'] = violationInfo['uniqueId']
            TToInfo['PassDateTime'] = ''.join([violationInfo['date'], 'T', violationInfo['time']])
            TToInfo['ReceiveDateTime'] = violationInfo['receiveDateTime']
            TToInfo['CrimeCode'] = violationInfo['crimeCode']
            TToInfo['MasterPlateNumber'] = violationInfo['ocrCode']
            TToInfo['DeviceId'] = violationInfo['deviceId']
            TToInfo['DeviceCode'] = violationInfo['policeCode']
            colorImage = open(violationInfo['footerImagePath'], 'rb')
            TToInfo['ColorImage'] = base64.b64encode(colorImage.read()).decode('utf-8')
            plateImage = open(violationInfo['plateImagePath'], 'rb')
            TToInfo['plateImage'] = base64.b64encode(plateImage.read()).decode('utf-8')
        except Exception as e:
            logging.info(f'Problem in setting data of json object before sending: {e}')

        TToInfo = json.dumps(TToInfo)
        responseCode = None
        message = None
        response = None
        try:
            response = requests.post(self.dataUrl, data=TToInfo, headers = self.dataHeaders)
        except Exception as e:
            logging.info('Problem in sending. Probably the dataUrl is not correct: {e}')
            message = 'Sent but no response'

        if not response:
            return responseCode, message
        
        return self.parseResponse(response)
        

    def parseResponse(self, response):
        '''it parses the respons coming from traffic control server and
           returns the response code and message
        '''
        try:
            response = response.json()
            return response
        except Exception as e:
            logging.info(f'Problem in parsing host response: {e}')
            return 'No Response'