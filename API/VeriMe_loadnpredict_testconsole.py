import tensorflow as tf
import numpy as np
import cv2
import sys
sys.path.append('/var/www/html/VeriMe/DataHelper')
import imutils
from PIL import Image
sys.path.append('/var/www/html/VeriMe/API')
from VeriMe_model import CNN_model
#import VeriMe.API.VeriMe_loadData as loadData
import os
import time
#sys.path.insert(0, '/var/www/html/VeriMe/VeriMe/')
sys.path.append('/var/www/html/VeriMe/VeriMe/')
from celeryconf import app

faceCascadePath = "/var/www/html/VeriMe/DataHelper/face.xml"
eyeCascadePath = "/var/www/html/VeriMe/DataHelper/eyes.xml"

faceCascade = cv2.CascadeClassifier(faceCascadePath)
eyeCascade = cv2.CascadeClassifier(eyeCascadePath)

WIDTH = 72
HEIGHT = 16

size = WIDTH, HEIGHT
mouthResult = []

@app.task(bind=True)
def predict_SVM(self, counter, mouthRoi):
    print("lol")
    #global mouthResult
    #svm = cv2.ml.SVM_load("smile_open.xml")
    #mouthRoi = cv2.resize(mouthRoi, (28, 28))
    #mouthRoi = np.array(mouthRoi, dtype='float32')
    #mouthRoi = mouthRoi.reshape(1, 28*28)
    #mouthResult.append((counter, svm.predict(mouthRoi)[1][0][0]))

def loadModel():
    cnn = CNN_model(feature_size=size[0] * size[1],
                    num_classes=4,
                    image_width=size[0],
                    image_height=size[1])
    return cnn


def make_image_data(img):

    # resized = img.resize(size, Image.ANTIALIAS) # resize image
    # grey = resized.convert('L') # convert the image to *greyscale*
    # im_array = np.array(grey) # convert to np array
    # oned_array = im_array.reshape(1, size[0] * size[1])
    resized = cv2.resize(img, (WIDTH, HEIGHT))
    oned_array = np.array(resized).reshape(1, size[0]*size[1])
    return oned_array

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
#        print(str(vid))
        kq = []
        try:
            counter = 0
            while(vid.isOpened()):
                counter += 1
 
                if counter % 2 == 0:
                    continue
                print(counter)
                grabbed, frame = vid.read()
                if not grabbed:
                    break
                #if frame.shape[1] > 600:
                frame = imutils.resize(frame, width=600)
                
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                #print("fuck2")
                faceRects = faceCascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=2, minSize=(100, 100),
                     flags=cv2.CASCADE_FIND_BIGGEST_OBJECT)
                print(faceRects)
                if len(faceRects) != 1:
                    continue
               
                faceROI = gray[faceRects[0][1]:faceRects[0][1] + faceRects[0][3], faceRects[0][0]:faceRects[0][0] + faceRects[0][2]]
                
                # detect eyes in the face ROI
                eyeRects = eyeCascade.detectMultiScale(faceROI, scaleFactor=1.1, minNeighbors=2, minSize=(20, 20),
                   flags=cv2.CASCADE_FIND_BIGGEST_OBJECT)
                
                if len(eyeRects) != 1:
                    continue
                print("fuck4")
                eyeROI = faceROI[eyeRects[0][1]:eyeRects[0][1] + eyeRects[0][3], eyeRects[0][0]:eyeRects[0][0] + eyeRects[0][2]]
                
                mouthROI = faceROI[eyeRects[0][1] + eyeRects[0][3]:faceROI.shape[0], eyeRects[0][0]:eyeRects[0][0] + eyeRects[0][2]]
                print(eyeRects)
                #predict_SVM.delay(counter, mouthROI)
                print("fuck5")
                image_to_predict = make_image_data(eyeROI)
                feed_dict = {
                                self.cnn.x: image_to_predict
                            }
                res = self.sess.run(self.cnn.y, feed_dict)
                predict_label = tf.argmax(res, 1).eval(session=self.sess)
                kq.append((counter, predict_label[0]))
                
        except Exception as e:
            print(str(e))
        print(round(time.time() - start, 2))
        vid.release()
        #print(kq + mouthResult)
        return kq
