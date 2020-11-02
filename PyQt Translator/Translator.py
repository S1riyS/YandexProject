import sys
import os
import sqlite3

from googletrans import Translator  # Библиотека для перевода текста
import pyttsx3 # Библиотека для произношения текста
import speech_recognition as sr # Библиотека для распознавания голоса


# Библиотеки для работы приложения
from PyQt5 import uic, QtGui
from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, QFileDialog

# Словарь с языками
languages = {"Русский": "ru", "Английский": "en", "Японский": "ja", "Немецкий": "nl"}


class MyWidget(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("translator.ui", self)
        self.setFixedSize(920, 500)
        self.setWindowIcon(QtGui.QIcon("Icons/icon.png"))
        self.setWindowTitle("Translator")

        self.recognizer = sr.Recognizer()
        self.max_symbols = 3100
        self.can_translate = True

        self.db_name = 'Translator.db'
        self.con = sqlite3.connect(self.db_name)
        self.cur = self.con.cursor()

        self.initUI()
        self.text_changed()

    def initUI(self):
        # Установка языков в выпадающие меню
        for lang in languages:
            self.inputLanguage.addItem(lang)
            self.outputLanguage.addItem(lang)
        self.outputLanguage.setCurrentText("Английский")

        # Текстовые поля
        self.inputText.textChanged.connect(self.text_changed)

        # Кнопки
        self.pushButton.clicked.connect(self.translate)

        self.switchButton.clicked.connect(self.switch_languages)

        self.clearButton.clicked.connect(self.clear)

        self.copyButton.clicked.connect(
            lambda: self.addToClipBoard(self.outputText.toPlainText())
        )

        self.speakButton_in.clicked.connect(
            lambda: self.speak(self.inputText.toPlainText())
        )
        self.speakButton_out.clicked.connect(
            lambda: self.speak(self.outputText.toPlainText())
        )

        self.voiceInputButton.clicked.connect(
            lambda: self.voice_input(languages[self.inputLanguage.currentText()])
        )

        # Верхнее меню
        self.menuOpen_file = QAction("Open", self)
        self.menuOpen_file.triggered.connect(self.openFile)

        self.menuSave_file = QAction("Save", self)
        self.menuSave_file.triggered.connect(self.saveFile)

        menubar = self.menuBar()
        self.fileMenu = menubar.addMenu("&File")
        self.fileMenu.addAction(self.menuOpen_file)
        self.fileMenu.addAction(self.menuSave_file)

    # Проверяем, вводит ли пользователь что-то
    def text_changed(self):
        text_len = len(self.inputText.toPlainText())

        self.maxSymbols.setText(f'{text_len}/{self.max_symbols}')
        if text_len > self.max_symbols:
            self.can_translate = False
        else:
            self.can_translate = True

    # Перестановка полей местами
    def switch_languages(self):
        try:
            self.translate()

            # Смена языков
            temp_lang = self.inputLanguage.currentText()
            self.inputLanguage.setCurrentText(self.outputLanguage.currentText())
            self.outputLanguage.setCurrentText(temp_lang)

            # Смена текстов
            temp_text = self.inputText.toPlainText()
            self.inputText.setText(self.outputText.toPlainText())
            self.outputText.setText(temp_text)
        except Exception as e:
            print(e)

    # Очистка обоих полей ввода
    def clear(self):
        self.inputText.setText('')
        self.outputText.setText('')

    # Копирование переведенного текста
    def addToClipBoard(self, text):
        command = 'echo ' + text.strip() + '| clip'
        os.system(command)

    # Перевод
    def translate(self):
        if self.can_translate:
            translator = Translator()
            in_text = self.inputText.toPlainText()
            in_lang = languages[self.inputLanguage.currentText()]
            out_lang = languages[self.outputLanguage.currentText()]
            try:
                result = translator.translate(in_text, src=in_lang, dest=out_lang)
                self.outputText.setText(result.text)

                self.save_to_data_base()
            except:
                pass

    # Открыть файл для перевода
    def openFile(self):
        try:
            fname = QFileDialog.getOpenFileName(self, "Open file", "/home")[0]
            f = open(fname, "r")
            with f:
                data = f.read()
                self.inputText.setText(data)
        except:
            pass

    # Сохранить перевеленный текст в текстовый файл
    def saveFile(self):
        try:
            fname = QFileDialog.getSaveFileName(self, "Save file", "/translate.txt")[0]
            f = open(fname, "tw")
            with f:
                f.write(self.outputText.toPlainText())
        except:
            pass

    # Воспроизведение текста
    def speak(self, text):
        try:
            self.engine = pyttsx3.init()
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            print(f'Не удалось воспроизвести текст ({e})')

    # Голосовой ввод
    def voice_input(self, language):
        try:
            with sr.Microphone() as source:
                lang = f'{language.upper()}-{language}'
                audio = self.recognizer.listen(source)
                text = self.recognizer.recognize_google(audio, language=lang)
                self.inputText.setText(text)
        except Exception as e:
            print(e)

    # Сохранение переводла в базу данных
    def save_to_data_base(self):
        data = (
            self.inputText.toPlainText(),
            languages[self.inputLanguage.currentText()],
            languages[self.outputLanguage.currentText()],
        )

        print(data)
        query = """INSERT INTO translations(text, input_lang, output_lang)
                   VALUES(?, ?, ?)"""
        self.cur.execute(query, data)
        self.con.commit()

    def closeEvent(self, event):
        self.con.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = MyWidget()
    ex.show()
    sys.exit(app.exec_())
