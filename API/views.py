from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from rest_framework.response import Response
import rest_framework.permissions as permissions
import io, os, sys, time
import rest_framework.authentication as authentication
import datetime
from .models import Upload, Merchant
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils import timezone
from django.http import HttpResponse
from .faceVerify import verify
from uuid import uuid4
# from .tasks import callbackMerchant, checkAction
from .tasks import checkAction
import random
import logging
# from django.core.mail import send_mail
# from wsgiref.util import FileWrapper
from django.http import FileResponse
from .VeriMe_loadnpredict import predict
import cv2
import ast
import requests as rq
from django.views import View
from sendfile import sendfile
from .signals import callback_merchant
from rest_framework import HTTP_HEADER_ENCODING, exceptions
# from rest_framework_jwt import authentication
sys.path.append('/var/www/html/VeriMe/VeriMe')
import settings
from .callOdooServer import getMerchantInfo, uploadProfile
from .serializers import submitInfoSerializer, getScriptSerializer, passportUploadSerializer, actionUploadSerializer, \
    selfieUploadSerializer, callbackMerchantSerializer, receiveMerchantInfoFromBackendSerializer
from .callbackMC import callbackMer, callback_merchant_handler
import copy

logger = logging.getLogger(__name__)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def randomOrder(numOfActions):
    if numOfActions == 1:
        return random.randint(1, 5)

    if numOfActions == 2:
        ran = random.sample(range(1, 6), 2)
        return str(ran[0]) + "-" + str(ran[1])

    ran = random.sample(range(1, 6), 3)
    return str(ran[0]) + "-" + str(ran[1]) + "-" + str(ran[2])


class receiveMerchantInfoFromBackend(APIView):
    def post(self, request, format=None):
        logger.info("Load receiveMerchantInfoFromBackend API")

        try:
            logger.debug("Data from backend: " + str(request.data))
        except Exception as e:
            logger.debug("Interrupted request: " + str(e))
            return Response()

        try:

            serializer = receiveMerchantInfoFromBackendSerializer(data=request.data)
            if not serializer.is_valid(raise_exception=True):
                logger.debug(str(serializer.errors))

            serializer.save()

            return Response(settings.local_settings.SUCCESS_RESPONSE,
                            content_type='application/json', status=status.HTTP_200_OK)

        except Exception as e:
            logger.error('Error in receiveMerchantInfoFromBackend API: ' + str(e))
            return Response(settings.local_settings.UNDEFINE_ERROR_RESPONSE,
                            content_type='application/json', status=status.HTTP_400_BAD_REQUEST)


