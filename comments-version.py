"""
Этот файл содержит максимально детальное объяснение каждой строки кода голосового ассистента на Python,
использующего синтез и распознавание речи. Всё оформлено как многострочный комментарий (docstring),
чтобы можно было использовать как документацию внутри проекта.
"""

'''
================================================================================
1. Импорты
================================================================================

import json
import time
import pyttsx3
import pyaudio
import vosk
import sys

- json: модуль стандартной библиотеки Python для работы с данными в формате JSON (JavaScript Object Notation).
  Используется для преобразования строки в структуру данных (словарь Python) и наоборот.
  В данном коде используется для парсинга JSON-ответа от распознавателя речи.

- time: встроенный модуль для работы со временем. Предоставляет функции для пауз (time.sleep),
  измерения времени и т.д. Здесь используется для задержки между произнесением приветствия и началом распознавания,
  чтобы избежать наложения звуков.

- pyttsx3: кросс-платформенная библиотека для синтеза речи (Text-to-Speech, TTS).
  Позволяет программе "говорить" с помощью голосовых движков, доступных в системе (например, SAPI5 на Windows, espeak на Linux).

- pyaudio: библиотека для работы с аудиоустройствами (микрофон, динамики).
  Предоставляет интерфейс для записи и воспроизведения звука через Python.

- vosk: библиотека для распознавания речи (Automatic Speech Recognition, ASR) на основе модели Kaldi.
  Позволяет преобразовывать аудио с микрофона в текст.

- sys: модуль стандартной библиотеки Python для взаимодействия с интерпретатором и системой.
  В данном коде не используется явно, но часто применяется для обработки ошибок и завершения программы.

================================================================================
2. Класс Speech (Синтез речи)
================================================================================

class Speech:
    def __init__(self):
        self.tts = pyttsx3.init('sapi5')
        self.voices = self.tts.getProperty('voices')

- def __init__(self): конструктор класса, вызывается при создании объекта класса.

- self.tts = pyttsx3.init('sapi5'):
  pyttsx3.init('sapi5') - создаёт объект синтезатора речи, используя движок SAPI5 (Speech API 5, стандартный движок Windows для синтеза речи).
  self.tts - ссылка на этот объект, через которую можно управлять голосом и произносить текст.

- self.voices = self.tts.getProperty('voices'):
  self.tts.getProperty('voices') - возвращает список доступных голосов, установленных в системе.
  self.voices - список объектов, каждый из которых содержит информацию о голосе (например, id, имя, язык).
  Пример содержимого self.voices:
    [Voice(id='HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_RU-RU_IRINA_11.0', name='IRINA', languages=['ru-RU']), ...]

    def set_voice(self, speaker):
        if 0 <= speaker < len(self.voices):
            return self.voices[speaker].id
        return self.voices[0].id  # fallback

- def set_voice(self, speaker): метод для выбора голоса по номеру.

- if 0 <= speaker < len(self.voices): проверяет, что номер голоса корректный (не выходит за пределы списка).

- return self.voices[speaker].id: возвращает идентификатор выбранного голоса.
  Идентификатор - это уникальная строка, по которой синтезатор определяет, какой голос использовать.

- return self.voices[0].id: если номер голоса некорректный, возвращает идентификатор первого голоса (fallback).

    def text2voice(self, speaker=0, text='Готов'):
        self.tts.setProperty('voice', self.set_voice(speaker))
        self.tts.say(text)
        self.tts.runAndWait()

- def text2voice(self, speaker=0, text='Готов'): метод для произнесения текста выбранным голосом.

- self.tts.setProperty('voice', self.set_voice(speaker)):
  self.set_voice(speaker) - получает идентификатор голоса.
  self.tts.setProperty('voice', ...) - устанавливает этот голос для синтезатора.

- self.tts.say(text): добавляет текст в очередь для произнесения.
  Текст не произносится сразу, а добавляется в очередь, чтобы можно было управлять очередью и произносить несколько фраз подряд.

- self.tts.runAndWait(): запускает произнесение текста и ждёт, пока очередь не опустеет.
  После этого метода синтезатор "молчит", пока не будет вызван say() снова.

================================================================================
3. Класс Recognize (Распознавание речи)
================================================================================

class Recognize:
    def __init__(self):
        self.model = vosk.Model('model_small')
        self.record = vosk.KaldiRecognizer(self.model, 16000)
        self.pa = pyaudio.PyAudio()
        self.stream = self.pa.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=8000
        )
        self._stop_listening = False

- def __init__(self): конструктор класса.

- self.model = vosk.Model('model_small'):
  vosk.Model('model_small') - загружает модель распознавания речи Vosk (должна быть скачана и находиться в папке model_small).
  self.model - объект модели, содержащий информацию о языке, словаре и т.д.

- self.record = vosk.KaldiRecognizer(self.model, 16000):
  vosk.KaldiRecognizer(self.model, 16000) - создаёт распознаватель, который будет работать с моделью и обрабатывать аудио с частотой 16000 Гц.
  self.record - объект распознавателя, через который передаётся аудио и получается результат.

- self.pa = pyaudio.PyAudio():
  pyaudio.PyAudio() - создаёт объект для работы с аудиоустройствами через PyAudio.
  self.pa - ссылка на этот объект, используется для открытия аудиопотока.

- self.stream = self.pa.open(...):
  self.pa.open(...) - открывает аудиопоток для записи с микрофона.
  format=pyaudio.paInt16 - формат аудио: 16-битный звук (обычный для микрофона).
  channels=1 - один канал (моно).
  rate=16000 - частота дискретизации 16000 Гц (стандартная для распознавания речи).
  input=True - поток для записи (ввода).
  frames_per_buffer=8000 - размер буфера для чтения данных (8000 фреймов).
  self.stream - объект аудиопотока, через который читаются данные с микрофона.

- self._stop_listening = False: флаг для остановки генератора распознавания.

    def listen(self):
        while not self._stop_listening:
            data = self.stream.read(4000, exception_on_overflow=False)
            if self.record.AcceptWaveform(data) and len(data) > 0:
                answer = json.loads(self.record.Result())
                if answer.get('text'):
                    yield answer['text']
        self.stream.stop_stream()
        self.stream.close()
        self.pa.terminate()

- def listen(self): метод-генератор для распознавания речи.

- while not self._stop_listening: цикл работает, пока флаг не установлен в True.

- data = self.stream.read(4000, exception_on_overflow=False):
  self.stream.read(4000, ...) - читает 4000 байт аудиоданных с микрофона.
  exception_on_overflow=False - если буфер переполнен, не выбрасывает исключение, а продолжает работу.

- if self.record.AcceptWaveform(data) and len(data) > 0:
  self.record.AcceptWaveform(data) - передаёт аудиоданные в распознаватель.
  len(data) > 0 - проверяет, что данные не пустые.
  Если распознан текст, возвращает True.

- answer = json.loads(self.record.Result()):
  self.record.Result() - возвращает результат распознавания в формате JSON-строки.
  json.loads(...) - преобразует JSON-строку в словарь Python.
  Пример answer: {'text': 'привет'}

- if answer.get('text'): проверяет, есть ли в ответе поле 'text'.

- yield answer['text']: возвращает распознанный текст через генератор.

- self.stream.stop_stream(): останавливает аудиопоток.

- self.stream.close(): закрывает аудиопоток.

- self.pa.terminate(): освобождает ресурсы PyAudio.

    def stop(self):
        self._stop_listening = True

- def stop(self): метод для остановки генератора распознавания.

- self._stop_listening = True: устанавливает флаг, который прервёт цикл в методе listen().

================================================================================
4. Функция speak
================================================================================

def speak(text, speaker=1):
    speech = Speech()
    speech.text2voice(speaker=speaker, text=text)

- def speak(text, speaker=1): функция для произнесения текста выбранным голосом.

- speech = Speech(): создаёт объект Speech.

- speech.text2voice(speaker=speaker, text=text): произносит текст выбранным голосом.

================================================================================
5. Функция main
================================================================================

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
            if text.strip().lower() == 'закрыть':
                speak('Бывай, ихтиандр', speaker=1)
                break
    except KeyboardInterrupt:
        print("\nЗавершение работы...")
'''