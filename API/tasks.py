from celery.utils.log import get_task_logger
import requests as rq
import sys
#sys.path.insert(0, '/var/www/html/VeriMe/API/')
sys.path.append('/var/www/html/VeriMe/API/')
from .models import Upload, Merchant
from django.core.mail import send_mail
sys.path.insert(0, '/var/www/html/VeriMe/VeriMe/')
#sys.path.append('/var/www/html/VeriMe/VeriMe/')
from celeryconf import app
import celery
import ast
from .VeriMe_loadnpredict import predict
import tensorflow as tf
import json
from requests_toolbelt import MultipartEncoder
from django.contrib.auth.models import User
from .faceVerify import verify
import os
from .callOdooServer import uploadProfile, callbackMer
from .signals import callback_merchant

logger = get_task_logger(__name__)

def removeCloseDup(ls):
    ls_cp = []
    try:
        for item in ls:
            if len(ls_cp) == 0:
                ls_cp.append(item)
            else:
                if item == ls_cp[-1]:
                    continue
                ls_cp.append(item)
        return ls_cp
    except Exception as e:
        print("Error while remove duplicates!")

def checkResultMatchAndOrder(actionCode, resultList):
    try:
        resultFiltered = set([str(resultList[i][1]) for i in range(len(resultList))])
        print("ActionCode: {0} --- Result: {1}".format(set(list(actionCode)), set(resultFiltered)))
        if not (set(list(actionCode)) < set(resultFiltered)):
            return False
    #if resultFiltered.index(actionCode[0]) < resultFiltered.index(actionCode[1]) and resultFiltered.index(actionCode[1]) < resultFiltered.index(actionCode[2]):
    #    return True
    except Exception as e:
        print(str(e))
        return False
    return True

@app.task(bind=True, max_retries=5)
def updateResultVAYMUON(self, server, token, verimeSessionId, profileId, actionResult, confidence, summary):
    #url = "http://beta2.vaymuon.vn/public/verime/update-user-result"
    #url = "http://192.168.11.72/public/verime/update-user-result"
    print('token: {0},verimeSessionId: {1},profileId: {2},actionResult: {3},server: {4}, confidence: {5}, sumary: {6}'.format(str(token), str(verimeSessionId), str(profileId), str(actionResult), str(server), str(confidence), str(summary)))
    if confidence != '-1':
        upload = Upload.objects.get(requestID=verimeSessionId)
        actionReport = ast.literal_eval(str(upload.actionReport))
        # wait checkAction() finishing, check by each 1 min
        wait_checkAction = 0
        while True:
            if str(actionReport['actionCodeMatch']) != '100':
                actionResult = actionReport['actionCodeMatch']
                summary = '1' if str(actionResult) == '1' and float(confidence) >= 0.48 else '0'
                break
            if wait_checkAction == 600:
                confidence = '-1'
                break
            wait_checkAction += 60
            print('waiting check actions')
            time.sleep(60)

    url = os.path.join(str(server), "verime/update-user-result")
    headers = {"Content-Type": "application/json"}
    data = {"parameter":{ "token": str(token),
                          "verimeSessionId": str(verimeSessionId),
                          "profileId": str(profileId),
                          "actionResult": str(actionResult),
                          "confidence": str(confidence),
                          "summary": summary }}
    try:
        res = rq.post(url=url, headers=headers, data=json.dumps(data))
    except Exception as e:
        self.retry(exc=e, countdown=60)
        return str(e)
    print(res.text)

@app.task(bind=True, max_retries=6)
def uploadPhotoVAYMUON(self, token, images, profileId, server):
    print('token: {0},images: {1},profileId: {2}, server: {3}'.format(str(token), str(images), str(profileId), str(server)))
    #url = "http://beta2.vaymuon.vn/public/profile/upload-photo"
    #url = "http://192.168.11.72/public/profile/upload-photo"
    url = os.path.join(str(server), "profile/upload-photo")
    multipart_data = MultipartEncoder(
                       fields={
                               "parameter.files[0]": ("front.jpg", open(images[0], "rb"), "image/jpeg"),
                               "parameter.files[1]": ("back.jpg", open(images[1], "rb"), "image/jpeg"),
                               "parameter.files[2]": ("selfie.jpg", open(images[2], "rb"), "image/jpeg"),
                               "parameter.profileId": str(profileId),
                               "parameter.profileType": "0",
                               "parameter.token": str(token)
                              }
    )
    headers = {"Content-Type": multipart_data.content_type}
    try:
        res = rq.post(url=url, headers=headers, data=multipart_data)
    except Exception as e:
        print(str(e))
        self.retry(exc=e, countdown=30)
    print(res.text)

def makeVerify(passportImgPath, selfieImgPath, key):
    
    faceVer = verify()
    result = {}
    try:
        result = faceVer.faceVerify(passportImgPath, selfieImgPath, key)
    except Exception as e:
        result["error_code"]= "20"
        result["error_desc"] =  str(e)

    result["error_code"] = "0"
    result["error_desc"] = ""
    
    return result

@app.task(bind=True, max_retries=5)
def checkAction(self, merchantToken, requestID, actionCode, vidLink):
    try:
        logger.info('checkAction input: merchantToken: {0}, requestID: {1}, actionCode: {2}, vidLink: {3}')

        upload = Upload.objects.get(requestID=requestID)

        check = predict()
        tf.get_variable_scope().reuse_variables()
        resultList = check.pre(vidLink)

        match_rightOrder = checkResultMatchAndOrder(actionCode, resultList)
        upload.actionResult = int(match_rightOrder)
        upload.save(update_fields=['actionResult'])
        
        # #using signals
        # logger.info('Using signals in checkAction')
        # callback_merchant.send(sender=None, requestID=requestID, userID=upload.userID, merchantToken=merchantToken,
        #                        checkInfoPP=False)
        
        logger.info("Match action code and order: {0}".format(match_rightOrder))
        uploadProfile.delay(requestID=requestID, merchantToken=merchantToken, fullName='', idNumber='', issused='', issPlace='', customerId=upload.userID, verimeResult='', checkActionResult = str(int(match_rightOrder)), frontPassportURL='', backPassportURL='', selfieURL='', phoneBook='', callLog='', GPS='')
    except Exception as e:
        return str(e)

@app.task(bind=True, max_retries=6)
def callbackMerchant(self, requestID):

    upload = Upload.objects.get(requestID=requestID)
    owner = str(upload.owner)
    logger.info(owner)
#    if owner=="VAYMUON":
#        pass               
    #return
            #if self.request.retries == 1:
            #    self.retry(exc=e, countdown=60)

            #if self.request.retries == 2:
            #    self.retry(exc=e, countdown=3*60)

            #if self.request.retries == 3:
            #    self.retry(exc=e, countdown=10*60)

            #if self.request.retries == 4:
            #    self.retry(exc=e, countdown=20*60)

            #if self.request.retries == 5:
            #    self.retry(exc=e, countdown=30*60)

            #elif self.request.retries > 5:
            #    upload.callbackStatus = 0
            #    return

            #self.retry(exc=e, countdown=10)

    #upload.save()
    #return res.content

@app.task(bind=True, max_retries=6)
def sendEmail(self, address, passwd):
    content = "Welcome to VeriMe,\n\nHere's your password to login VeriMe application: {0}\n\nBest Regards,".format(passwd)
    try:
        send_mail(
        'VeriMe: Your Password!',
        content,
        'verime@nexttech.asia',
        [address],
        fail_silently=False,
        )
    except Exception as e:
        print('retry in {0} time(s)'.format(self.request.retries))
        self.retry(exc=e, countdown=10)

