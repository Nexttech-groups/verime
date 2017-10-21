import cv2
import DataHelper.imutils as imutils
from PIL import Image
import numpy as np
import os

WIDTH, HEIGHT = 28, 28  # all mouth images will be resized to the same size
dim = WIDTH * HEIGHT  # dimension of feature vector

faceCascadePath = "/Users/pro/tensorflow/DataHelper/face.xml"
eyeCascadePath = "/Users/pro/tensorflow/DataHelper/eyes.xml"

faceCascade = cv2.CascadeClassifier(faceCascadePath)
eyeCascade = cv2.CascadeClassifier(eyeCascadePath)

def vectorize(filename):
    size = WIDTH, HEIGHT  # (width, height)
    im = Image.open(filename)
    resized_im = im.resize(size, Image.ANTIALIAS)  # resize image
    im_grey = resized_im.convert('L')  # convert the image to *greyscale*
    im_array = np.array(im_grey)  # convert to np array
    oned_array = im_array.reshape(1, size[0] * size[1])
    return oned_array

def cameraTest():

    svm = cv2.ml.SVM_load("smile_open.xml")

    camera = cv2.VideoCapture(0)
    while True:
        # grab the current frame
        (grabbed, frame) = camera.read()
        if not grabbed:
            continue
        frame = imutils.resize(frame, width=600)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faceRects = faceCascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=2, minSize=(100, 100),
                                                 flags=cv2.CASCADE_FIND_BIGGEST_OBJECT)
        if len(faceRects) != 1:
            continue

        # loop over the face bounding boxes
        for (fX, fY, fW, fH) in faceRects:
            # extract the face ROI and update the list of
            # bounding boxes

            faceROI = gray[fY:fY + fH, fX:fX + fW]

            # detect eyes in the face ROI
            eyeRects = eyeCascade.detectMultiScale(faceROI, scaleFactor=1.1, minNeighbors=2, minSize=(20, 20),
                                                   flags=cv2.CASCADE_FIND_BIGGEST_OBJECT)
            if len(eyeRects) != 1:
                continue
            # loop over the eye bounding boxes
            for (eX, eY, eW, eH) in eyeRects:
                mouthRoi = faceROI[eY + eH:faceROI.shape[0], eX:eX + eW]
                mouthRoi = cv2.resize(mouthRoi, (28, 28))
                mouthRoi = np.array(mouthRoi, dtype='float32')
                mouthRoi = mouthRoi.reshape(1, 28*28)
                print(svm.predict(mouthRoi))
                # cv2.imshow('xxxxx', eyeROI)
                # if cv2.waitKey(1) & 0xFF == ord("q"):
                #     break
    # cleanup the camera and close any open windows
    camera.release()
    cv2.destroyAllWindows()

cameraTest()
