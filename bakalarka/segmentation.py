import time

import cv2 as cv
import numpy as np

from segmentBlack import SegmentBlack
from segmentWhite import SegmentWhite


class Segmentation:
    blackKeysYBound = None
    kernel5 = np.ones((5, 5), np.uint8)
    kernel3 = np.ones((3, 3), np.uint8)
    blurredBackground = None
    segmentBlack, segmentWhite = None, None
    LOWER_RESOLUTION = 80000

    def __init__(self, main):
        self.main = main
        self._prepareForSegmentation()
        s = time.time()
        self.segmentBlack = SegmentBlack(self)
        self.segmentBlack.blackKeysSegmentation()
        print(f'Black keys was segmented in {time.time() - s} ms')
        t = time.time()
        self.segmentWhite = SegmentWhite(self)
        self.segmentWhite.whiteKeysSegmentation()
        print(f'White keys was segmented in {time.time() - t} ms')
        self._mapKeys()
        cv.waitKey(0)

    def _prepareForSegmentation(self):
        blurred = cv.GaussianBlur(self.main.capture.grayBackground, (3, 3), 0)
        self.blurredBackground = blurred

    def getThreshed(self, image, type):
        if self.main.gui.manualThresh.get():
            ret, thresh = cv.threshold(image, self.main.gui.thresh.get(), 255, type)
        else:
            ret, thresh = cv.threshold(image, 0, 255, type + cv.THRESH_OTSU)
        return thresh

    def _mapKeys(self):
        self.segmentBlack.mapBlackKeys()
        self.segmentWhite.mapWhiteKeys()

    @staticmethod
    def getColorsFromFile(filename='colors.txt'):
        with open(filename, 'r') as f:
            result = [map(int, i.split(' ')) for i in f.read().split('\n')]
            return result

    @staticmethod
    def filterContours(contours):
        forRemove = []
        averageArea = sum([cv.contourArea(cnt) for cnt in contours]) / len(contours)
        thresh = averageArea * 0.6
        for i in range(len(contours)):
            if cv.contourArea(contours[i]) < thresh:
                forRemove.append(i)
        while forRemove:
            contours.pop(forRemove.pop())
        return contours

    def drawAndMapKeys(self, contours, key_color):
        colors = self.getColorsFromFile()
        img = self.main.capture.background.copy()
        for i in range(len(contours)):
            r, g, b = colors[i]
            key = np.zeros((len(img), len(img[0]), 3), np.uint8)
            M = cv.moments(contours[i])
            x = int(M['m10'] / M['m00'])
            y = int(M['m01'] / M['m00'])
            cv.drawContours(key, [contours[i]], -1, (r, g, b), -1)
            cv.drawContours(img, [contours[i]], -1, (r, g, b), -1)
            cv.putText(img, str(i), (x - 5, y + 100), cv.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
            self._assignKey(x, key, key_color)
        self.showSegmentedKeys(img, key_color)

    @staticmethod
    def showSegmentedKeys(img, key_color):
        if key_color == 'white':
            cv.imshow('White Keys', img)
        elif key_color == 'black':
            cv.imshow('Black Keys', img)

    def _assignKey(self, x, key, key_color):
        if key_color == 'white':
            self.segmentWhite.assignWhiteKey(x, key)
        elif key_color == 'black':
            self.segmentBlack.assignBlackKey(x, key)

    @staticmethod
    def getNonZeroPoints(image, y_bound):
        result = []
        for y in range(len(image)):
            for x in range(len(image[0])):
                if any(image[y, x]) and y < y_bound:
                    result.append((x, y))
        return result
