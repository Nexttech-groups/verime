import json
import os
import requests
import ast
import logging

logger = logging.getLogger(__name__)

key = '[AZURE_SERVICE_KEY]'
detectUrl = 'https://eastus2.api.cognitive.microsoft.com/face/v1.0/detect?returnFaceId=true'
verifyUrl = 'https://eastus2.api.cognitive.microsoft.com/face/v1.0/verify'

class verify():

    def getImageId(self, imgPath, key):
        # print(imgPath)
        headers = {'Content-Type': 'application/octet-stream', 'Ocp-Apim-Subscription-Key': key}
        # detectUrl = 'https://api.projectoxford.ai/face/v1.0/detect?returnFaceId=true'
        files = open(imgPath, 'rb').read()
        try:
            res = requests.post(url=detectUrl, headers=headers, data=files).text
            res = ast.literal_eval(res)
            logger.debug('faceId: ' + str(res[0]['faceId']))
            return res[0]['faceId']
        except Exception as e:
            return e


    def faceVerify(self, image1, image2, key1):
        headers = {'Content-Type': 'application/json', 'Ocp-Apim-Subscription-Key': key}
        # verifyUrl = 'https://api.projectoxford.ai/face/v1.0/verify'

        payload = {}
        payload['faceId1'] = self.getImageId(image1, key)
        print('fd1' + payload['faceId1'])
        payload['faceId2'] = self.getImageId(image2, key)
        print('fd2' + payload['faceId2'])

        try:
            rq = requests.post(url=verifyUrl, data=json.dumps(payload), headers=headers)
            data = rq.json()
            rq.close()
            return data
        except Exception as e:
            return e

# ver=verify()
# print(ver.faceVerify('/Users/pro/Desktop/h1.jpeg',
#                      '/Users/pro/Desktop/h2.jpeg', key1=''))
