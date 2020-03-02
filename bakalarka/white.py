import cv2 as cv
import numpy as np
import random

i = cv.imread('../dataset/klaviatura.png')
# cv.imshow('original', i)
gray = cv.cvtColor(i, cv.COLOR_BGR2GRAY)
cv.imshow('grayscale', gray)

# img = cv.GaussianBlur(gray,(3,3),0)
# cv.imshow('removed noise', img)
img = i
# laplacian = cv.Laplacian(img, 8)
# laplacian = cv.blur(laplacian,(3,3))
#cv.imshow('laplace', laplacian)
ret, thresh = cv.threshold(gray,210,255,cv.THRESH_BINARY_INV)
cv.imshow('thresh', thresh)

kernel = np.ones((9,9),np.uint8)
opening = cv.morphologyEx(thresh,cv.MORPH_OPEN,kernel, iterations = 1)


dist_transform = cv.distanceTransform(opening,cv.DIST_L2,5)
ret, sure_fg = cv.threshold(dist_transform,0.05*dist_transform.max(),255,0)


sure_fg = np.uint8(sure_fg)
contours, hierarchy=cv.findContours(sure_fg,cv.RETR_EXTERNAL,cv.CHAIN_APPROX_NONE)
i = 0
for c in contours:
    r = random.randint(0, 255)
    g = random.randint(0, 255)
    b = random.randint(0, 255)
    cv.fillPoly(img, pts=[c], color= (r, g, b))
    cv.drawContours(img, [c], -1, (r, g, b), 3)
    i += 10

cv.imshow('contours',img)




cv.waitKey(0)