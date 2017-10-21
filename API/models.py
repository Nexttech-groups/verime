from django.db import models
from django.conf import settings
from rest_framework.authtoken.models import Token
from uuid import uuid4
import os
from django.contrib.auth.models import User
import logging

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def uploadPath(instance, filename):
    ext = filename.split(".")[-1]
    mediaPath = os.path.join(BASE_DIR, 'media')
    randName = uuid4().hex
    while True:
        if os.path.isfile(os.path.join(mediaPath, randName + '.' + ext)):
            randName = uuid4().hex
            continue
        break
    return "{}/{}.{}".format(mediaPath, randName, ext)


class Merchant(models.Model):
    user = models.OneToOneField(User)
    typeApprove = models.PositiveIntegerField(default=0, null=True)
    merchantToken = models.CharField(max_length=100, null=True)
    callbackUrl = models.CharField(max_length=100, null=True)
    costCounter = models.PositiveIntegerField(default=0, null=True)
    merchantKey = models.CharField(default='4bd1a868ed1c4269b62f9ebdb6a691e5', max_length=100, null=True)
    confidenceThreshold = models.FloatField(default=0)


class Upload(models.Model):
    owner = models.ForeignKey(User)
    profileId = models.CharField(max_length=100, null=True)
    userID = models.CharField(max_length=100, null=True)
    passwd = models.CharField(max_length=100, null=True)
    requestID = models.CharField(max_length=100, null=True)
    requestID_expire = models.PositiveIntegerField(null=True, default=0)
    fullName = models.CharField(max_length=100, null=True, default='')
    idNumber = models.CharField(max_length=100, null=True, default='')
    issused = models.CharField(max_length=100, null=True, default='')
    issPlace = models.CharField(max_length=100, null=True, default='')
    GPS = models.CharField(max_length=100, null=True)
    phoneBook = models.TextField(null=True)
    callLog = models.TextField(null=True)
    clientSensor = models.CharField(max_length=100, null=True)
    completeTime = models.PositiveIntegerField(null=True, default=0)
    frontPassportUploadFile = models.ImageField(upload_to=uploadPath, null=True)
    backPassportUploadFile = models.ImageField(upload_to=uploadPath, null=True)
    selfieUploadFile = models.ImageField(upload_to=uploadPath, null=True)
    verifyResultFromMS = models.CharField(max_length=100, null=True)
    verifyAfterFilter = models.PositiveIntegerField(null=True)
    actionScript = models.CharField(max_length=100, null=True)
    actionVid = models.FileField(upload_to=uploadPath, null=True)
    actionResult = models.PositiveSmallIntegerField(null=True)
    actionReport = models.TextField(
        default="{'actionOrderMatch': 100, 'actionCodeMatch':100, 'score': 0, 'diff': 0}", null=True)
    merchantData = models.CharField(max_length=100, null=True)
