# coding=utf-8
import cv2
import datetime
import threading
import numpy
import time
from multiprocessing import Process
from multiprocessing import Array
import cPickle
import tempfile
import os

#计算某点的自适应加权滤波均值
def weighted_mean(img, p):
    w = 1
    wmax = 39
    while w < wmax:
        x = 0 if p[0] < w else p[0] - w
        y = 0 if p[1] < w else p[1] - w
        arr = []
        while x <= p[0] + w:
            if x >= img.shape[0]:
                break
            while y <= p[1]+w:
                if y >= img.shape[1]:
                    break
                arr.append(img[x][y])
                y += 1
            y = 0 if p[1] < w else p[1] - w
            x += 1
        arr = sorted(arr)
        smin = arr[0]
        smax = arr[-1]
        arr1 = []
        x = 0 if p[0] <= w else p[0] - w - 1
        y = 0 if p[1] <= w else p[1] - w - 1
        while x <= p[0] + w + 1:
            if x >= img.shape[0]:
                break
            while y <= p[1] + w + 1:
                if y >= img.shape[1]:
                    break
                arr1.append(img[x][y])
                y += 1
            y = 0 if p[1] <= w else p[1] - w - 1
            x += 1
        arr1 = sorted(arr1)
        smin1 = arr1[0]
        smax1 = arr1[-1]
        if smin == smin1 and smax == smax1:
            if img[p[0]][p[1]] == smin or img[p[0]][p[1]] == smax:
                nonn = [i for i in arr if i != smin and i != smax]
                sa = len(nonn)
                if sa == 0:
                    w += 1
                else:
                    sum = 0
                    for s in nonn:
                        sum += s
                    ret = round(sum/sa)
                    return ret
            else:
                # print img[p[0]][p[1]], arr, "(", p[0], p[1], ")"
                return img[p[0]][p[1]]
        else:
            w += 1
    return img[p[0]][p[1]]

def awmf(fromurl):
    imb = cv2.imread(fromurl, flags=cv2.IMREAD_GRAYSCALE)
    bs = imb.shape
    i = 1; j = 1
    while i < bs[0] - 1:
        while j < bs[1] - 1:
            imb[i][j] = weighted_mean(imb, (i,j))
            j += 1
        i += 1
        j = 1
    time.sleep(3)
    return imb


class MyProcess(Process):

    def __init__(self, imb, thread, threads):
        Process.__init__(self)

        self.imb = imb
        self.thread = thread
        self.threads = threads

    def run(self):
            thread = self.thread
            threads = self.threads
            imb = self.imb
            bs = imb.shape
            start = 0
            st = time.time()
            i = thread
            j = 1
            while i < bs[0] - 1:
                while j < bs[1] - 1:
                    start += 1
                    imb[i][j] = weighted_mean(imb, (i, j))
                    j += 1
                i += threads
                j = 1
            name = tempfile.gettempprefix()+"tempimg"+str(thread)+".png"
            cv2.imwrite(name, imb)


def mawmf(fromurl, threads):
    imb = cv2.imread(fromurl, flags=cv2.IMREAD_GRAYSCALE)
    arr = []
    bs = imb.shape
    for i in range(0, threads):
        arr.append(MyProcess(imb, i, threads))
        arr[i].start()
    for i in range(0, threads):
        arr[i].join()
        name = tempfile.gettempprefix()+"tempimg"+str(i)+".png"
        imt = cv2.imread(name, cv2.IMREAD_GRAYSCALE)
        os.remove(name)
        it = i
        while it < bs[0] - 1:
            imb[it] = imt[it]
            it += threads
    return imb

#计算某点的自适应中值
def weighted_middle(img, p):
    w = 1
    wmax = 39
    while w < wmax:
        x = 0 if p[0] < w else p[0] - w
        y = 0 if p[1] < w else p[1] - w
        arr = []
        while x <= p[0] + w:
            if x >= img.shape[0]:
                x += 1
                continue
            while y <= p[1]+w:
                if y >= img.shape[1]:
                    y += 1
                    continue
                arr.append(img[x][y])
                y += 1
            y = 0 if p[1] < w else p[1] - w
            x += 1
        arr = sorted(arr)
        smin = arr[0]
        smax = arr[-1]
        arr1 = []
        x = 0 if p[0] <= w else p[0] - w - 1
        y = 0 if p[1] <= w else p[1] - w - 1
        while x <= p[0] + w + 1:
            if x >= img.shape[0]:
                x += 1
                continue
            while y <= p[1] + w + 1:
                if y >= img.shape[1]:
                    y += 1
                    continue
                arr1.append(img[x][y])
                y += 1
            y = 0 if p[1] <= w else p[1] - w - 1
            x += 1
        arr1 = sorted(arr1)
        smin1 = arr1[0]
        smax1 = arr1[-1]
        if smin == smin1 and smax == smax1:
            if img[p[0]][p[1]] == smin or img[p[0]][p[1]] == smax:
                    return arr1[len(arr1)/2]
            else:
                return img[p[0]][p[1]]
        else:
            w += 1
    return img[p[0]][p[1]]

def amf(fromurl):
    imb = cv2.imread(fromurl, flags=cv2.IMREAD_GRAYSCALE)
    bs = imb.shape
    i = 1; j = 1
    while i < bs[0] - 1:
        while j < bs[1] - 1:
            imb[i][j] = weighted_middle(imb, (i, j))
            j += 1
        i += 1
        j = 1
    return imb


def middle(img):
    img = cv2.imread(img, flags=cv2.IMREAD_GRAYSCALE)
    x = img.shape[0]
    y = img.shape[1]
    for i in range(1, x-1):
        for j in range(1, y-1):
            arr = []
            for i1 in range(i-1, i+2):
                for j1 in range(j-1, j+2):
                    arr.append(img[i1][j1])
            arr = sorted(arr)
            middle = arr[4]
            img[i][j] = middle
    return img


def mean(img):
    img = cv2.imread(img, flags=cv2.IMREAD_GRAYSCALE)
    x = img.shape[0]
    y = img.shape[1]
    for i in range(1, x-1):
        for j in range(1, y-1):
            arr = []
            for i1 in range(i-1, i+2):
                for j1 in range(j-1, j+2):
                    arr.append(img[i1][j1])
            s = sum(arr, 0)
            middle = s/len(arr)
            img[i][j] = middle
    return img


if __name__ == "__main__":
    print middle(r"C:\Users\Administrator\Desktop\lena1.png")


