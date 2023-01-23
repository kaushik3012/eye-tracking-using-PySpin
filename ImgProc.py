import cv2
import numpy as np

def scaleDown(n, maxVal):
    n = -10 + n * (20/maxVal)
    return n

def detect_pupil(img):
    rows, cols = img.shape
    img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    inv = cv2.bitwise_not(img)
    thresh = cv2.cvtColor(inv, cv2.COLOR_BGR2GRAY)
    kernel = np.ones((2,2),np.uint8)
    erosion = cv2.erode(thresh,kernel,iterations = 1)
    ret,thresh1 = cv2.threshold(erosion,220,255,cv2.THRESH_BINARY)
    cnts, hierarchy = cv2.findContours(thresh1, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    center = (scaleDown(cols/2, cols), scaleDown(rows/2, rows))
    radius = 0
    if len(cnts) != 0:
        c = max(cnts, key = cv2.contourArea)
        (x,y),radius = cv2.minEnclosingCircle(c)
        center = (int(x),int(y))
        radius = int(radius)
        cv2.circle(img,center,radius,(255,0,0),2)
        cv2.line(img, (center[0], 0), (center[0], rows), (0, 255, 0), 2)
        cv2.line(img, (0, center[1]), (cols, center[1]), (0, 255, 0), 2)
    cl = (int((cols/2) - 5), int(rows/2))
    cr = (int((cols/2) + 5), int(rows/2))
    ct = (int(cols/2), int((rows/2) - 5))
    cb = (int(cols/2), int((rows/2) +5))
    cv2.line(img, cl, cr, (169,169,169), 2)
    cv2.line(img, ct, cb, (169,169,169), 2)
    return (scaleDown(center[0],cols),scaleDown(center[1],rows),img, radius)

def detect_pupil2(img):
    img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    roi = img
    rows, cols, _ = roi.shape
    gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    gray_roi = cv2.GaussianBlur(gray_roi, (7,7), 0)

    _, threshold = cv2.threshold(gray_roi, 35, 255, cv2.THRESH_BINARY_INV)
    contours,_  = cv2.findContours(threshold, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=lambda x: cv2.contourArea(x), reverse=True)
    x=cols/2
    y=rows/2
    w=0
    h=0
    for cnt in contours:
        (x, y, w, h) = cv2.boundingRect(cnt)
        k=[]
        #cv2.drawContours(roi, [cnt], -1, (0, 0, 255), 3)
        cv2.rectangle(roi, (x, y), (x + w, y + h), (255, 0, 0), 2)
        cv2.line(roi, (x + int(w/2), 0), (x + int(w/2), rows), (0, 255, 0), 2)
        cv2.line(roi, (0, y + int(h/2)), (cols, y + int(h/2)), (0, 255, 0), 2)
        # print(x,y)
        break

    #cv2.imshow("Threshold", threshold)
    #cv2.imshow("gray roi", gray_roi)
    return (scaleDown(x + int(w/2), cols),scaleDown(y + int(h/2),rows),roi, gray_roi)