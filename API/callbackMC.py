import sys

sys.path.insert(0, '/var/www/html/VeriMe/VeriMe/')
from local_settings import DOWNLOAD_IMAGES_URL
from celeryconf import app
from .models import Upload, Merchant
import requests as rq
import json
import logging
from .signals import callback_merchant
import ast
import time

logger = logging.getLogger(__name__)

def waitBlankField(requestID, field):

    count = 0
    while True:
        uploader = Upload.objects.get(requestID=requestID)

        content = str(getattr(uploader, field))

        if content != 'None' and content != '':
            logger.debug('RequestID: {0} received {1} field value'.format(requestID, field))
            return True

        logger.debug('RequestID: {0} is waiting {1} field value'.format(requestID, field))
        count += 1
        if count == 300:
            logger.debug('RequestID: {0} does not receive {1} field value'.format(requestID, field))
            return False
        time.sleep(1)


def checkBlankFields(requestID, *args):

    logger.debug('args: {0}'.format(args))

    uploader = Upload.objects.get(requestID=requestID)
    for field in args:

        content = str(getattr(uploader, field))
        logger.debug('{0} value: {1}'.format(field, content))

        if content != 'None' and content != '':
            continue

        else:
            waitBlankField(requestID, field)

    return True

@app.task(bind=True, max_retries=5)
def callbackMer(self, requestID, customerId, callbackUrl):
    res = ''
    try:
        uploader = Upload.objects.get(requestID=requestID)

        payload = {'fullName': str(uploader.fullName),
                   'idNumber': str(uploader.idNumber),
                   'issused': str(uploader.issused),
                   'issPlace': str(uploader.issPlace),
                   'frontPassportUrl': DOWNLOAD_IMAGES_URL + str(uploader.frontPassportUploadFile.name).split('/')[-1],
                   'backPassportUrl': DOWNLOAD_IMAGES_URL + str(uploader.backPassportUploadFile.name).split('/')[-1],
                   'selfieUrl': DOWNLOAD_IMAGES_URL + str(uploader.selfieUploadFile.name).split('/')[-1],
                   'customerId': customerId,
                   'requestID': requestID,
                   'confidence': uploader.verifyAfterFilter,
                   'checkAction': uploader.actionResult,
                   'merchantData': uploader.merchantData
                   }

        logger.debug("Params for callback: " + str(payload))

        headers = {'Content-Type': 'application/json'}

        res = rq.post(url=callbackUrl, headers=headers, data=json.dumps(payload)).text

        # logger.debug(res)
    except Exception as e:
        logger.debug("callbackMer error: " + str(e))
        logger.debug("callbackMer response: " + str(res))
        return 0


@app.task(bind=True, max_retries=5)
def callback_merchant_handler(self, **kwargs):
    try:
        requestID = kwargs['requestID']
        userID = kwargs['userID']
        merchantToken = kwargs['merchantToken']
        checkInfoPP = kwargs['checkInfoPP']
        logger.debug('callback_merchant_handler: requestID: {0} -- userID: {1}'.format(requestID, userID))

        if checkInfoPP == False:
            checkToCallback = checkBlankFields(requestID, 'backPassportUploadFile', 'actionResult',
                                               'verifyAfterFilter', 'merchantData')
        else:
            checkToCallback = checkBlankFields(requestID, 'backPassportUploadFile', 'actionResult', 'verifyAfterFilter',
                                               'fullName', 'idNumber', 'issused', 'issPlace', 'merchantData')

        if checkToCallback:

            callbackUrl = Merchant.objects.get(merchantToken=merchantToken).callbackUrl

            logger.debug('callback_merchant_handler: requestID: {0}, callbackUrl: {1} - merchantToken: {2}'
                          .format(requestID, callbackUrl, merchantToken))

            callbackMer(requestID=requestID, customerId=userID, callbackUrl=callbackUrl)

    except Exception as e:
        logger.debug("callback_merchant_handler error: " + str(e))
        return 0

# callback_merchant.connect(callback_merchant_handler)
