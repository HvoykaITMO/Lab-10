import json
import time
import pyttsx3
import pyaudio
import vosk
import sys


class Speech:
    def __init__(self):
        self.tts = pyttsx3.init('sapi5')
        self.voices = self.tts.getProperty('voices')

    def set_voice(self, speaker):
        if 0 <= speaker < len(self.voices):
            return self.voices[speaker].id
        return self.voices[0].id


    def text2voice(self, speaker=0, text='Готов!'):
        self.tts.setProperty('voice', self.set_voice(speaker))
        self.tts.say(text)
        self.tts.runAndWait()


class Recognize:
    def __init__(self):
        self.model = vosk.Model('model_small')
        self.record = vosk.KaldiRecognizer(self.model, 16000)
        self.pa = pyaudio.PyAudio()
        self.stream = self.pa.open(format=pyaudio.paInt16,
                                   channels=1,
                                   rate=16000,
                                   input=True,
                                   frames_per_buffer=8000
                                   )
        self._stop_listening = False

    def listen(self):
        while not self._stop_listening:
            data = self.stream.read(4000, exception_on_overflow=False)
            if self.record.AcceptWaveform(data) and len(data) > 0:
                self.record.AcceptWaveform(data)
                answer = json.loads(self.record.Result())
                if answer.get('text'):
                    yield answer['text']
        self.stream.stop_stream()
        self.stream.close()
        self.pa.terminate()

def speak(text, speaker=1):
    speech = Speech()
    speech.text2voice(speaker=speaker, text=text)


def main():
    rec = Recognize()
    text_gen = rec.listen()

    rec.stream.stop_stream()
    speak('Starting', speaker=1)
    time.sleep(0.5)
    rec.stream.start_stream()

    try:
        for text in text_gen:
            print(text)
            speak(text, speaker=1),
            if text.strip().lower() == 'закрыть':
                speak('Бывай, ихтиандр', speaker=1)
                break
    except KeyboardInterrupt:
        print("\nЗавершение работы...")


main()
