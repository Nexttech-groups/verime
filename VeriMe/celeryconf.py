from __future__ import absolute_import
import os
from celery import Celery

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VeriMe.settings')
#os.environ.setdefault('C_FORCE_ROOT', 'true')
from django.conf import settings  # noqa

app = Celery('VeriMe', backend='redis://localhost:6379', broker='redis://localhost:6379')
app.conf.update(CELERY_ACCEPT_CONTENT = ['json', 'pickle'])
#app.conf.update(CELERY_RESULT_SERIALIZER = 'json', 'pickle')
# app = Celery('VeriMe', backend='amqp://', broker='amqp')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
CELERY_IMPORTS=["callbackMerchant"]


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
