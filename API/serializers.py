from rest_framework import serializers
from .models import Upload
import logging
import time
import sys
from .callOdooServer import getMerchantInfo, uploadProfile
sys.path.append('/var/www/html/VeriMe/VeriMe')
import local_settings
import re
from rest_framework import HTTP_HEADER_ENCODING, exceptions
from .models import Merchant
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
import ast
from .tasks import checkAction

logger = logging.getLogger(__name__)


def checkRequestIDExpire(value):

    if not Upload.objects.filter(requestID=value).exists():
        raise exceptions.NotFound(local_settings.REQUESTID_NOTFOUND_RESPONSE)

    upload = Upload.objects.get(requestID=value)
    if int(round(time.time(), 0)) > int(upload.requestID_expire) + 1:
        raise exceptions.ParseError(local_settings.REQUESTID_EXPRIE_RESPONSE)
    return value

class receiveMerchantInfoFromBackendSerializer(serializers.Serializer):
    merchantToken = serializers.CharField(max_length=100)
    merchantId = serializers.CharField(max_length=100)
    typeApprove = serializers.IntegerField(max_value=1, min_value=0)
    confidenceThreshold = serializers.FloatField(max_value=1.0, min_value=0.0)
    callbackUrl = serializers.CharField(max_length=100, required=False)
    # merchantKey = serializers.CharField(default='4bd1a868ed1c4269b62f9ebdb6a691e5', max_length=100)

    def create(self, validated_data):
        merchantId = validated_data.get('merchantId')
        merchantToken = validated_data.get('merchantToken')

        validated_data.pop('merchantId')
        user, created = User.objects.get_or_create(username=merchantId)
        if not created:
            Token.objects.filter(user=user).update(key=merchantToken)
            Merchant.objects.filter(user=user).update(**validated_data)
            return 'Merchant updated!'

        validated_data['user'] = user
        Token.objects.create(user=user, key=merchantToken)
        Merchant.objects.create(**validated_data)
        return 'Merchant created!'


class getScriptSerializer(serializers.Serializer):
    merchantToken = serializers.CharField(max_length=100)
    merchantId = serializers.CharField(max_length=100)
    userID = serializers.CharField(max_length=50)
    numOfActions = serializers.IntegerField(max_value=3, min_value=1)
    merchantData = serializers.CharField(max_length=100)

    # def validate(self, data):
    #
    #     KYC_Token = ''
    #     if str(data['merchantToken']) != KYC_Token and Upload.objects.filter(userID=data['userID']).exists():
    #         raise exceptions.ParseError({"error_code": "004", "error_desc": "userID existed!"})
    #     return data

class passportUploadSerializer(serializers.Serializer):
    # merchantToken = serializers.CharField(max_length=100)
    requestID = serializers.CharField(max_length=100, validators=[checkRequestIDExpire])
    side = serializers.CharField(max_length=10)
    passportImg = serializers.ImageField()

    def validate(self, data):
        upload = Upload.objects.get(requestID=data['requestID'])
        if str(upload.owner) != str(self.context['request'].user):
            raise exceptions.PermissionDenied(
                {"error_code": "017", "error_desc": "This requestID does not belong your merchant!"})

        if data['side'] not in ['front', 'back']:
            raise exceptions.ParseError({"error_code": "005", "error_desc": "Wrong 'side' parameter!"})

        merchantToken = Token.objects.get(user=upload.owner).key
        data['merchantToken'] = merchantToken

        return data

    def save(self, **kwargs):
        requestID = self.validated_data['requestID']
        side = self.validated_data['side']
        passportImg = self.validated_data['passportImg']
        upload = Upload.objects.get(requestID=requestID)

        if side == 'front':
            upload.frontPassportUploadFile = passportImg
            upload.save(update_fields=['frontPassportUploadFile'])
            frontPassportURL = str(upload.frontPassportUploadFile.name).split('/')[-1]
            uploadProfile.delay(requestID=requestID, merchantToken=self.validated_data['merchantToken'],
                                customerId=upload.userID, frontPassportURL=frontPassportURL)

        elif side == 'back':
            upload.backPassportUploadFile = passportImg
            upload.save(update_fields=['backPassportUploadFile'])
            backPassportURL = str(upload.backPassportUploadFile.name).split('/')[-1]
            uploadProfile.delay(requestID=requestID, merchantToken=self.validated_data['merchantToken'],
                                customerId=upload.userID, backPassportURL=backPassportURL)


class actionUploadSerializer(serializers.Serializer):
    # merchantToken = serializers.CharField(max_length=100)
    requestID = serializers.CharField(max_length=100, validators=[checkRequestIDExpire])
    actionCode = serializers.CharField(max_length=10)
    actionVid = serializers.FileField()

    def validate(self, data):

        upload = Upload.objects.get(requestID=data['requestID'])
        actionScript = upload.actionScript

        if str(upload.owner) != str(self.context['request'].user):
            raise exceptions.PermissionDenied(
                {"error_code": "017", "error_desc": "This requestID does not belong your merchant!"})

        if actionScript != str(data['actionCode']):
            raise exceptions.ParseError({"error_code": "011", "error_desc": "Action code not match!"})

        return data


class selfieUploadSerializer(serializers.Serializer):
    # merchantToken = serializers.CharField(max_length=100)
    requestID = serializers.CharField(max_length=100, validators=[checkRequestIDExpire])
    selfieImg = serializers.ImageField()

    def validate_requestID(self, value):
        upload = Upload.objects.get(requestID=value)
        if str(upload.owner) != str(self.context['request'].user):
            raise exceptions.PermissionDenied(
                {"error_code": "017", "error_desc": "This requestID does not belong your merchant!"})
        return value

    def update(self, instance, validated_data):
        # merchantToken = self.validated_data.get('merchantToken')
        requestID = validated_data.get('requestID')
        selfieImg = validated_data.get('selfieImg')

        # upload = Upload.objects.get(requestID=requestID)
        merchantToken = Token.objects.get(user=instance.owner).key
        instance.selfieUploadFile = selfieImg
        instance.save()

        selfieURL = str(instance.selfieUploadFile.name).split('/')[-1]
        uploadProfile.delay(requestID=requestID, merchantToken=merchantToken,
                            customerId=instance.userID, selfieURL=selfieURL)

        return instance


class submitInfoSerializer(serializers.Serializer):
    # merchantToken = serializers.CharField(max_length=100)
    requestID = serializers.CharField(max_length=100, validators=[checkRequestIDExpire])
    fullName = serializers.CharField(max_length=100, allow_blank=True)
    idNumber = serializers.CharField(max_length=20, allow_blank=True)
    issused = serializers.CharField(max_length=100, allow_blank=True)
    issPlace = serializers.CharField(max_length=100, allow_blank=True)
    phoneBook = serializers.CharField(allow_blank=True)
    callLog = serializers.CharField(allow_blank=True)
    GPS = serializers.CharField(max_length=100, allow_blank=True)

    def validate_requestID(self, value):
        upload = Upload.objects.get(requestID=value)
        if str(upload.owner) != str(self.context['request'].user):
            raise exceptions.PermissionDenied(
                {"error_code": "017", "error_desc": "This requestID does not belong your merchant!"})
        return value

    # def save(self, **kwargs):



class callbackMerchantSerializer(serializers.Serializer):
    result = serializers.IntegerField(max_value=1, min_value=0)
    customerID = serializers.CharField(max_length=50)
    merchantToken = serializers.CharField(max_length=100)
