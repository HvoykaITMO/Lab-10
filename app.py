import json
import pyttsx3
import pyaudio
import vosk
import requests
import time
import webbrowser


website = 'https://api.dictionaryapi.dev/api/v2/entries/en/'


class Speech:  # Класс синтеза речи
    def __init__(self):
        self.tts = pyttsx3.init('sapi5')  # создаёт объект синтезатора речи, используя SAPI5
        self.voices = self.tts.getProperty('voices')  # возвращает список доступных голосов, установленных в системе.

    def set_voice(self, speaker):  # установка голоса
        if 0 <= speaker < len(self.voices):  # проверка на корректность индекса
            return self.voices[speaker].id
        return self.voices[0].id  # если индекс был некорректный

    def text2voice(self, speaker=1, text='Готов!'):  # преобразование текста в голос
        self.tts.setProperty('voice', self.set_voice(speaker))  # выбираем голос
        self.tts.say(text)  # добавляем текст в очередь для произнесения
        self.tts.runAndWait()  # запускаем произнесение текста и ждёт, пока очередь не опустеет


class Recognize:
    def __init__(self):
        self.model = vosk.Model('vosk-model-en-us-0.42-gigaspeech')  # загружаем модель
        self.record = vosk.KaldiRecognizer(self.model, 16000)  # создаём распознаватель
        self.pa = pyaudio.PyAudio()  # создаём объект для работы с аудиоустройствами через PyAudio
        self.stream = self.pa.open(format=pyaudio.paInt16,  # открываем аудиопоток для записи с микрофона
                                   channels=1,
                                   rate=16000,
                                   input=True,
                                   frames_per_buffer=8000)
        self._stop_listening = False

    def listen(self):  # метод - генератор для распознавания речи
        while not self._stop_listening:
            """Получаем аудиопоток"""
            data = self.stream.read(4000, exception_on_overflow=False)
            """self.record.AcceptWaveform гарантирует, что будет обработана полностью завершенная фраза, без этого
                программа будет пытаться обрабатывать на лету каждое полученное слово.
                
               len(data) > 0 не позволит программе обрабатывать полную пустоту (микро выключен)"""
            if self.record.AcceptWaveform(data) and len(data) > 0:
                answer = json.loads(self.record.Result())  # преобразуем json строку с результатом в словарь python
                """Это условие на проверку того, что к нам не попал случайный шум (пустая строка)"""
                if answer.get('text'):
                    yield answer['text']
        self.stream.stop_stream()  # останавливаем поток
        self.stream.close()  # закрываем поток
        self.pa.terminate()  # освобождаем ресурсы PyAudio


class TalkData:  # Детали, важные для диалога. ( + возможность отработать теорию про слоты, property, синглтоны :) )
    _instance = None
    __slots__ = ('_main_word', '_candidate', '_meaning', '_link', '_example', '_is_active')

    def __init__(self):
        self._candidate = None  # Cловарь со всей информацией
        self._main_word = None
        self._meaning = None
        self._link = None
        self._example = None
        self._is_active = False  # Проверка, было ли приветствие. Понил с некультурными не разговаривает!

# Далее идёт много-много property (в основном для закрепления уже пройденного материала)
    @property
    def main_word(self):
        return self._main_word

    @main_word.setter
    def main_word(self, value):
        self._main_word = value

    @property
    def candidate(self):
        return self._candidate

    @candidate.setter
    def candidate(self, value: bool):
        self._candidate = value

    @property
    def meaning(self):
        return self._meaning

    @meaning.setter
    def meaning(self, value):
        self._meaning = value

    @property
    def link(self):
        return self._link

    @link.setter
    def link(self, value):
        self._link = value

    @property
    def example(self):
        return self._example

    @example.setter
    def example(self, value):
        self._example = value

    @property
    def is_active(self):
        return self._is_active

    @is_active.setter
    def is_active(self, value):
        self._is_active = value

    def __new__(cls, *args, **kwargs):  # теперь у нас существует всегда только один экземпляр класса
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance


def speak(text, speaker=1):  # удобная функция, в которую будем передавать фразы для озвучки
    speech = Speech()
    speech.text2voice(speaker=speaker, text=text)  # произнести текст выбранным голосом


def format_speak(phrase, t_type, source):  # Просто красиво оформляем разговор
    if t_type == 'user':
        print('\nYou:', f'\033[36m{phrase.capitalize()}\033[0m', end='\n\n')
        time.sleep(1.3)
    elif t_type == 'ai':
        print('Model:', f'\033[35m{phrase}\033[0m')
        source.stream.stop_stream()
        speak(phrase)
        source.stream.start_stream()


