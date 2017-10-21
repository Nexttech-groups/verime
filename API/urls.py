from django.conf.urls import include, url
from django.contrib import admin
from .views import passportUpload, selfieUpload, downloadImg, getScript, actionUpload, submitInfo, callbackMerchant, \
receiveMerchantInfoFromBackend

admin.autodiscover()

urlpatterns = [
    url(r'^upload/passport$', passportUpload.as_view()),
    url(r'^upload/actionVid$', actionUpload.as_view()),
    url(r'^upload/selfie$', selfieUpload.as_view()),
    url(r'^submit$', submitInfo.as_view()),
    #url(r'^checkemail', checkEmail.as_view()),
    #url(r'^download/passport$', downloadImg.as_view()),
    #url(r'^download/selfie$', downloadImg.as_view()),
    url(r'^getscript$', getScript.as_view()),
    url(r'^$', downloadImg.as_view()),
    url(r'^callback/$', callbackMerchant.as_view()),
    url(r'^update/merchant_info$', receiveMerchantInfoFromBackend.as_view()),
]
