import cv2
import numpy as np


def SSIM(img1, img2):
    im1 = cv2.imread(img1)
    im2 = cv2.imread(img2)
    sigma2x = np.var(im1)
    sigma2y = np.var(im2)
    ux = np.mean(im1)
    uy = np.mean(im2)
    sigmaxy = np.mean((im1 - ux) * (im2 - uy))
    # i2 = im2 + 200

    k1 = 0.01
    k2 = 0.03
    L = 255
    c1 = (k1*L)**2
    c2 = (k2*L)**2
    c3 = c2/2

    l = (2*ux*uy+c1)/(ux*ux+uy*uy+c1)
    c = (2*(sigma2x**0.5)*(sigma2y**0.5)+c2)/(sigma2x+sigma2y+c2)
    s = (sigmaxy+c3)/((sigma2x**0.5)*(sigma2y**0.5)+c3)

    re = l*c*s
    return re


def PSNR(im1, im2):
    img1 = cv2.imread(im1)
    img2 = cv2.imread(im2)
    k = 8
    fmax = 2**k - 1
    a = fmax**2
    e = img1 - img2
    m, n, x = img1.shape
    b = np.sum(e**2)
    if b == 0:
        return -1
    re = 10*np.log10(m*n*a/b)
    return re


def main():
    PSNR("1.png", "2.png")

if __name__ == "__main__":
    main()
