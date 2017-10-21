import tensorflow as tf
import numpy as np
import cv2
import sys
sys.path.append("/var/www/html/VeriMe/")
import DataHelper.imutils as imutils
from PIL import Image
sys.path.append("/var/www/html/VeriMe/API")
#from .VeriMe_model import CNN_model
from VeriMe_model import CNN_model
#from tasks import testCe
#import VeriMe.API.VeriMe_loadData as loadData
import os
import time
#sys.path.insert(0, '/var/www/html/VeriMe/VeriMe/')
sys.path.append('/var/www/html/VeriMe/VeriMe/')
from celeryconf import app
from celery.utils.log import get_task_logger
logger = get_task_logger(__name__)

#sys.path.append("/var/www/html/VeriMe/API")
#from tasks import callbackMerchant, sendEmail, checkAction, testCe

faceCascadePath = "/var/www/html/VeriMe/DataHelper/face.xml"
eyeCascadePath = "/var/www/html/VeriMe/DataHelper/eyes.xml"

faceCascade = cv2.CascadeClassifier(faceCascadePath)
eyeCascade = cv2.CascadeClassifier(eyeCascadePath)

WIDTH = 72
HEIGHT = 16

size = WIDTH, HEIGHT
svm = cv2.ml.SVM_load("/var/www/html/VeriMe/API/smile_open.xml")


def make_image_data(img):

    # resized = img.resize(size, Image.ANTIALIAS) # resize image
    # grey = resized.convert('L') # convert the image to *greyscale*
    # im_array = np.array(grey) # convert to np array
    # oned_array = im_array.reshape(1, size[0] * size[1])
    resized = cv2.resize(img, (WIDTH, HEIGHT))
    oned_array = np.array(resized).reshape(1, size[0]*size[1])
    return oned_array


@app.task(bind=True, serializer='pickle')
def predict_SVM(self, counter, mouthRoi):
    mouthRoi = cv2.resize(mouthRoi, (28, 28))
    mouthRoi = np.array(mouthRoi, dtype='float32')
    mouthRoi = mouthRoi.reshape(1, 28*28)
    res = int(svm.predict(mouthRoi)[1][0][0])
    res = 0 if res == 0 else res + 3
    #logger.info("mouth ope: {0}".format(res))
    return res


def loadModel():
    cnn = CNN_model(feature_size=size[0] * size[1],
                    num_classes=4,
                    image_width=size[0],
                    image_height=size[1])
    return cnn


class predict():
    
    def __init__(self):
        self.cnn = loadModel()
        self.sess = tf.Session()
        self.saver = tf.train.Saver()    
        self.saver.restore(self.sess, "/var/www/html/VeriMe/API/ckpt/model-900")
 
    def pre(self, link):
        print("link to vid: "+ link)
        start = time.time()
        vid = cv2.VideoCapture(str(link))
        kq = []
        try:
            counter = 0
            while(vid.isOpened()):
                counter += 1
 
                if counter % 2 == 0:
                    continue
                #print(counter)
                grabbed, frame = vid.read()
                if not grabbed:
                    break
                #if frame.shape[1] > 600:
                frame = imutils.resize(frame, width=600)
                
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                faceRects = faceCascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=2, minSize=(100, 100),
                     flags=cv2.CASCADE_FIND_BIGGEST_OBJECT)
                
                if len(faceRects) != 1:
                    continue
               
                faceROI = gray[faceRects[0][1]:faceRects[0][1] + faceRects[0][3], faceRects[0][0]:faceRects[0][0] + faceRects[0][2]]
                
                # detect eyes in the face ROI
                eyeRects = eyeCascade.detectMultiScale(faceROI, scaleFactor=1.1, minNeighbors=2, minSize=(20, 20),
                   flags=cv2.CASCADE_FIND_BIGGEST_OBJECT)
                
                if len(eyeRects) != 1:
                    continue
                eyeROI = faceROI[eyeRects[0][1]:eyeRects[0][1] + eyeRects[0][3], eyeRects[0][0]:eyeRects[0][0] + eyeRects[0][2]]
                mouthROI = faceROI[eyeRects[0][1] + eyeRects[0][3]:faceROI.shape[0], eyeRects[0][0]:eyeRects[0][0] + eyeRects[0][2]]

                x = predict_SVM.apply_async((counter, mouthROI), serializer='pickle')
                
                image_to_predict = make_image_data(eyeROI)
                feed_dict = {
                                self.cnn.x: image_to_predict
                            }
                res = self.sess.run(self.cnn.y, feed_dict)
                predict_label = tf.argmax(res, 1).eval(session=self.sess)
                if str(x.status) == 'SUCCESS':
                    kq.append((counter, int(x.result)))
                else:
                    continue
                kq.append((counter, predict_label[0]))
                #print(counter, predict_label[0])
        except Exception as e:
            print(str(e))
        logger.info('Time to process: {0}'.format(round(time.time() - start, 2)))
        logger.info('Result: {0}'. format(kq))
        vid.release()
        return kq
