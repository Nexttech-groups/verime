import sys

sys.path.append('/var/www/html/VeriMe/VeriMe')
import settings
import requests as rq
import ast
import logging

sys.path.insert(0, '/var/www/html/VeriMe/VeriMe/')
# sys.path.append('/var/www/html/VeriMe/VeriMe/')
from celeryconf import app
import celery
import json

logger = logging.getLogger(__name__)


def getMerchantInfo(merchantId, userID, requestID):
    getMerchantUrl = settings.local_settings.GET_MERCHANT_INFO_URL
    params = "mc=" + str(merchantId) + "&customer_code=" + str(userID) + "&request_id=" + str(requestID)
    res = ""
    try:
        res = ast.literal_eval(rq.get(getMerchantUrl + params).text)
        logger.debug(res)
        if len(res) != 0:
            return res["merchant_token"], res["merchant_name"], res["type_approve"], res["call_back_url"], res[
                "change_info"], res["verime_cutoff"]
        else:
            return 0
    except Exception as e:
        logger.debug("getMerchantInfo error: " + str(e))
        logger.debug("getMerchantInfo response: " + str(res))
        return 1


@app.task(bind=True, max_retries=5)
def uploadProfile(self, **kwargs):

    logger.debug('Params to upload backend: ' + str(kwargs))

    uploadProfileURL = settings.local_settings.UPLOAD_PROFILE_URL

    listParams = {'requestID': '', 'merchantToken': '', 'fullName': '', 'idNumber': '', 'issused': '', 'issPlace': '',
                  'customerId': '', 'verimeResult': '', 'checkActionResult': '', 'frontPassportURL': '',
                  'backPassportURL': '', 'selfieURL': '', 'phoneBook': '', 'callLog': '', 'GPS': ''}

    for key in kwargs.keys():
        listParams[key] = kwargs[key]

    data = {"request_id": listParams['requestID'], "merchantToken": listParams['merchantToken'],
            "fullName": listParams['fullName'], "idNumber": listParams['idNumber'], "issused": listParams['issused'],
            "issPlace": listParams['issPlace'], "customerId": listParams['customerId'],
            "verimeResult": str(listParams['verimeResult']), "checkActionResult": listParams['checkActionResult'],
            "frontPassportURL": listParams['frontPassportURL'], "backPassportURL": listParams['backPassportURL'],
            "selfieURL": listParams['selfieURL'], "phoneBook": listParams['phoneBook'], "callLog": listParams['callLog'],
            "GPS": listParams['GPS']}

    res = ""
    # logger.debug("uploadProfile data: " + str(data))
    try:
        res = ast.literal_eval(rq.post(url=uploadProfileURL, data=data).text)
        logger.debug(res)
        if len(res) != 0:
            return 1
    except Exception as e:
        logger.debug("uploadProfile error: " + str(e))
        logger.debug("uploadProfile response: " + str(res))
        return 0


@app.task(bind=True, max_retries=5)
def callbackMer(self, url, customerID, result):
    params = 'result=' + str(result) + '&customerID=' + customerID
    res = ''
    try:
        res = rq.get(url=url, params=params).text
        logger.debug(res)
    except Exception as e:
        logger.debug("callbackMer error: " + str(e))
        logger.debug("callbackMer response: " + str(res))
        return 0
