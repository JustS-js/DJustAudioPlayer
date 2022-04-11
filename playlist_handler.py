from PyQt5 import uic
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtMultimedia import QMediaPlaylist

import sqlite3
import os


class QPlaylistHandler(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi('icons/ph.ui', self)

        self.list_of_urls = []
        self.dict_of_urls_pl = dict()

        self.setup_dir()

        self.load_list_of_playlists()
        self.load_current_playlist()

        self.mode = QMediaPlaylist.Loop

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

        self.menu = QtWidgets.QMenu(self)
        action = self.menu.addAction('Добавить...')
        action.triggered.connect(self.add_track_to_queue)
        action = self.menu.addAction('Удалить')
        action.triggered.connect(self.delete_track_from_queue)

        self.playlistsBox.currentIndexChanged.connect(self.load_current_playlist)
        self.playlistView.itemClicked.connect(self.change_track_in_queue)
        self.playlistView.itemDoubleClicked.connect(self.choose_and_play)

        self.choosed_index = None
        self.playlistView.itemPressed.connect(self._choose_index)

        self.setAcceptDrops(True)

        self.setSizePolicy(
            QtWidgets.QSizePolicy.MinimumExpanding,
            QtWidgets.QSizePolicy.MinimumExpanding
        )

    def choose_and_play(self, item):
        """Функция для запуска трека по двойному нажатию"""
        self.parent().change_track_by_click(self.playlistView.indexFromItem(item).row())
        if self.parent().is_playing:
            self.parent().play_or_pause()
        self.parent().play_or_pause()

    def change_playmode(self):
        """Функция для смены режима проигрывания"""
        if self.sender() == self.parent().repeatModeOption:
            self.mode = QMediaPlaylist.Loop
        elif self.sender() == self.parent().oneModeOption:
            self.mode = QMediaPlaylist.Sequential
        elif self.sender() == self.parent().randomModeOption:
            self.mode = QMediaPlaylist.Random
        self.parent().queue.setPlaybackMode(self.mode)

    def setup_dir(self):
        """Функция для сохранения пользовательской информации"""
        self.data_con = sqlite3.connect('user_data.sqlite')
        self.data_cur = self.data_con.cursor()
        self.data_cur.execute("""CREATE TABLE IF NOT EXISTS dir(url TEXT UNIQUE NOT NULL)""")
        self.data_cur.execute("""CREATE TABLE IF NOT EXISTS theme(isit BOOL NOT NULL)""")
        if len(self.data_cur.execute("""SELECT * from dir""").fetchall()) == 0:
            self.data_cur.execute("""INSERT INTO dir(url) VALUES('')""")
            self.data_con.commit()
        if len(self.data_cur.execute("""SELECT * from theme""").fetchall()) == 0:
            self.data_cur.execute("""INSERT INTO theme(isit) VALUES(1)""")
            self.data_con.commit()
        self.data_cur.execute("""CREATE TABLE IF NOT EXISTS A(
                            id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
                            url TEXT UNIQUE NOT NULL, title TEXT UNIQUE NOT NULL)""")

    def dragEnterEvent(self, event):
        try:
            #  Для каждого файла проверяем, является ли он Аудиофайлом, иначе запрещаем Drag&Drop
            for url in event.mimeData().urls():
                if url.fileName().split('.')[-1] not in ('mp3', 'wav', 'ogg', 'oga', 'aac'):
                    event.ignore()
                    return
            event.accept()
        except Exception as e:
            pass
            # print(e.__class__.__name__, e)

    def dropEvent(self, event):
        try:
            #  Если пользователь закинул файлы, отправляем их на добавление
            self.drag_and_drop_adding(event.mimeData().urls())
        except Exception as e:
            pass
            # print(e.__class__.__name__, e)

    def drag_and_drop_adding(self, urls):
        """Функция для добавления треков в список с помощью drag&drop"""
        #  Прежде, чем добавлять музыку, нам нужно парсить ссылки
        reformatted_urls = []
        for url in urls:
            #  Отрезаем ненужный кусок "file:///"
            url = url.url()[8:]
            #  Проверяем, что этого трека ещё нет в системе, иначе вызываем диалоговое окно
            if url in self.list_of_urls:
                QtWidgets.QMessageBox.warning(self, 'DJust Audio Player',
                                              'Вы не можете добавить в очередь одинаковые файлы.',
                                              QtWidgets.QMessageBox.Ok)
                return
            reformatted_urls.append(url)
        #  Если ошибок нет, добавляем каждый трек в очередь
        for url in reformatted_urls:
            self.list_of_urls.append(url)
            self.parent().add_song_to_mediaplayer(url)
            title = url.split("/")[-1].split(".")[0]
            self.playlistView.addItem(f'{self.playlistView.count() + 1}. {title}')

    def check_for_disappeared_urls(self, songs):
        """Функция для удаления несуществующих ссылок"""
        return list(filter(lambda x: os.path.exists(x[0]), songs))

    def _choose_index(self, item):
        """Мини-функция для изменения индекса при удалении трека из очереди"""
        self.choosed_index = self.playlistView.indexFromItem(item).row()

    def delete_track_from_queue(self):
        """Функция для удаления музыки из очереди"""
        if self.choosed_index is None:
            QtWidgets.QMessageBox.warning(self, 'DJust Audio Player',
                                          'Прежде чем удалить файл, его нужно выделить.',
                                          QtWidgets.QMessageBox.Ok)
            return
        rez = QtWidgets.QMessageBox.question(self, 'DJust Audio Player',
                                             'Вы действительно хотите удалить трек из очереди?',
                                             QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                             QtWidgets.QMessageBox.No)
        if rez == QtWidgets.QMessageBox.No:
            return
        self.list_of_urls.pop(self.choosed_index)
        self.playlistView.clear()
        for n, url in enumerate(self.list_of_urls):
            title = url.split('/')[-1].split('.')[0]
            self.playlistView.addItem(f'{n + 1}. {title}')
        self.parent().delete_song_from_mediaplayer(self.choosed_index)

    def add_track_to_queue(self):
        """Функция для добавления музыки в очередь"""
        try:
            _dir = self.data_cur.execute("""SELECT * FROM dir""").fetchone()[0]
            if not os.path.exists(_dir):
                if os.path.exists(f'C:/Users/{os.environ.get( "USERNAME" )}/Music'):
                    _dir = f'C:/Users/{os.environ.get( "USERNAME" )}/Music'
                else:
                    _dir = ''
            urls = QtWidgets.QFileDialog.getOpenFileNames(self, 'Выбрать аудиофайл(ы)', _dir,
                                                          'Аудиофайл(ы) '
                                                          '(*.mp3 *.wav *.ogg *.oga *.aac)')[0]
            for url in urls:
                if url in self.list_of_urls:
                    QtWidgets.QMessageBox.warning(self, 'DJust Audio Player',
                                                  'Вы не можете добавить в очередь '
                                                  'одинаковые файлы.',
                                                  QtWidgets.QMessageBox.Ok)
                    return
                if not url:
                    return
            self.data_cur.execute(f"""UPDATE dir SET url = '{'/'.join(urls[0].split('/')[:-1])}'""")
            self.data_con.commit()
            for url in urls:
                self.list_of_urls.append(url)
                self.parent().add_song_to_mediaplayer(url)
                title = url.split("/")[-1].split(".")[0]
                self.playlistView.addItem(f'{self.playlistView.count() + 1}. {title}')
        except Exception as e:
            pass
            # print(e)

    def show_context_menu(self, point):
        self.menu.exec(self.mapToGlobal(point))

    def delete_playlist(self):
        """Удаление данного плейлиста"""
        try:
            current_pl = self.list_of_urls_pl[self.playlistsBox.currentText()]
            if current_pl == 'A':
                QtWidgets.QMessageBox.warning(self, 'DJust Audio Player',
                                              'Удаление данного плейлиста может повлечь фатальные '
                                              'ошибки.',
                                              QtWidgets.QMessageBox.Ok)
                return
            ok = QtWidgets.QMessageBox.question(self, 'DJust Audio Player',
                                                'Вы действительно хотите удалить плейлист?',
                                                QtWidgets.QMessageBox.Yes |
                                                QtWidgets.QMessageBox.No,
                                                QtWidgets.QMessageBox.No)
            if ok == QtWidgets.QMessageBox.No:
                return
            self.data_cur.execute(f"""DROP TABLE {current_pl.replace(" ", "_")}""")
            self.data_con.commit()

            #  Перезагружаем
            self.load_list_of_playlists()
            self.playlistsBox.setCurrentIndex(0)
            self.load_current_playlist()
        except Exception as e:
            pass
            # print('delete_playlist')
            # print(e.__class__.__name__, ': ', e, sep='')

    def save_playlist(self):
        """Сохранение данного плейлиста"""
        try:
            #  Спрашиваем пользователя, нужно ли сохранить изменения
            ok = QtWidgets.QMessageBox.question(self, 'DJust Audio Player',
                                                'Сохранить изменения?',
                                                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                                QtWidgets.QMessageBox.Yes)
            if ok == QtWidgets.QMessageBox.No:
                #  Если нет, то выходим из функции
                return

            #  Получаем имя БД
            current_pl = self.list_of_urls_pl[self.playlistsBox.currentText()]
            #  Очищаем старые данные
            self.data_cur.execute(f"""DELETE FROM {current_pl.replace(" ", "_")}""")
            self.data_con.commit()
            #  Загружаем новые
            for n, url in enumerate(self.list_of_urls):
                self.data_cur.execute(f"""INSERT INTO {current_pl.replace(" ", "_")}(id, url, title)
                VALUES({n + 1}, '{url}',
                '{url.split('/')[-1].split('.')[0].replace('_', ' ')}')""")
                self.data_con.commit()
        except Exception as e:
            pass
            # print('save_playlist')
            # print(e.__class__.__name__, e)

    def save_playlist_as(self):
        """Сохранение данного плейлиста в новую БД"""
        try:
            #  Подтверждаем сохранение
            text, ok = QtWidgets.QInputDialog.getText(self, "Сохранить плейлист как...",
                                                      "Имя плейлиста:", QtWidgets.QLineEdit.Normal,
                                                      '')

            #  Избавляемся от запрещённых символов
            text.replace('\\', '').replace('/', '').replace(':', '').replace('*', '')
            text.replace('?', '').replace('"', '').replace('<', '').replace('>', '').replace('|', '')
            if ok and text:
                #  Если имя подходит условиям и пользователь подтвердил операцию,
                #  То сохраняем данные в БД
                if text in [url.split('/')[-1].split('.')[0].replace('_', ' ')
                            for url in self.list_of_urls_pl]:
                    #  Если название нового плейлиста совпадает с существующим, требуем перезапись
                    rez = QtWidgets.QMessageBox.question(self, 'DJust Audio Player',
                                                         'Такой плейлист уже существует. ' +
                                                         'Перезаписать?',
                                                         QtWidgets.QMessageBox.Yes |
                                                         QtWidgets.QMessageBox.No,
                                                         QtWidgets.QMessageBox.No)
                    #  Если пользователь подтвердил перезапись - выполняем операцию
                    if rez == QtWidgets.QMessageBox.Yes:
                        self.data_cur.execute(f"""DELETE FROM {text.replace(" ", "_")}""")
                        self.data_con.commit()
                        for url in self.list_of_urls:
                            self.data_cur.execute(f"""INSERT INTO {text.replace(" ", "_")}
                            (url, title) VALUES('{url}',
                            '{url.split('/')[-1].split('.')[0].replace('_', ' ')}')""")
                            self.data_.commit()
                        self.data_con.close()
                        self.load_list_of_playlists()
                    return

                #  Создаём новую БД с плейлистом
                self.list_of_urls_pl[text] = text.replace(" ", "_")
                self.data_cur.execute(f"""CREATE TABLE IF NOT EXISTS {text.replace(' ', '_')}(
                                id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
                                url TEXT UNIQUE NOT NULL, title TEXT UNIQUE NOT NULL)""")
                #  Загружаем в БД ссылки на песни
                for url in self.list_of_urls:
                    self.data_cur.execute(f"""INSERT INTO {text.replace(' ', '_')}(url, title)
                    VALUES('{url}', '{url.split('/')[-1].split('.')[0].replace('_', ' ')}')""")
                    self.data_con.commit()
                #  Перезагружаем
                index = self.playlistsBox.currentIndex()
                self.load_list_of_playlists()
                self.playlistsBox.setCurrentIndex(index)
            elif ok:
                QtWidgets.QMessageBox.warning(self, 'DJust Audio Player',
                                              'Вы должны дать плейлисту название!',
                                              QtWidgets.QMessageBox.Ok)
        except Exception as e:
            pass
            # print('save_playlist_as')
            # print(e.__class__.__name__, e)

    def change_track_in_queue(self, item):
        """Изменение трека по нажатию мышкой"""
        self.parent().change_track_by_click(self.playlistView.indexFromItem(item).row())

    def set_current_select(self, value):
        """Функция для выделения играющего трека"""
        self.playlistView.setCurrentRow(value)

    def urls(self):
        """Функция для вывода списка с ссылками"""
        return self.list_of_urls

    def load_current_playlist(self):
        """Функция для загрузки музыки из данного плейлиста"""
        try:
            #  Загружаем ссылку на данный плейлист
            current_pl = self.list_of_urls_pl[self.playlistsBox.currentText()]

            #  Загружаем ссылки на песни из БД
            songs = self.data_cur.execute(f"""SELECT url, title FROM {current_pl}""").fetchall()
            #  Очищаем БД от нерабочих ссылок
            songs = self.check_for_disappeared_urls(songs)
            self.data_cur.execute(f"""DELETE FROM {current_pl}""")
            self.data_con.commit()
            for url, title in songs:
                self.data_cur.execute(f"""INSERT INTO {current_pl}(url, title)
                 VALUES('{url}', '{title}')""")
                self.data_con.commit()
            #  Загружаем песни в программу
            self.list_of_urls = []
            self.playlistView.clear()
            for n, (url, title) in enumerate(songs):
                self.playlistView.addItem(f'{n + 1}. {title}')
                self.list_of_urls.append(url)
            self.parent().queue.setPlaybackMode(self.mode)
            self.parent().load_songs_from_playlist()
            self.parent().icon_changed()
        except KeyError:
            pass
        except Exception as e:
            pass
            # print('load_current_playlist')
            # print(e.__class__.__name__, ': ', e, sep='')

    def load_list_of_playlists(self):
        """Функция для загрузки БД с ссылками на плейлисты"""
        try:
            #  Выводим плейлисты на форму
            self.playlistsBox.clear()
            self.list_of_urls_pl = dict()
            playlists = self.data_cur.execute("SELECT name FROM sqlite_master "
                                              "WHERE type='table';").fetchall()
            for title in playlists:
                if title[0] in ('dir', 'sqlite_sequence', 'theme'):
                    continue
                if title[0] == 'A':
                    self.playlistsBox.addItem('Ваша музыка')
                    self.list_of_urls_pl['Ваша музыка'] = title[0]
                else:
                    self.playlistsBox.addItem(title[0].replace('_', ' '))
                    self.list_of_urls_pl[title[0].replace('_', ' ')] = title[0]
        except Exception as e:
            pass
            # print('load_list_of_playlists')
            # print(e.__class__.__name__, ': ', e, sep='')