class getScript(APIView):
    authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, format=None):
        logger.debug("Load getScript API")

        # check interupt request
        try:
            logger.debug("Data from client: " + str(request.data))
        except Exception as e:
            logger.debug("Interrupted request: " + str(e))
            return Response()



        serializer = getScriptSerializer(data=request.data)
        if not serializer.is_valid(raise_exception=True):
            logger.debug(str(serializer.errors))

        try:

            merchantToken = serializer.validated_data.get('merchantToken')
            merchantData = serializer.validated_data.get('merchantData')
            userID = serializer.validated_data.get('userID')
            numOfActions = serializer.validated_data.get('numOfActions')

            requestID = uuid4().hex
            actionScript = randomOrder(int(numOfActions))

            uploadProfile.delay(requestID=requestID, merchantToken=merchantToken, customerId=userID)

            upload = Upload.objects.create(owner=request.user,
                                           userID=userID,
                                           requestID=requestID,
                                           actionScript=actionScript,
                                           requestID_expire=int(
                                               round(time.time(), 0)) + settings.local_settings.REQUESTID_EXPIRE_TIME,
                                           merchantData=merchantData
                                           )
            upload.save()

            SUCCESS_RESPONSE = copy.deepcopy(settings.local_settings.SUCCESS_RESPONSE)
            SUCCESS_RESPONSE.update({"actionScript": str(actionScript), "requestID": requestID})

            return Response(SUCCESS_RESPONSE, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(str(e))
            return Response(settings.local_settings.UNDEFINE_ERROR_RESPONSE,
                            content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

class passportUpload(APIView):
    authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, format=None):
        logger.debug("Load passportUpload API")

        try:
            logger.debug("Data from client: " + str(request.data))
        except Exception as e:
            logger.debug("Interrupted request: " + str(e))
            return Response()

        serializer = passportUploadSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid(raise_exception=True):
            logger.debug(str(serializer.errors))

        serializer.save()

        return Response(settings.local_settings.SUCCESS_RESPONSE, content_type='application/json',
                            status=status.HTTP_201_CREATED)


class actionUpload(APIView):
    authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, format=None):
        logger.debug("Load actionUpload API")

        try:
            logger.debug("Data from client: " + str(request.data))
        except Exception as e:
            logger.debug("Interrupted request: " + str(e))
            return Response()

        serializer = actionUploadSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid(raise_exception=True):
            logger.debug(str(serializer.errors))

        try:

            # merchantToken = serializer.validated_data.get('merchantToken')
            requestID = serializer.validated_data.get('requestID')
            actionVid = serializer.validated_data.get('actionVid')
            actionCode = serializer.validated_data.get('actionCode')
            actionCode = actionCode.replace('-', '')

            upload = Upload.objects.get(requestID=requestID)
            upload.actionVid = actionVid
            upload.save(update_fields=['actionVid'])
            merchantToken = Token.objects.get(user=upload.owner).key

            vidLink = str(upload.actionVid)
            checkAction.delay(merchantToken=merchantToken, requestID=requestID, actionCode=actionCode, vidLink=vidLink)

            return Response(settings.local_settings.SUCCESS_RESPONSE, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("actionUpload API error: " + str(e))
            return Response(settings.local_settings.UNDEFINE_ERROR_RESPONSE,
                            content_type='application/json', status=status.HTTP_400_BAD_REQUEST)


class selfieUpload(APIView):
    authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, format=None):
        logger.debug("Load selfieUpload API")

        try:
            logger.debug("Data from client: " + str(request.data))
        except Exception as e:
            logger.debug("Interrupted request: " + str(e))
            return Response()

        requestID = request.data['requestID']

        try:
            upload = Upload.objects.get(requestID=requestID)
        except Exception as e:
            logger.error("selfieUpload API error: " + str(e))
            raise exceptions.NotFound({"error_code": "002", "error_desc": "RequestID not found!"})

        serializer = selfieUploadSerializer(upload, data=request.data, context={'request': request})
        if not serializer.is_valid(raise_exception=True):
            logger.debug(str(serializer.errors))

        data = serializer.save()
        try:

            passportImgPath = os.path.join(BASE_DIR, upload.frontPassportUploadFile.name)
            # backPassportImgPath = os.path.join(BASE_DIR, upload.backPassportUploadFile.name)
            selfieImgPath = os.path.join(BASE_DIR, data.selfieUploadFile.name)

            merchantName = data.owner
            logger.debug(merchantName)
            merchant = Merchant.objects.get(user=merchantName)
            key = merchant.merchantKey
            merchantToken = Token.objects.get(user=data.owner).key

            faceVer = verify()

            try:

                logger.debug('requestID: {0} -- image for verification: {1} - {2}'.format(data.requestID, passportImgPath,
                                                                                          selfieImgPath))
                result = faceVer.faceVerify(passportImgPath, selfieImgPath, key)

            except Exception as e:
                uploadProfile.delay(requestID=data.requestID, merchantToken=merchantToken,
                                    customerId=upload.userID, verimeResult=-1)
                logger.debug('Face Verification Error: ' + str(e))
                return Response({"error_code": "017", "error_desc": "Face Verification Error!", "status": 0},
                                content_type='application/json', status=status.HTTP_200_OK)

            ver_status = 1 if float(result['confidence']) >= float(merchant.confidenceThreshold) else 0
            upload.verifyAfterFilter = ver_status
            logger.debug('requestID: {0} -- Verify Result: {1} -- Confidence: {2}'.format(data.requestID, str(ver_status),
                                                                                          str(result['confidence'])))

            upload.verifyResultFromMS = str(result)
            upload.save(update_fields=['verifyResultFromMS', 'verifyAfterFilter'])

            uploadProfile.delay(requestID=data.requestID, merchantToken=merchantToken,
                                customerId=upload.userID, verimeResult=result['confidence'])

            # using signals
            logger.debug('Using signals in selfieUpload API')
            callback_merchant_handler.delay(requestID=requestID, userID=upload.userID, merchantToken=merchantToken,
                                   checkInfoPP=False)

            SUCCESS_RESPONSE = copy.deepcopy(settings.local_settings.SUCCESS_RESPONSE)
            SUCCESS_RESPONSE.update({"fullName": "", "idNumber": "",
                                     "issused": "", "issPlace": "", "status": ver_status,
                                    })
            return Response(SUCCESS_RESPONSE, content_type='application/json',
                status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(str(e))
            return Response(settings.local_settings.UNDEFINE_ERROR_RESPONSE,
                           content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

class submitInfo(APIView):
    authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, format=None):
        logger.debug("Load submitInfo API")

        try:
            # logger.debug("Data from client: "+str(request.data))
            request.data
        except Exception as e:
            logger.debug("Interrupted request: " + str(e))
            return Response()

        serializer = submitInfoSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid(raise_exception=True):
            logger.debug(str(serializer.errors))

        try:
            # merchantToken = request.data['merchantToken']
            requestID = request.data['requestID']
            fullName = request.data['fullName']
            idNumber = request.data['idNumber']
            issused = request.data['issused']
            issPlace = request.data['issPlace']
            phoneBook = request.data['phoneBook']
            callLog = request.data['callLog']
            GPS = request.data['GPS']

            upload = Upload.objects.get(requestID=requestID)
            merchantToken = Token.objects.get(user=upload.owner).key

            uploadProfile.delay(requestID=requestID, merchantToken=merchantToken, fullName=fullName, idNumber=idNumber,
                                issused=issused, issPlace=issPlace, customerId=upload.userID, phoneBook=phoneBook,
                                callLog=callLog, GPS=GPS)

            update_info = {'fullName': fullName, 'idNumber': idNumber, 'issused': issused, 'issPlace': issPlace,
                           'phoneBook': phoneBook, 'callLog': callLog, 'GPS': GPS}
            Upload.objects.filter(requestID=requestID).update(**update_info)

            # using signals
            logger.debug('Using signals in submitInfo API')
            callback_merchant_handler.delay(sender=None, requestID=requestID, userID=upload.userID, merchantToken=merchantToken)

            return Response(settings.local_settings.SUCCESS_RESPONSE, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(str(e))
            return Response(settings.local_settings.UNDEFINE_ERROR_RESPONSE,
                            content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

class downloadImg(APIView):
    # authentication_classes = (authentication.JSONWebTokenAuthentication, )
    # permission_classes = (permissions.IsAuthenticated, )

    def get(self, request):
        logger.debug("Load download API")
        logger.debug("Data from Odoo server: " + str(request.GET))
        file_path = settings.MEDIA_ROOT + request.GET['img']
        if os.path.isfile(file_path):
            return sendfile(request, file_path)
        return Response({"error_code": "1004", "error_desc": "Image not found!"}, status=status.HTTP_400_BAD_REQUEST)


class callbackMerchant(APIView):
    def get(self, request):
        logger.debug("Load download API")
        logger.debug("Data from Odoo server: " + str(request.GET))

        serializer = callbackMerchantSerializer(data=request.GET)
        serializer.is_valid(raise_exception=True)

        requestID = request.GET['requestID']
        result = request.GET['result']
        customerID = request.GET['customerID']
        merchantToken = request.GET['merchantToken']

        try:
            merchant = Merchant.objects.get(merchantToken=merchantToken)
            callbackURL = merchant.callbackUrl
            callbackMer.delay(url=callbackURL, result=result, customerId=customerID, requestID=requestID)
            logger.debug("callbackMerchant API -- Callback Merchant Info: {0} - {1} - {2}".format(callbackURL, result,
                                                                                                  customerID))
        except Exception as e:
            logger.error(str(e))
            return Response(settings.local_settings.UNDEFINE_ERROR_RESPONSE, status=status.HTTP_400_BAD_REQUEST)

        return Response(settings.local_settings.SUCCESS_RESPONSE, status=status.HTTP_200_OK)
