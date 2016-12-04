import cv2


def c2b(src):
    try:
        im = cv2.imread(src)
        im = cv2.cvtColor(im, cv2.COLOR_RGB2GRAY)
        return im
    except Exception:
        return None
