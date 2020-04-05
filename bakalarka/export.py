from os import remove
from midiutil import MIDIFile
from music21 import converter


class Export:
    def __init__(self, filename, data, tempo, transpose):
        self.data = data
        self.tempo = tempo
        self.transpose = transpose
        self._runExport(filename)

    def _runExport(self, filename):
        self._prepare()
        if '.midi' in filename:
            self._exportMIDI(filename)
        elif '.musicxml' in filename:
            self._exportMusicXML(filename)
        else:
            raise RuntimeError('Chosen Wrong File Extension')
        print(f'Successfully Exported To {filename}')

    def _prepare(self):
        pass

    def _exportMIDI(self, filename='.tmpMidiFileForExport'):
        midi = MIDIFile(1)
        midi.addTempo(0, 0, self.tempo)
        for pitch, duration, start in self.data:
            midi.addNote(0, 0, pitch + self.transpose, start / 1000, duration / 1000, 100)
        with open(filename, 'wb') as file:
            midi.writeFile(file)

    def _exportMusicXML(self, filename):
        self._exportMIDI()
        score = converter.parse('.tmpMidiFileForExport', format='midi')
        remove('.tmpMidiFileForExport')
        score.write('musicxml', filename)
