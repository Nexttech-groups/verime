# README #

VeriMe is a application with two purposes

* Compare two faces and verify that belong a same person or not.
* More important, it help anti-proofing, such as somebody use other people's indentites to do bad things, VeriMe will detect and decline their request. 

### Server set up? ###

* Summary of set up: Django + mod_wsgi + Apache + OpenCV 3

	1. OpenCV 3: follow this instruction http://www.pyimagesearch.com/2015/07/20/install-opencv-3-0-and-python-3-4-on-ubuntu/
	
	2. Apache: 
		
		`sudo apt-get install apache2`
	
		`sudo apt-get install apache2-dev`
	
	3. Mod_wsgi: follow this guide: http://modwsgi.readthedocs.io/en/develop/user-guides/quick-installation-guide.html. Note that fix `apxs` and `python3` directory when run `./configure:`
		
		`./configure --with-apxs=/usr/bin/apxs   --with-python=/usr/bin/python3`
	
	4. Django:
		
			## Install newest pip3 version for python3.
			curl https://bootstrap.pypa.io/get-pip.py | python3
		
			## Install Django 1.10
			pip3 install django==1.10
		
			## Install Django Rest Framework for make API
			pip3 install djangorestframework
		
			## Install djangorestframework-httpsignature for using TokenAuthentication
			pip3 install djangorestframework-httpsignature

* Configuration:

	1. Create httpd.conf in /etc/apache2/ and add this lines:
		
			WSGIScriptAlias / /path/to/mysite.com/mysite/wsgi.py
			WSGIPythonPath /path/to/mysite.com
	
			<Directory /path/to/mysite.com/mysite>
			<Files wsgi.py>
			Require all granted
			</Files>
			</Directory>

		
	2. Add this line into apache2.conf in /etc/apache2:
		
		
			LoadModule wsgi_module /usr/lib/apache2/modules/mod_wsgi.so
			Include httpd.conf

			WSGIPassAuthorization On
			ServerName localhost
	
	
	3. Restart apache:
	
			sudo service apache2 restart
		
* Dependencies:

	1. POSTGRES:
	
			sudo apt-get install postgresql postgresql-contrib
		
		Then create databse for project:
	
			CREATE ROLE verime_dev WITH LOGIN PASSWORD '123456';
			CREATE DATABASE verime;
			GRANT ALL PRIVILEGES ON DATABASE verime TO verime_dev;
		
		
	2. CELERY - REDIS:

			pip3 install celery
			sudo apt-get install redis-server
		
		
	3. MORE DEPENDENCIES:
			
			pip3 install requests
			pip3 install tensorflow==0.12.1
			pip3 install Pillow
			pip3 install redis
			pip3 install psycopg2
			apt-get install libapache2-mod-xsendfile 
			pip3 install django-sendfile
		