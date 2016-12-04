# coding=utf-8
import random
import cv2


def salt(img, n):
    for k in range(0, n, 1):
        i = int(random.random()*img.shape[0])
        j = int(random.random()*img.shape[1])
        if len(img.shape) == 2:
            img[i][j] = 255
        elif img.shape[2] == 3:
            img[i][j][0] = 255
            img[i][j][1] = 255
            img[i][j][2] = 255


def pepper(img, n):
    for k in range(0, n, 1):
        i = int(random.random()*img.shape[0])
        j = int(random.random()*img.shape[1])
        if len(img.shape) == 2:
            img[i][j] = 0
        elif img.shape[2] == 3:
            img[i][j][0] = 0
            img[i][j][1] = 0
            img[i][j][2] = 0


def addspnoise(img, saltn, peppern):
    im = cv2.imread(img)
    size = im.shape[0]*im.shape[1]/2
    saltn = int((float(saltn)/100)*size)
    peppern = int((float(peppern)/100)*size)
    salt(im, saltn)
    pepper(im, peppern)
    return im
