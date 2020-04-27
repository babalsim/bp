import cv2 as cv
import numpy as np


class SegmentWhite:
    lowerWhite, higherWhite = [], []

    def __init__(self, segmentation):
        self.segmentation = segmentation

    def _getWhiteKeysContours(self):
        croppedKeys = self.segmentation.main.capture.grayBackground[0:self.segmentation.blackKeysYBound, 0:len(self.segmentation.main.capture.background[0])]
        thresh = self.segmentation.getThreshed(croppedKeys, cv.THRESH_BINARY)
        thresh = cv.dilate(thresh, self.segmentation.kernel5, iterations=1)
        contours, hierarchy = cv.findContours(thresh, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE)
        contours = self._splitWideContours(contours)
        return contours

    def whiteKeysSegmentation(self):
        rawContours = self._getWhiteKeysContours()
        contours = self.segmentation.filterContours(self._splitWideContours(rawContours))
        contours.sort(key=lambda ctr: cv.boundingRect(ctr)[0])
        print(f'Detected {len(contours)} White Keys')
        self.segmentation.drawAndMapKeys(contours, 'white')

    def _splitWideContours(self, contours):
        averageWidth = sum([cv.boundingRect(cnt)[2] for cnt in contours]) / len(contours)
        biggerContours = [cnt for cnt in enumerate(contours) if cv.boundingRect(cnt[1])[2] > averageWidth * 1.4]
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
            x1, x2 = self._getBounds(box)
            x, y = point[0]
            if x < x1 and y < 25 or x < x2 and y > 25 or x in range(min(round(x1), round(x2))):
                a.append([[x, y]])
            else:
                b.append([[x, y]])
        return np.asarray(a), np.asarray(b)

    def assignWhiteKey(self, x, key):
        if self.segmentation.main.capture.x_middle == 0:
            raise AttributeError()
        points = self.segmentation.getNonZeroPoints(key, (self.segmentation.blackKeysYBound / 3) * 2)
        if x < self.segmentation.main.capture.x_middle:
            self.lowerWhite.append(points)
        else:
            self.higherWhite.append(points)

    def mapWhiteKeys(self):
        self._mapWhiteHigherKeys()
        self._mapWhiteLowerKeys()
        self._initAvgWhite()

    def _initAvgWhite(self):
        for key, points in self.segmentation.main.whiteKeys.items():
            self._setAvgKey(key, points)

    def _setAvgKey(self, key, points):
        s = 0
        for x, y in points:
            s += self.segmentation.main.capture.grayBackground[y][x]
        avg = s / len(points)
        self.segmentation.main.whiteAvgKeys[key] = avg

    def _mapWhiteHigherKeys(self):
        auxHigher = [2, 1, 2, 2, 2, 1, 2] * 5
        midiHigher = [62]
        for step in auxHigher:
            midiHigher.append(midiHigher[-1] + step)
        for key in zip(midiHigher, self.higherWhite):
            midiNumber, points = key
            self.segmentation.main.whiteKeys[midiNumber] = points

    def _mapWhiteLowerKeys(self):
        auxLower = [1, 2, 2, 2, 1, 2, 2] * 5
        midiLower = [60]
        for step in auxLower:
            midiLower.append(midiLower[-1] - step)
        self.lowerWhite.reverse()
        for key in zip(midiLower, self.lowerWhite):
            midiNumber, points = key
            self.segmentation.main.whiteKeys[midiNumber] = points

    @staticmethod
    def _getBounds(box):
        lower, higher = box[:2], box[2:]
        x1 = (lower[0][0] + lower[1][0]) / 2
        x2 = (higher[0][0] + higher[1][0]) / 2
        return x1, x2
