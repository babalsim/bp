import cv2 as cv
import numpy as np
import random

i = cv.imread('../dataset/klaviatura.png')
# cv.imshow('original', i)
gray = cv.cvtColor(i, cv.COLOR_BGR2GRAY)
cv.imshow('grayscale', gray)

print(gray)

# # img = cv.GaussianBlur(gray,(3,3),0)
# # cv.imshow('removed noise', img)
# img = i
# # laplacian = cv.Laplacian(img, 8)
# # laplacian = cv.blur(laplacian,(3,3))
# #cv.imshow('laplace', laplacian)
# ret, thresh = cv.threshold(gray,180,255,cv.THRESH_BINARY)
# cv.imshow('thresh', thresh)
#
# lines = cv.HoughLines(thresh, 1, np.pi / 180, 150, None, 0, 0)
# linesp = cv.HoughLinesP(thresh, 1, np.pi / 180, 50, None, 50, 10)
#
# for j in lines:
#     for rho,theta in j:
#         a = np.cos(theta)
#         b = np.sin(theta)
#         x0 = a * rho
#         y0 = b * rho
#         x1 = int(x0 + 1000 * (-b))
#         y1 = int(y0 + 1000 * (a))
#         x2 = int(x0 - 1000 * (-b))
#         y2 = int(y0 - 1000 * (a))
#         cv.line(i,(x1,y1),(x2,y2),(0,255,0),2)
#
# # for j in range(0, len(linesp)):
# #             l = linesp[j][0]
# #             cv.line(i, (l[0], l[1]), (l[2], l[3]), (0,0,255), 3, cv.LINE_AA)
#
# cv.imshow('houghlines5.jpg',i)
#
# kernel = np.ones((9,9),np.uint8)
# opening = cv.morphologyEx(thresh,cv.MORPH_OPEN,kernel, iterations = 1)
#
#
# dist_transform = cv.distanceTransform(opening,cv.DIST_L2,5)
# ret, sure_fg = cv.threshold(dist_transform,0.05*dist_transform.max(),255,0)
#
#
# sure_fg = np.uint8(sure_fg)
# contours, hierarchy=cv.findContours(sure_fg,cv.RETR_EXTERNAL,cv.CHAIN_APPROX_NONE)
# i = 0
# for c in contours:
#     r = random.randint(0, 255)
#     g = random.randint(0, 255)
#     b = random.randint(0, 255)
#     cv.fillPoly(img, pts=[c], color= (r, g, b))
#     cv.drawContours(img, [c], -1, (r, g, b), 3)
#     i += 10
#
# cv.imshow('contours',img)
#



cv.waitKey(0)