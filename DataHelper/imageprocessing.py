import DataHelper.imutils as imutils
import cv2
import os
import random
import numpy as np
import time

faceCascadePath = "/Users/pro/tensorflow/DataHelper/face.xml"
eyeCascadePath = "/Users/pro/tensorflow/DataHelper/eyes.xml"

faceCascade = cv2.CascadeClassifier(faceCascadePath)
eyeCascade = cv2.CascadeClassifier(eyeCascadePath)


def extractEye(imgPath, savePath):

    for fname in os.listdir(imgPath):
        if fname.split('.')[-1] not in ["jpg", "png", "jpeg", "JPG", "PNG", "JPEG"]:
            continue
        image = cv2.imread(os.path.join(imgPath, fname))
        image = imutils.resize(image, width=600)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # detect faces in the image and initialize the list of
        # rectangles containing the faces and eyes
        faceRects = faceCascade.detectMultiScale(image, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100),
                                                 flags=cv2.CASCADE_FIND_BIGGEST_OBJECT)
        if len(faceRects) != 1:
            continue

        # loop over the face bounding boxes
        for (fX, fY, fW, fH) in faceRects:
            # extract the face ROI and update the list of
            # bounding boxes
            faceROI = image[fY:fY + fH, fX:fX + fW]

            # detect eyes in the face ROI
            eyeRects = eyeCascade.detectMultiScale(faceROI, scaleFactor=1.1, minNeighbors=0, minSize=(20, 20),
                                                   flags=cv2.CASCADE_FIND_BIGGEST_OBJECT)
            if len(eyeRects) != 1:
                continue
            # loop over the eye bounding boxes
            for (eX, eY, eW, eH) in eyeRects:
                eyeROI = faceROI[eY:eY+eH, eX:eX+eW]
                cv2.imwrite(os.path.join(savePath, fname), eyeROI)
                time.sleep(0.25)

def imgprocessing(imgPath, savePath):
    imgls = os.listdir(imgPath)
    for fname in imgls:
        if fname.split('.')[-1] not in ["jpg", "png", "jpeg", "JPG", "PNG", "JPEG"]:
            continue
        img = cv2.imread(os.path.join(imgPath, fname))
        img_name = fname.split('.')[0]
        rotated_5deg = imutils.rotate(image=img, angle=5)
        cv2.imwrite(os.path.join(savePath, str(img_name) + "_rotated_5deg" + ".jpg"), rotated_5deg)
        rotated_10deg = imutils.rotate(image=img, angle=10)
        cv2.imwrite(os.path.join(savePath, str(img_name) + "_rotated_10deg" + ".jpg"), rotated_10deg)
        rotated_minus5deg = imutils.rotate(image=img, angle=-5)
        cv2.imwrite(os.path.join(savePath, str(img_name) + "_rotated_minus5deg" + ".jpg"), rotated_minus5deg)
        rotated_minus10deg = imutils.rotate(image=img, angle=-10)
        cv2.imwrite(os.path.join(savePath, str(img_name) + "_rotated_minus10deg" + ".jpg"), rotated_minus10deg)
        time.sleep(0.5)

def cameraTest():
    camera = cv2.VideoCapture(0)
    while True:
        # grab the current frame
        (grabbed, frame) = camera.read()
        if not grabbed:
            continue
        frame = imutils.resize(frame, width=600)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faceRects = faceCascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=2, minSize=(20, 20),
                                                 flags=cv2.CASCADE_FIND_BIGGEST_OBJECT)
        if len(faceRects) != 1:
            continue

        # loop over the face bounding boxes
        for (fX, fY, fW, fH) in faceRects:
            # extract the face ROI and update the list of
            # bounding boxes

            faceROI = gray[fY:fY + fH, fX:fX + fW]

            # detect eyes in the face ROI
            eyeRects = eyeCascade.detectMultiScale(faceROI, scaleFactor=1.1, minNeighbors=2, minSize=(4, 4),
                                                   flags=cv2.CASCADE_FIND_BIGGEST_OBJECT)
            if len(eyeRects) != 1:
                continue
            # loop over the eye bounding boxes
            for (eX, eY, eW, eH) in eyeRects:
                eyeROI = faceROI[eY:eY + eH, eX:eX + eW]
                cv2.imshow('xxxxx', eyeROI)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
    # cleanup the camera and close any open windows
    camera.release()
    cv2.destroyAllWindows()


