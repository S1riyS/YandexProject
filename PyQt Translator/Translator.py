import sys
import os
import sqlite3  # Библиотека для работы с БД

from googletrans import Translator  # Библиотека для перевода текста
import pyttsx3  # Библиотека для произношения текста
import speech_recognition as sr  # Библиотека для распознавания голоса


# Библиотеки для работы приложения
from PyQt5 import uic, QtGui
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QAction,
    QFileDialog,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
)

# Словарь с языками
languages = {"Русский": "ru", "Английский": "en", "Японский": "ja", "Немецкий": "nl", "Китайский": "zh-cn"}


class MyWidget(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("translator.ui", self)  # Загружаем UI файл
        self.setFixedSize(920, 510)  # Задаем фиксированный размер
        self.setWindowIcon(QtGui.QIcon("Icons/icon.png"))  # Загружаем иконку приложения
        self.setWindowTitle("Translator")  # Устанавливаем название окна

        self.recognizer = (sr.Recognizer())  # инициализируем библиотеку "speech_recognition"

        self.max_symbols = 3100  # Максимальное количество символов, которое доступно для перевода
        self.font_change_value = 800
        self.can_translate = True  # Можно ли перевести текст
        self.current_font = QFont()


        self.is_history_open = False  # Открыта ли история переводов
        self.row, self.col = 0, 0  # Положение поля в таблицах с историей переводов по умолчанию

        self.db_name = "Translator.db"  # Название БД с историей всех переводов
        self.con = sqlite3.connect(self.db_name)  # Подключаемся к БД
        self.cur = self.con.cursor()  # Создаем курсор для отправки запросов к БД

        self.initUI()  # Функцию, отвечающая за все события
        self.text_changed()  # Функция, устанавливающая значение в поле с кол-вом введенных символов

    # Привязываем элементы приложения к функциямв
    def initUI(self):
        # Установка языков в выпадающие меню
        for lang in languages:
            self.inputLanguage.addItem(lang)
            self.outputLanguage.addItem(lang)
        self.outputLanguage.setCurrentText("Английский")

        # Привязываем функцию "text_changed", которая срабатывает
        # только в случае изменения текста
        self.inputText.textChanged.connect(self.text_changed)

        # -------------------- Кнопки --------------------
        # ------------------------------------------------

        # Кнопка перевода
        self.pushButton.clicked.connect(self.translate)

        # Кнопка перестановки полей
        self.switchButton.clicked.connect(self.switch_languages)

        # Кнопка очистки полей
        self.clearButton.clicked.connect(self.clear)

        # Кнопка добавления перевода в "сохраненные"
        self.saveButton.clicked.connect(self.save_translation)

        # Кнопка, которая открывает историю переводов
        self.historyButton.clicked.connect(self.show_history)

        # Кнопка копирования переведенного тектса в буфер
        self.copyButton.clicked.connect(
            lambda: self.addToClipBoard(self.outputText.toPlainText())
        )
        # Кнопка воспроизведения введенного текста
        self.speakButton_in.clicked.connect(
            lambda: self.speak(self.inputText.toPlainText())
        )
        # Кнопка воспроизведения переведенного текста
        self.speakButton_out.clicked.connect(
            lambda: self.speak(self.outputText.toPlainText())
        )
        # Кнопка голосового ввода
        self.voiceInputButton.clicked.connect(
            lambda: self.voice_input(languages[self.inputLanguage.currentText()])
        )

        # Кнопка удаления всей истории
        self.historyDeleteButton.clicked.connect(
            lambda: self.showDeleteDialog("history")
        )

        # Кнопка удаления "сохраненных"
        self.savedDeleteButton.clicked.connect(
            lambda: self.showDeleteDialog("saved")
        )

        #
        self.chooseFromHistory.clicked.connect(
            lambda: self.set_data_from_widget(self.historyTableWidget)
        )

        #
        self.chooseFromSaved.clicked.connect(
            lambda: self.set_data_from_widget(self.savedTableWidget)
        )

        # --------------- Верхнее меню (Menu bar) -----------------
        # ---------------------------------------------------------

        self.menuOpen_file = QAction("Open", self)
        self.menuOpen_file.triggered.connect(self.openFile)

        self.menuSave_file = QAction("Save", self)
        self.menuSave_file.triggered.connect(self.saveFile)

        menubar = self.menuBar()
        self.fileMenu = menubar.addMenu("&File")
        self.fileMenu.addAction(self.menuOpen_file)
        self.fileMenu.addAction(self.menuSave_file)

        # ---------------- Таблицы (Table widgets) ----------------
        # ---------------------------------------------------------

        # Привязываем функцию "cellClick" к Table widget`ам
        self.historyTableWidget.cellClicked.connect(self.cellClick)
        self.savedTableWidget.cellClicked.connect(self.cellClick)

    # Проверяем, вводит ли пользователь что-то прямо сейчас
    def text_changed(self):
        try:
            text_len = len(self.inputText.toPlainText())

            self.maxSymbols.setText(f"{text_len}/{self.max_symbols}")
            if text_len == 0:
                self.outputText.setPlainText("")

            if text_len > self.font_change_value:
                self.current_font.setPointSize(11)
            else:
                self.current_font.setPointSize(12)

            self.inputText.setFont(self.current_font)
            self.outputText.setFont(self.current_font)

            if text_len > self.max_symbols:
                self.can_translate = False
            else:
                self.can_translate = True

            self.switch_saveBtn_icon()
        except Exception as e:
            print(e)

    # Перестановка полей местами
    def switch_languages(self):
        try:
            # Смена языков
            temp_lang = self.inputLanguage.currentText()
            self.inputLanguage.setCurrentText(self.outputLanguage.currentText())
            self.outputLanguage.setCurrentText(temp_lang)

            # Смена текстов
            temp_text = self.inputText.toPlainText()
            self.inputText.setPlainText(self.outputText.toPlainText())
            self.outputText.setPlainText(temp_text)

            self.translate()
        except Exception as e:
            print(e)

    # Очистка обоих полей ввода
    def clear(self):
        self.inputText.setPlainText("")
        self.outputText.setPlainText("")

    # Копирование переведенного текста
    @staticmethod
    def addToClipBoard(text):
        command = "echo " + text.strip() + "| clip"
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
                self.outputText.setPlainText(result.text)

                self.save_to_data_base()
                self.update_table_widgets()
            except Exception as e:
                print(e)

    # Открыть файл для перевода
    def openFile(self):
        try:
            fname = QFileDialog.getOpenFileName(self, "Open file", "/home")[0]
            f = open(fname, "r")
            with f:
                data = f.read()
                self.inputText.setPlainText(data)
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
            print(f"Не удалось воспроизвести текст ({e})")

    # Голосовой ввод
    def voice_input(self, language):
        try:
            with sr.Microphone() as source:
                lang = f"{language.upper()}-{language}"
                audio = self.recognizer.listen(source)
                text = self.recognizer.recognize_google(audio, language=lang)
                self.inputText.setPlainText(text)
        except Exception as e:
            print(e)

    # Получение информации из поля ввода и текущие языки
    def get_data(self):
        data = [
            self.inputText.toPlainText(),
            languages[self.inputLanguage.currentText()],
            languages[self.outputLanguage.currentText()],
        ]
        return data

    # Сохранение перевода в базу данных
    def save_to_data_base(self):
        data = self.get_data()

        query = """SELECT saved FROM translations
                   WHERE text=? AND input_lang=? AND output_lang=?"""
        saved = self.cur.execute(
            query, data
        ).fetchone()  # Получаем значение поля saved для данного перевода

        # Прооверяем, содержиться ли такой перевод в БД.
        # Если да, то переписываем его с текущим значением парметра "saved".
        # Если нет, то просто добавляем его в БД со значением saved = 0

        if saved is not None:
            query = f"""INSERT INTO translations(text, input_lang, output_lang, saved)
                        VALUES(?, ?, ?, ?)"""
            data.append(saved[0])
        else:
            query = f"""INSERT INTO translations(text, input_lang, output_lang)
                        VALUES(?, ?, ?)"""
        self.cur.execute(query, data)
        self.con.commit()

    # Меняем иконку кнопки "добавить в сохраненные"
    def switch_saveBtn_icon(self):
        data = self.get_data()
        query = """SELECT saved FROM translations
                   WHERE text=? AND input_lang=? AND output_lang=?"""
        result = self.cur.execute(query, data).fetchone()

        if result is not None:
            is_saved = result[0]
            if is_saved == 1:
                self.saveButton.setIcon(QIcon("icons/active_star.png"))
            else:
                self.saveButton.setIcon(QIcon("icons/inactive_star.png"))
        else:
            self.saveButton.setIcon(QIcon("icons/inactive_star.png"))

    # Добавление перевода в "сохраненные"
    def save_translation(self):
        try:
            data = self.get_data()
            query = """SELECT id, saved FROM translations
                       WHERE text=? AND input_lang=? AND output_lang=?"""

            id, result = self.cur.execute(query, data).fetchone()
            if result == 0:
                saved = 1
            else:
                saved = 0
            set_saved_query = f"""UPDATE translations
                                  SET saved = {saved}
                                  WHERE id = {id}"""

            self.cur.execute(set_saved_query)
            self.con.commit()

            self.switch_saveBtn_icon()
            self.update_table_widgets()
        except:
            pass

    # Разворачиваем историю переводов
    def show_history(self):
        # Открываем или закрываем историю
        if not self.is_history_open:
            self.setFixedSize(1200, 510)
            self.is_history_open = True
        else:
            self.setFixedSize(920, 510)
            self.is_history_open = False
        self.update_table_widgets()

    # Обновляем данные, которые выводятся в виджеты
    def update_table_widgets(self):
        try:
            # -------------------------------------------------------------------------------------------
            # ----------------------------------- Все переводы ------------------------------------------

            # Выводим всю историю из БД на виджет
            history_query = """SELECT text, input_lang, output_lang FROM translations
                               ORDER BY id"""
            history_result = self.cur.execute(history_query).fetchall()

            self.historyCountLabel.setText(f"Переводов: {len(history_result)}")

            self.historyTableWidget.setColumnCount(3)
            self.historyTableWidget.setRowCount(0)

            # Меняем размеры столюцов для более удобного просмотра
            header = self.historyTableWidget.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.Stretch)
            header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(2, QHeaderView.ResizeToContents)

            # Заполняем таблицу элементами
            for i, row in enumerate(history_result):
                self.historyTableWidget.setRowCount(
                    self.historyTableWidget.rowCount() + 1
                )
                for j, elem in enumerate(row):
                    self.historyTableWidget.setItem(i, j, QTableWidgetItem(str(elem)))
            # -------------------------------------------------------------------------------------------
            # -------------------------------- "Сохраненные" переводы -----------------------------------

            # Выводим из БД только сохраненные переводы на виджет
            saved_query = """SELECT text, input_lang, output_lang FROM translations
                             WHERE saved = 1
                             ORDER BY id"""
            saved_result = self.cur.execute(saved_query).fetchall()

            self.savedCountLabel.setText(f"Переводов: {len(saved_result)}")

            self.savedTableWidget.setColumnCount(3)
            self.savedTableWidget.setRowCount(0)

            # Меняем размеры столюцов для более удобного просмотра
            header = self.savedTableWidget.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.Stretch)
            header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(2, QHeaderView.ResizeToContents)

            # Заполняем таблицу элементами
            for i, row in enumerate(saved_result):
                self.savedTableWidget.setRowCount(self.savedTableWidget.rowCount() + 1)
                for j, elem in enumerate(row):
                    self.savedTableWidget.setItem(i, j, QTableWidgetItem(str(elem)))
        except Exception as e:
            print(e)

    # Окно подтверждения и удаления соответственно
    def showDeleteDialog(self, what_delete: str):
        try:
            messageBox = QMessageBox()
            messageBox.setIcon(QMessageBox.Information)
            messageBox.setText("Нажмите 'ОК', что бы удалить все")
            messageBox.setWindowTitle("Удаление из БД")
            messageBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)

            returnValue = messageBox.exec()
            if returnValue == QMessageBox.Ok:
                if what_delete == "history":
                    query = """DELETE * FROM translations"""
                else:
                    query = """UPDATE translations
                               SET saved = 0
                               WHERE saved = 1"""
                self.cur.execute(query)
                self.con.commit()

                self.cur.execute(query)
                self.con.commit()

                self.update_table_widgets()
                self.switch_saveBtn_icon()

        except Exception as e:
            print(e)

    # Получает координаты выбранного поля на виджете
    def cellClick(self, row, col):
        self.row = row
        self.col = col

    # Устанавливает выбранный из истории или "сохраненных" перевод в соответствующие поля
    def set_data_from_widget(self, widget, cols=3):
        # Функция для получения ключа из словаря languages
        def get_key(item):
            for i in languages:
                if languages[i] == item:
                    return i

        # Формируем массив с данными из выбранного поля виджета
        data = []
        for col in range(cols):
            data.append(widget.item(self.row, col).text())
        text, input_lang, output_lang = data
        self.inputText.setPlainText(text)
        self.inputLanguage.setCurrentText(get_key(input_lang))
        self.outputLanguage.setCurrentText(get_key(output_lang))

        self.translate()
        self.switch_saveBtn_icon()

    # Функция, вызываемая при закрытии приложения
    def closeEvent(self, event):
        self.con.close()  # Отключаем соединение с БД


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = MyWidget()
    ex.show()
    sys.exit(app.exec_())
