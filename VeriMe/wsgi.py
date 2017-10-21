"""
WSGI config for VeriMe project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/howto/deployment/wsgi/
"""
'''
from io import StringIO
import os, sys 
import django.core.handlers.wsgi
import logging

class Wrapper: 

    def __init__(self, application): 
        self.__application = application 

    def __call__(self, environ, start_response): 
        if environ.get('CONTENT_ENCODING', '') == 'gzip': 
            #buffer = cStringIO.StringIO() 
            buffer = StringIO.StringIO() 
            input = environ['wsgi.input'] 
            blksize = 8192 
            length = 0 
            return self.__application(environ, start_response)
            data = input.read(blksize) 
            buffer.write(data) 
            length += len(data) 

            while data: 
                data = input.read(blksize) 
                buffer.write(data) 
                length += len(data) 

            buffer = StringIO.StringIO(buffer.getvalue()) 

            environ['wsgi.input'] = buffer 
            environ['CONTENT_LENGTH'] = length 

        return self.__application(environ, start_response) 

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "VeriMe.settings")
sys.path.append('/var/www/html/VeriMe/VeriMe')
sys.path.append('/var/www/html/VeriMe')

application = Wrapper(django.core.handlers.wsgi.WSGIHandler())

'''


import os, sys
from io import StringIO
from django.core.wsgi import get_wsgi_application
#import site

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "VeriMe.settings")
sys.path.append('/var/www/html/VeriMe/VeriMe')
sys.path.append('/var/www/html/VeriMe')


django_application = get_wsgi_application()

def application(environ, start_response):
    print( environ.get('CONTENT_LENGTH')) 
    #print(str(environ))
    try:
        if environ.get("mod_wsgi.input_chunked") == "1":
            stream = environ["wsgi.input"]
            data = stream.read()
            print(type(data))  
            environ["CONTENT_LENGTH"] = str(len(data))
            environ["wsgi.input"] = StringIO.StringIO(data)

        return django_application(environ, start_response)
    except Exception as e:
        return str(e)

'''
import pprint

class LoggingMiddleware:

    def __init__(self, application):
        self.__application = application

    def __call__(self, environ, start_response):
        errors = environ['wsgi.errors']
        pprint.pprint(('REQUEST', environ), stream=errors)

        def _start_response(status, headers, *args):
            pprint.pprint(('RESPONSE', status, headers), stream=errors)
            return start_response(status, headers, *args)

        return self.__application(environ, _start_response)

application = LoggingMiddleware(application)
'''
