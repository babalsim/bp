import cv2 as cv
import numpy as np


class SegmentWhite:
    def __init__(self, main):
        self.main = main
        self._whiteKeysSegmentation()

    # noinspection DuplicatedCode
    def _getWhiteKeysContours(self):
        croppedKeys = self.main.capture.background[0:self.main.blackKeysYBound, 0:len(self.main.capture.background[0])]
        gray = cv.cvtColor(croppedKeys, cv.COLOR_BGR2GRAY)
        gray = cv.GaussianBlur(gray, (3, 3), 0)
        ret, thresh = cv.threshold(gray, self.main.gui.thresh.get(), 255, cv.THRESH_BINARY)
        kernel = np.ones((5, 5), np.uint8)
        thresh = cv.dilate(thresh, kernel, iterations=1)
        dist_transform = cv.distanceTransform(thresh, cv.DIST_LABEL_PIXEL, 5)
        ret, sure_fg = cv.threshold(dist_transform, 0.05 * dist_transform.max(), 255, 0)
        sure_fg = np.uint8(sure_fg)
        contours, hierarchy = cv.findContours(sure_fg, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE)
        contours = self._splitWideContours(contours)
        return contours

    def _whiteKeysSegmentation(self):
        rawContours = self._getWhiteKeysContours()
        contours = self.main._filterContours(self._splitWideContours(rawContours))
        contours.sort(key=lambda ctr: cv.boundingRect(ctr)[0])
        print(f'Detected {len(contours)} White Keys')
        self.drawAndMapKeys(contours, False)

    def _splitWideContours(self, contours):
        averageWidth = sum([cv.boundingRect(cnt)[2] for cnt in contours]) / len(contours)
        biggerContours = [cnt for cnt in enumerate(contours) if cv.boundingRect(cnt[1])[2] > averageWidth * 1.85]
        while biggerContours:
            index, cnt = biggerContours.pop()
            contours.pop(index)
            a, b = self._splitContour(cnt)
            contours.append(a)
            contours.append(b)
        return contours

    def _splitContour(self, cnt):
        a, b = [], []
        for point in cnt:
            box = sorted(cv.boxPoints(cv.minAreaRect(cnt)).tolist(), key=lambda x: x[1])
            x1, x2 = self.main._getBounds(box)
            x, y = point[0]
            if x < x1 and y < 25 or x < x2 and y > 25 or x in range(min(round(x1), round(x2))):
                a.append([[x, y]])
            else:
                b.append([[x, y]])
        return np.asarray(a), np.asarray(b)

    def assignWhiteKey(self, x, key):
        if self.main.capture.x_middle == 0:
            raise AttributeError()
        points = self.main.getNonZeroPoints(key)
        if x < self.main.capture.x_middle:
            self.main.lowerWhite.append(points)
        else:
            self.main.higherWhite.append(points)

    def mapWhiteKeys(self):
        self._mapWhiteHigherKeys()
        self._mapWhiteLowerKeys()

    def _mapWhiteHigherKeys(self):
        auxHigher = [2, 1, 2, 2, 2, 1, 2] * 5
        midiHigher = [62]
        for step in auxHigher:
            midiHigher.append(midiHigher[-1] + step)
        for key in zip(midiHigher, self.main.higherBlack):
            midiNumber, points = key
            self.main.whiteKeys[midiNumber] = points

    def _mapWhiteLowerKeys(self):
        auxLower = [1, 2, 2, 2, 1, 2, 2] * 5
        midiLower = [60]
        for step in auxLower:
            midiLower.append(midiLower[-1] - step)
        self.main.lowerWhite.reverse()
        for key in zip(midiLower, self.main.lowerWhite):
            midiNumber, points = key
            self.main.whiteKeys[midiNumber] = points

    def drawAndMapKeys(self, contours, black):
        colors = self.main.getColorsFromFile()
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
            if black:
                self.main.assignBlackKey(x, key)
            else:
                self.assignWhiteKey(x, key)
        self.main.showSegmentedKeys(img, black)
