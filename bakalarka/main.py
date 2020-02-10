from tkinter import filedialog, messagebox, Frame, Canvas, Button
from os import path

import cv2 as cv
from tkinter import Tk, NW
from PIL import Image, ImageTk

class Constants:
    SIZE_OF_CANVAS = 400
    COEFFICIENT = 100

class Program:
    SIZE_OF_CANVAS = Constants.SIZE_OF_CANVAS

    def __init__(self):
        self._initGUI()
        self.master.update()
        self.master.mainloop()

    def __del__(self):
        self.cap.release()

    def _initGUI(self):
        self.master = Tk()
        self.master.title('Bakalarka')
        self._initFrameCanvasGUI()
        self._initLoadResetGUI()
        self._initExportGUI()

    def _initFrameCanvasGUI(self):
        self.frame = Frame(self.master, width=self.SIZE_OF_CANVAS + 250, height=self.SIZE_OF_CANVAS * 2 + 100)
        self.frame.pack()
        self.canvas = Canvas(self.frame, width=self.SIZE_OF_CANVAS, height=self.SIZE_OF_CANVAS)
        self.canvas.place(x=0, y=0)

    def load(self):
        try:
            filename = filedialog.askopenfilename(title="Vyberte súbor")
            if not path.isfile(filename):
                raise FileNotFoundError
            self.cap = cv.VideoCapture(filename)
        except:
            messagebox.showinfo("Chyba", "Súbor sa nepodarilo prečítať")
        self.play()

    def play(self):
        fgbg = cv.createBackgroundSubtractorMOG2()
        canvas = Canvas(self.frame, width=self.SIZE_OF_CANVAS, height=self.SIZE_OF_CANVAS)
        canvas.place(x=0, y=self.SIZE_OF_CANVAS)
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            photo = ImageTk.PhotoImage(image=Image.fromarray(cv.cvtColor(frame, cv.COLOR_BGR2RGB)).resize(
                (Constants.SIZE_OF_CANVAS, Constants.SIZE_OF_CANVAS), Image.ANTIALIAS))
            canvas.create_image(0, 0, image=photo, anchor=NW)
            frame = fgbg.apply(frame)
            self.photo = ImageTk.PhotoImage(image=Image.fromarray(cv.cvtColor(frame, cv.COLOR_BGR2RGB)).resize(
                (Constants.SIZE_OF_CANVAS, Constants.SIZE_OF_CANVAS), Image.ANTIALIAS))
            self.canvas.create_image(0, 0, image=self.photo, anchor=NW)
            if cv.waitKey(1) == ord('q'):
                break
            self.canvas.update()

    def reset(self):
        ...

    def exportMIDI(self):
        ...

    def exportMusicXML(self):
        ...

    def getBackground(self):
        try:
            filename = filedialog.askopenfilename(title="Vyberte súbor")
            self.background = cv.imread(filename)
        except:
            messagebox.showinfo("Chyba", "Súbor sa nepodarilo prečítať")

    def setBackground(self):
        ...

    def _initLoadResetGUI(self):
        Button(self.frame, text='Load', padx=10, pady=1, command=self.load).place(
            x=self.SIZE_OF_CANVAS + 5, y=5)
        Button(self.frame, text='Reset', padx=10, pady=1, command=self.reset).place(
            x=self.SIZE_OF_CANVAS + 115, y=5)

    def _initExportGUI(self):
        Button(self.frame, text='Export to MIDI', padx=10, pady=1, command=self.exportMIDI).place(
            x=self.SIZE_OF_CANVAS + 5, y=45)
        Button(self.frame, text='Export to MusicXML', padx=10, pady=1, command=self.exportMusicXML).place(
            x=self.SIZE_OF_CANVAS + 115, y=45)

    def _initBackgroundGUI(self):
        Button(self.frame, text='Set Background', padx=10, pady=1, command=self.setBackground).place(
            x=self.SIZE_OF_CANVAS + 5, y=95)
        Button(self.frame, text='Get Background', padx=10, pady=1, command=self.getBackground).place(
            x=self.SIZE_OF_CANVAS + 115, y=95)





Program()







