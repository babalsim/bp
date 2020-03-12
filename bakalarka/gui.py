from tkinter import Frame, Canvas, Button, Scale, DoubleVar, Checkbutton, BooleanVar, HORIZONTAL, Tk, messagebox
import cv2 as cv


class Gui:
    fps = None
    frame_count = None
    duration = None

    def __init__(self, main, size_x, size_y):
        self.main = main
        self.SIZE_X = size_x
        self.SIZE_Y = size_y
        self._initGUI()

    def _initGUI(self):
        self.master = Tk()
        self.master.title('Bakalarka')
        self._initFrameCanvasGUI()
        self._initLoadResetGUI()
        self._initExportGUI()
        self._initTimeControlGUI()
        self._initBackgroundCropGUI()
        self._initPlayMarkGUI()
        self._initCheckButtons()

    def _initFrameCanvasGUI(self):
        self.frame = Frame(self.master, width=self.SIZE_X + 250, height=self.SIZE_X * 2 + 100)
        self.frame.pack()
        self.canvas = Canvas(self.frame, width=self.SIZE_X, height=self.SIZE_Y)
        self.canvas.place(x=0, y=0)

    def _initLoadResetGUI(self):
        Button(self.frame, text='Load', padx=10, pady=1, command=self.main.load).place(
            x=self.SIZE_X + 5, y=5)
        Button(self.frame, text='Reset', padx=10, pady=1, command=self.main.reset).place(
            x=self.SIZE_X + 115, y=5)

    def _initExportGUI(self):
        Button(self.frame, text='Export to MIDI', padx=10, pady=1, command=self.main.exportMIDI).place(
            x=self.SIZE_X + 5, y=45)
        Button(self.frame, text='Export to MusicXML', padx=10, pady=1, command=self.main.exportMusicXML).place(
            x=self.SIZE_X + 115, y=45)

    def _initTimeControlGUI(self):
        self.position = DoubleVar(0)
        self.scale = Scale(self.frame, label='----', from_=0, orient=HORIZONTAL,
                           length=self.SIZE_X, tickinterval=15, command=self.updatePosition, variable=self.position)
        self.scale.place(x=20, y=self.SIZE_X + 20)

    def _initBackgroundCropGUI(self):
        Button(self.frame, text='Set Background', padx=10, pady=1, command=self.main.setBackground).place(
            x=self.SIZE_X + 5, y=95)
        Button(self.frame, text='Crop Keyboard', padx=10, pady=1, command=self.main.cropKeyboardArea).place(
            x=self.SIZE_X + 115, y=95)

    def _initPlayMarkGUI(self):
        self.playOrStopButton = Button(self.frame, text='Play', padx=10, pady=1, command=self.playOrStop)
        self.playOrStopButton.place(x=self.SIZE_X + 5, y=135)
        Button(self.frame, text='Mark C', padx=10, pady=1, command=self.main.markKeyboardMiddle).place(
            x=self.SIZE_X + 115, y=135)

    def _initCheckButtons(self):
        self.handFilter = BooleanVar()
        self.handFilter.set(False)
        Checkbutton(self.frame, text="HandFilter", variable=self.handFilter).place(x=self.SIZE_X + 5, y=165)
        self.transcribing = BooleanVar()
        self.transcribing.set(False)
        Checkbutton(self.frame, text="Transcribing", variable=self.transcribing).place(x=self.SIZE_X + 5, y=185)

    def playOrStop(self):
        if self.main.playing:
            self.stop()
        elif self.main.capture is not None and self.main.capture.isOpened():
            self.play()
        else:
            messagebox.showinfo('Chyba', 'Nie je načítané video.')

    def play(self):
        self.main.playing = True
        self.playOrStopButton['text'] = 'Stop'
        while self.main.playing:
            try:
                self.main.step()
            except FileNotFoundError:######################################neskor prepisat na TypeError
                self.stop()

    def stop(self):
        self.main.playing = False
        self.playOrStopButton['text'] = 'Play'

    def setTimeControlGUI(self):
        self.fps = self.main.capture.get(cv.CAP_PROP_FPS)
        self.frame_count = int(self.main.capture.get(cv.CAP_PROP_FRAME_COUNT))
        self.duration = self.frame_count / self.fps
        self.scale['to'] = self.duration

    def updatePosition(self, position):
        frameNumber = int(position) * self.fps
        self.main.capture.set(cv.CAP_PROP_POS_FRAMES, frameNumber)
        self.main.showFrame()

    def showPosition(self):
        self.position.set(self.main.capture.get(cv.CAP_PROP_POS_MSEC) / 1000)