def adjust_gamma(image, gamma=1.0):
    # build a lookup table mapping the pixel values [0, 255] to
    # their adjusted gamma values
    invGamma = 1.0 / gamma
    table = np.array([((i / 255.0) ** invGamma) * 255
                      for i in np.arange(0, 256)]).astype("uint8")

    # apply gamma correction using the lookup table
    return cv2.LUT(image, table)

if __name__=="__main__":

    # ("/Users/pro/Desktop/openIOS", "/Users/pro/tensorflow/data/CNN/open"),
    # ("/Users/pro/Desktop/closeIOS", "/Users/pro/tensorflow/data/CNN/close"),

    imgForExtractPaths = [
                          ("/Users/pro/Desktop/leftIOS", "/Users/pro/tensorflow/data/CNN/left"),
                          ("/Users/pro/Desktop/rightIOS", "/Users/pro/tensorflow/data/CNN/right"),
                          ]

    imgForProccessPaths = [("/Users/pro/Desktop/closeIOS", "/Users/pro/Desktop/closeIOS"),
                           ("/Users/pro/Desktop/leftIOS", "/Users/pro/Desktop/leftIOS"),
                           ("/Users/pro/Desktop/rightIOS", "/Users/pro/Desktop/rightIOS"),
                           ("/Users/pro/Desktop/openIOS", "/Users/pro/Desktop/openIOS")]

    # for path in imgForProccessPaths:

        # imgprocessing(imgPath=path[0], savePath=path[1])

        # imgls = os.listdir(path[0])
        # for fname in imgls:
        #     if fname.split('.')[-1] not in ["jpg", "png", "jpeg", "JPG", "PNG", "JPEG"]:
        #         continue
        #     img_name = fname.split('.')[0]
        #     img = cv2.imread(os.path.join(path[0], fname))
        #     darker = adjust_gamma(img, gamma=0.8)
        #     cv2.imwrite(os.path.join(path[0], str(img_name) + "_darker" + ".jpg"), darker)
        #     brighter = adjust_gamma(img, gamma=1.3)
        #     cv2.imwrite(os.path.join(path[0], str(img_name) + "_brighter" + ".jpg"), brighter)
        #     time.sleep(0.5)


    # for path in imgForExtractPaths:
    #     extractEye(imgPath=path[0], savePath=path[1])

    # FLIP IMAGEs
    # flipPaths = ["/Users/pro/tensorflow/data/CNN/left", "/Users/pro/tensorflow/data/CNN/right"]
    # leftImgs = os.listdir(flipPaths[0])
    # rightImgs = os.listdir(flipPaths[1])
    #
    # for imgName in leftImgs:
    #     img = cv2.imread(os.path.join(flipPaths[0], imgName))
    #     fliped = cv2.flip(img, 1)
    #     cv2.imwrite(os.path.join(flipPaths[1], 'flip_' + imgName.split('.')[0]+'.jpg'), fliped)
    #     time.sleep(0.25)
    #
    # for imgName in rightImgs:
    #     img = cv2.imread(os.path.join(flipPaths[1], imgName))
    #     fliped = cv2.flip(img, 1)
    #     cv2.imwrite(os.path.join(flipPaths[0], 'flip_' + imgName.split('.')[0]+'.jpg'), fliped)
    #     time.sleep(0.25)

    imgPaths = ["/Users/pro/tensorflow/data/CNN/open",
                "/Users/pro/tensorflow/data/CNN/left",
                "/Users/pro/tensorflow/data/CNN/right",
                "/Users/pro/tensorflow/data/CNN/close"]
    ls = []
    for path in imgPaths:
        for fname in os.listdir(path):
            img = cv2.imread(os.path.join(path, fname))
            ls.append(round(img.shape[1]/img.shape[0], 2))

    print(np.mean(ls))