import cv2 as cv
import numpy as np


class SegmentBlack:
    lowerBlack, higherBlack = [], []

    def __init__(self, segmentation):
        self.segmentation = segmentation
        self._blackKeysSegmentation()

    def _getBlackKeysContours(self, thresh_value=None):
        gray = cv.cvtColor(self.segmentation.main.capture.background, cv.COLOR_BGR2GRAY)
        gray = cv.GaussianBlur(gray, (3, 3), 0)
        if thresh_value is None:
            ret, thresh = cv.threshold(gray, 0, 255, cv.THRESH_BINARY_INV + cv.THRESH_OTSU)
        else:
            ret, thresh = cv.threshold(gray, self.segmentation.main.gui.thresh.get(), 255, cv.THRESH_BINARY_INV)
        kernel5 = np.ones((5, 5), np.uint8)
        kernel3 = np.ones((3, 3), np.uint8)
        thresh = cv.dilate(thresh, kernel5, iterations=1)
        thresh = cv.erode(thresh, kernel5, iterations=1)
        thresh = cv.erode(thresh, kernel3, iterations=1)
        dist_transform = cv.distanceTransform(thresh, cv.DIST_LABEL_PIXEL, 5)
        ret, sure_fg = cv.threshold(dist_transform, 0.05 * dist_transform.max(), 255, 0)
        sure_fg = np.uint8(sure_fg)
        contours, hierarchy = cv.findContours(sure_fg, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE)
        return contours

    def _blackKeysSegmentation(self):
        rawContours = self._getBlackKeysContours()
        contours = self.segmentation.filterContours(rawContours)
        self._setBlackKeysYBound(contours)
        contours.sort(key=lambda ctr: cv.boundingRect(ctr)[0])
        print(f'Detected {len(contours)} Black Keys')
        self.drawAndMapKeys(contours)

    def _setBlackKeysYBound(self, contours):
        averageYBound = sum([cv.boundingRect(cnt)[3] for cnt in contours]) / len(contours)
        self.segmentation.blackKeysYBound = int(averageYBound * 0.95)

    def assignBlackKey(self, x, key):
        if self.segmentation.main.capture.x_middle == 0:
            raise AttributeError()
        points = self.segmentation.getNonZeroPoints(key)
        if x < self.segmentation.main.capture.x_middle:
            self.lowerBlack.append(points)
        else:
            self.higherBlack.append(points)

    def mapBlackKeys(self):
        self._mapBlackHigherKeys()
        self._mapBlackLowerKeys()
        self._initAvgBlack()

    def _initAvgBlack(self):
        for key, points in self.segmentation.main.blackKeys.items():
            self._setAvgKey(key, points)

    def _setAvgKey(self, key, points):
        s = 0
        for x, y in points:
            s += self.segmentation.main.capture.grayBackground[y][x]
        avg = s / len(points)
        self.segmentation.main.blackAvgKeys[key] = avg

    def _mapBlackHigherKeys(self):
        auxHigher = [2, 3, 2, 2, 3] * 5
        midiHigher = [61]
        for step in auxHigher:
            midiHigher.append(midiHigher[-1] + step)
        for key in zip(midiHigher, self.higherBlack):
            midiNumber, points = key
            self.segmentation.main.blackKeys[midiNumber] = points

    def _mapBlackLowerKeys(self):
        auxLower = [2, 2, 3, 2, 3] * 5
        midiLower = [58]
        for step in auxLower:
            midiLower.append(midiLower[-1] - step)
        self.lowerBlack.reverse()
        for key in zip(midiLower, self.lowerBlack):
            midiNumber, points = key
            self.segmentation.main.blackKeys[midiNumber] = points

    def drawAndMapKeys(self, contours):
        colors = self.segmentation.getColorsFromFile()
        img = self.segmentation.main.capture.background.copy()
        for i in range(len(contours)):
            r, g, b = colors[i]
            key = np.zeros((len(img), len(img[0]), 3), np.uint8)
            M = cv.moments(contours[i])
            x = int(M['m10'] / M['m00'])
            y = int(M['m01'] / M['m00'])
            cv.drawContours(key, [contours[i]], -1, (r, g, b), -1)
            cv.drawContours(img, [contours[i]], -1, (r, g, b), -1)
            cv.putText(img, str(i), (x - 5, y + 100), cv.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
            self.assignBlackKey(x, key)
        self.segmentation.showSegmentedKeys(img, 'Black Keys')
