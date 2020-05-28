import cv2 as cv


class SegmentBlack:
    lowerBlack, higherBlack = [], []

    def __init__(self, segmentation):
        self.segmentation = segmentation

    def _getBlackKeysContours(self):
        thresh = self.segmentation.getThreshed(self.segmentation.blurredBackground, cv.THRESH_BINARY_INV)
        if self.segmentation.main.capture.get(cv.CAP_PROP_FRAME_WIDTH) * \
                self.segmentation.main.capture.get(cv.CAP_PROP_FRAME_HEIGHT) < self.segmentation.LOWER_RESOLUTION:
            thresh = cv.dilate(thresh, self.segmentation.kernel3, iterations=1)
            thresh = cv.erode(thresh, self.segmentation.kernel3, iterations=1)
        else:
            thresh = cv.dilate(thresh, self.segmentation.kernel5, iterations=1)
            thresh = cv.erode(thresh, self.segmentation.kernel5, iterations=2)
        contours, hierarchy = cv.findContours(thresh, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE)
        return contours

    def blackKeysSegmentation(self):
        rawContours = self._getBlackKeysContours()
        contours = self.segmentation.filterContours(rawContours)
        self._setBlackKeysYBound(contours)
        contours.sort(key=lambda ctr: cv.boundingRect(ctr)[0])
        print(f'Detected {len(contours)} Black Keys')
        self.segmentation.drawAndMapKeys(contours, 'black')

    def _setBlackKeysYBound(self, contours):
        averageYBound = sum([cv.boundingRect(cnt)[3] for cnt in contours]) / len(contours)
        self.segmentation.blackKeysYBound = int(averageYBound * 0.95)

    def assignBlackKey(self, x, key):
        if self.segmentation.main.capture.x_middle == 0:
            raise AttributeError()
        points = self.segmentation.getNonZeroPoints(key, self.segmentation.blackKeysYBound / 2)
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
