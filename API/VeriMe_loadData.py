import os
import numpy as np
from PIL import Image

WIDTH = 72
HEIGHT = 16
dim = WIDTH*HEIGHT
NUM_CLASSES = 4

def convert_label(origin_labels):
    hot_labels = []
    label_size = NUM_CLASSES
    for label_ in origin_labels:
        hot_label = [0 for _ in range(label_size)]
        hot_label[label_ - 1] = 1
        hot_labels.append(hot_label)
    return hot_labels

def batch_iter(_data, _batch_size, _batch_num):
    data_size = len(_data)
    start_index =  _batch_num * _batch_size
    end_index = min([(_batch_num+1)*_batch_size, data_size])
    batch = _data[start_index:end_index]
    x_, y_ = zip(*batch)
    return list(x_), list(y_)

def vectorize(filename):
    size = WIDTH, HEIGHT # (width, height)
    im = Image.open(filename)
    resized_im = im.resize(size, Image.ANTIALIAS) # resize image
    im_grey = resized_im.convert('L') # convert the image to *greyscale*
    im_array = np.array(im_grey) # convert to np array
    oned_array = im_array.reshape(1, size[0] * size[1])
    return oned_array

def load_data():
    openImgPath = "/Users/pro/tensorflow/data/CNN/open"
    leftImgPath = "/Users/pro/tensorflow/data/CNN/left"
    rightImgPath = "/Users/pro/tensorflow/data/CNN/right"
    closeImgPath = "/Users/pro/tensorflow/data/CNN/close"

    openFiles = os.listdir(openImgPath)
    leftFiles = os.listdir(leftImgPath)
    rightFiles = os.listdir(rightImgPath)
    closeFiles = os.listdir(closeImgPath)

    # N x dim matrix to store the vectorized data (aka feature space)
    eyeData = np.zeros((len(openFiles) + len(leftFiles) + len(rightFiles) + len(closeFiles), dim))
    # 1 x N vector to store binary labels of the data: 1 for smile and 0 for neutral
    labels = []

    for idx, filename in enumerate(openFiles):
        eyeData[idx] = vectorize(os.path.join(openImgPath, filename))
        labels.append(1)

    offset = len(openFiles)
    for idx, filename in enumerate(leftFiles):
        eyeData[idx + offset] = vectorize(os.path.join(leftImgPath, filename))
        labels.append(2)

    offset = len(openFiles) + len(leftFiles)
    for idx, filename in enumerate(rightFiles):
        eyeData[idx + offset] = vectorize(os.path.join(rightImgPath, filename))
        labels.append(3)

    offset = len(openFiles) + len(leftFiles) + len(rightFiles)
    for idx, filename in enumerate(closeFiles):
        eyeData[idx + offset] = vectorize(os.path.join(closeImgPath, filename))
        labels.append(4)

    return eyeData, labels