def word_info(word):  # Здесь будем обрабатывать информацию, которую мы получаем
    response = requests.get(website + word)
    if response.status_code != 200:
        return -1
    response_json = response.json()
    info = {'word': word}  # Создадим словарь с информацией о слове
    # Далее много блоков try-except. Я не придумал как это сделать по другому, ведь информация находится по разному пути
    try:
        info['meaning'] = response_json[0]['meanings'][0]['definitions'][0]['definition']
    except KeyError:
        info['meaning'] = "I couldn't find any information about this word."
    try:
        info['example'] = response_json[0]['meanings'][0]['definitions'][0]['example']
    except KeyError:
        info['example'] = "I have not found any information about usage examples."
    try:
        info['link'] = response_json[0]['sourceUrls'][0]
    except KeyError:
        info['link'] = 'I have not found any information about the link to this word.'
    return info


def main():
    talkdata = TalkData()  # экземпляр класса наших данных разговора
    rec = Recognize()  # создаём экземпляр класса тем самым инициализируем модель, настраиваем аудиопоток и т.д.
    text_gen = rec.listen()  # наш генератор для распознавания речи
    rec.stream.stop_stream()  # останавливаем поток, чтобы туда случайно не попал голос ассистента (следующая строка)
    format_speak(phrase="Hi, I'm Ponil, your dictionary assistant. Say 'Hello' to start the dialogue.",
                 source=rec, t_type='ai')
    rec.stream.start_stream()  # и снова запускаем поток
    try:
        for text in text_gen:  # получаем фразы из нашего генератора
            text = text.strip().lower()
            if text == 'hello':  # будем попадать, каждый раз, когда приветствуемся
                talkdata.is_active = True
                info = ("Hi! I'll help you learn the meaning of new words."
                        " To get started, say 'find' and the word you're interested in.")
                format_speak(phrase=text, source=rec, t_type='user')
                format_speak(phrase=info, source=rec, t_type='ai')
                continue
            if not talkdata.is_active:  # Если ты не поздоровался - то не вежливый!!!
                continue
            format_speak(phrase=text, source=rec, t_type='user')
            if text.split()[0] == 'find':  # обработка команды find <word>
                word_book = word_info(text.split()[-1])  # для простоты будем брать просто последнее слово
                if word_book == -1:  # обработка ошибки при получении данных
                    format_speak(phrase='Something went wrong. Please try again.', source=rec, t_type='ai')
                    continue
                format_speak(phrase=f'{word_book["word"].capitalize()} - {word_book["meaning"]}',
                             source=rec, t_type='ai')
                info = 'If you want to know more about this word, say "save".'
                format_speak(phrase=info, source=rec, t_type='ai')
                talkdata.candidate = word_book
            elif text == 'close':  # обработка команды close
                format_speak(phrase='Goodbye, ichtiandr', source=rec, t_type='ai')
                break
            elif text == 'save' and talkdata.candidate is not None:  # обработка команды save
                talkdata.main_word = talkdata.candidate['word']
                talkdata.meaning = talkdata.candidate['meaning']
                talkdata.example = talkdata.candidate['example']
                talkdata.link = talkdata.candidate['link']
                info = ("I remember your word, let's work with it. Here are the available commands:"
                        " 'meaning' - repeat the meaning of the word;"
                        " 'link' - open the link to the word in the browser;"
                        " 'example' - give an example of using the word."
                        " If you are no longer interested in this word, say 'forget' or ask about another word.")
                format_speak(phrase=info, source=rec, t_type='ai')
            elif talkdata.main_word is not None:  # Остальные команды только когда user сказал save
                if text == 'meaning':
                    format_speak(phrase=f'{talkdata.main_word.capitalize()} - {talkdata.meaning}',
                                 source=rec, t_type='ai')
                elif text == 'example':
                    format_speak(phrase=talkdata.example, source=rec, t_type='ai')
                elif text == 'link':
                    format_speak(phrase='One second.', source=rec, t_type='ai')
                    if talkdata.link is not None:
                        webbrowser.open(talkdata.link)
                elif text == 'forget':
                    talkdata.main_word = None
                    talkdata.meaning = None
                    talkdata.example = None
                    talkdata.link = None
                    talkdata.candidate = None
                    info = ("I erased that word. If you want to know something else,"
                            " write me 'find' and the word you are interested in.")
                    format_speak(phrase=info, source=rec, t_type='ai')
                else:
                    format_speak(phrase="I couldn't understand you.", source=rec, t_type='ai')
            else:
                format_speak(phrase="I couldn't understand you.", source=rec, t_type='ai')
            print('-------\n' + '\033[33mSay something...\033[0m', )
    except KeyboardInterrupt:
        print("\nЗавершение работы...")


if __name__ == '__main__':
    main()
