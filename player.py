import sys
import sqlite3

from PyQt5 import uic  # Импортируем uic
from PyQt5.QtGui import QPixmap, QIcon, QPalette, QColor
from PyQt5.QtCore import QUrl, QByteArray, Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt5.QtMultimedia import QMediaPlayer, QMediaPlaylist, QMediaContent

from mutagen import File

from volume_equalizer import QVolumeEq
from playlist_handler import QPlaylistHandler
from about import QAbout, QHelp


class MyWidget(QMainWindow):
    def __init__(self):
        super().__init__()
        #  !Костыль
        #  Запрещаю менять размер окна, т.к. не хочу работать с layout`ами
        self.setFixedSize(656, 532)
        self.setWindowIcon(QIcon('icons/icon.ico'))

        #  Добавляем эквалайзер громкости
        self.equalizer = QVolumeEq((255, 255, 102), (255, 26, 10), bg_color=(0, 0, 0, 20))
        self.equalizer.setParent(self)
        self.equalizer.move(20, 391)
        self.equalizer.resize(341, 31)

        uic.loadUi('icons/djap.ui', self)

        self.lightThemeAction.triggered.connect(self.change_theme)
        self.darkThemeAction.triggered.connect(self.change_theme)

        #  Создаём организатор плейлистов
        self.playlist_handler = QPlaylistHandler()
        self.playlist_handler.setParent(self)
        self.playlist_handler.move(380, 40)

        #  Настраиваем меню
        self.saveOption.triggered.connect(self.playlist_handler.save_playlist)
        self.saveAsOption.triggered.connect(self.playlist_handler.save_playlist_as)
        self.deleteOption.triggered.connect(self.playlist_handler.delete_playlist)
        self.aboutOption.triggered.connect(self.about)
        self.helpOption.triggered.connect(self.help)
        self.repeatModeOption.triggered.connect(self.playlist_handler.change_playmode)
        self.oneModeOption.triggered.connect(self.playlist_handler.change_playmode)
        self.randomModeOption.triggered.connect(self.playlist_handler.change_playmode)

        #  Реализация проигрывателя и основного плейлиста
        self.player = QMediaPlayer()
        self.player.durationChanged.connect(self.update_song)
        self.player.setVolume(25)
        self.player.positionChanged.connect(self.update_timeline_position)
        self.queue = QMediaPlaylist(self.player)
        self.player.setPlaylist(self.queue)

        self.queue.setPlaybackMode(QMediaPlaylist.Loop)
        self.is_looped_queue = True

        #  Загрузка музыки из плейлиста
        self.load_songs_from_playlist()

        #  Подключаем кнопки к их функциям
        self.is_playing = False
        self.playBtn.clicked.connect(self.play_or_pause)
        self.queue.currentMediaChanged.connect(self.check_to_stop)

        self.nextBtn.clicked.connect(self.next_audio)
        self.prevBtn.clicked.connect(self.prev_audio)

        self.is_looped_current_track = False
        self.loopBtn.clicked.connect(self.loop_or_unloop_current_track)

        #  Настройка слайдера звука
        self.volumeSlider.hide()
        self.volumeSlider.setValue(25)
        self.equalizer.setValue(25)
        self.volumeSlider.sliderReleased.connect(self.volumeSlider.hide)
        self.volumeSlider.valueChanged.connect(self.change_volume)
        self.volumeBtn.clicked.connect(self.change_volume)

        #  Настройка таймлайна
        self.is_timeline_dragged = False
        self.timeline.sliderReleased.connect(self.timeline_changed)
        self.timeline.sliderPressed.connect(self.timeline_is_dragged)

        #  !Костыль
        #  Имитируем запуск аудиодорожки, чтобы подгрузить данные
        self.play_or_pause()
        self.play_or_pause()
        self.icon_changed()

    def palette(self):
        """Функция для создания темы"""
        con = sqlite3.connect('user_data.sqlite')
        cur = con.cursor()
        if int(cur.execute('SELECT * FROM theme').fetchone()[0]):
            palette = QPalette()
            palette.setColor(QPalette.Window, QColor(240, 240, 240))
            palette.setColor(QPalette.WindowText, Qt.black)
            palette.setColor(QPalette.Base, Qt.white)
            palette.setColor(QPalette.AlternateBase, QColor(246, 246, 246))
            palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 240))
            palette.setColor(QPalette.ToolTipText, Qt.black)
            palette.setColor(QPalette.Text, Qt.black)
            palette.setColor(QPalette.Button, QColor(240, 240, 240))
            palette.setColor(QPalette.ButtonText, Qt.black)
            palette.setColor(QPalette.BrightText, Qt.white)
            palette.setColor(QPalette.Highlight, QColor(0, 120, 215).lighter())
            palette.setColor(QPalette.HighlightedText, Qt.white)
        else:
            palette = QPalette()
            palette.setColor(QPalette.Window, QColor(53, 53, 53))
            palette.setColor(QPalette.WindowText, Qt.white)
            palette.setColor(QPalette.Base, QColor(15, 15, 15))
            palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
            palette.setColor(QPalette.ToolTipBase, Qt.white)
            palette.setColor(QPalette.ToolTipText, Qt.white)
            palette.setColor(QPalette.Text, Qt.white)
            palette.setColor(QPalette.Button, QColor(53, 53, 53))
            palette.setColor(QPalette.ButtonText, Qt.white)
            palette.setColor(QPalette.BrightText, Qt.red)
            palette.setColor(QPalette.Highlight, QColor(142, 45, 197).lighter())
            palette.setColor(QPalette.HighlightedText, Qt.black)
        return palette

    def change_theme(self):
        """Функция для смены темы"""
        con = sqlite3.connect('user_data.sqlite')
        cur = con.cursor()
        if self.sender() == self.lightThemeAction:
            cur.execute('UPDATE theme SET isit = 1')
        else:
            cur.execute('UPDATE theme SET isit = 0')
        con.commit()

        QMessageBox.warning(self, 'DJust Audio Player', 'Чтобы изменения вступили в силу, '
                                                        'перезапустите приложение.', QMessageBox.Ok)

    def help(self):
        """Функция для показа формы справки"""
        self.help = QHelp()

    def about(self):
        """Функция для показа формы О программе"""
        self.about = QAbout()

    def delete_song_from_mediaplayer(self, index):
        """Удалить трек из медиаплеера"""
        self.queue.removeMedia(index)

    def add_song_to_mediaplayer(self, url):
        """Добавить трек в медиаплеер"""
        self.queue.addMedia(QMediaContent(QUrl(url)))

    def change_track_by_click(self, row):
        """Функция для смены трека по нажатию в списке"""
        self.queue.setCurrentIndex(row)

    def check_to_stop(self):
        """Проверяем, чтобы плеер не играл с пустым плейлистом"""
        if self.queue.isEmpty() and self.is_playing:
            self.play_or_pause()

    def load_songs_from_playlist(self):
        """Загрузка музыки из БД в плейлист"""
        self.queue.clear()
        for url in self.playlist_handler.urls():
            self.queue.addMedia(QMediaContent(QUrl(url)))

    def icon_changed(self):
        """Функция для вывода обложки трека"""

        def noicon():
            """В случае отсутствия обложки эта функция ставить свою заглушку"""
            try:
                pixmap = QPixmap()
                if pixmap.load('icons/noicon.png'):
                    self.audioPic.setPixmap(pixmap)
            except Exception as e:
                print(e.__class__.__name__, ': ', e, sep='')

        try:
            #  Читаем метаданные трека
            n = self.queue.currentIndex()
            url = self.playlist_handler.urls()[n if n > -1 else 0]
            file = File(url)
            for i in file.tags.keys():
                if 'APIC:' in i:
                    artwork = file.tags[i].data
                    break
            else:
                raise KeyError
            #  Переводим их в байтовый массив
            ba = QByteArray(artwork)
            #  И загружаем на форму, если это возможно
            pixmap = QPixmap()
            if pixmap.loadFromData(ba):
                self.audioPic.setPixmap(pixmap.scaled(341, 341, Qt.IgnoreAspectRatio))
            else:
                raise KeyError
        except Exception as e:
            #  print(e.__class__.__name__, ': ', e, sep='')
            noicon()

    def timeline_is_dragged(self):
        """Мини-функция для изменения переменной"""
        #  При вызове этой функции мы понимаем, что пользователь
        #  взаимодействует с таймлайном трека
        self.is_timeline_dragged = True

    def timeline_changed(self):
        """Функция для пользовательской перемотки данного трека"""
        #  Перематываем позицию плеера
        self.player.setPosition(self.timeline.value() * 1000)

        #  Пользователь отпустил язычок слайдера и больше не взаимодействует с таймлайном
        self.is_timeline_dragged = False

        #  Вызываем обновление временной шкалы, т.к. произошла перемотка
        self.update_timeline_position()

    def update_song(self):
        """Изменение данных о треке"""
        #  !Костыль
        #  Проматываем несколько миллисекунд, чтобы избежать повреждённых треков
        self.player.setPosition(10)

        #  Меняем обложку
        self.icon_changed()

        #  Выделяем в списке новый трек
        self.playlist_handler.set_current_select(self.queue.currentIndex())

        #  Меняем название окна в соответствии с играющим треком
        title = self.queue.currentMedia().canonicalUrl().path().split('/')[-1]
        if title:
            self.setWindowTitle('DJust Audio Player | %s' % title)
        else:
            self.setWindowTitle('DJust Audio Player')

        #  Изменяем длину таймлайна на длину трека
        self.timeline.setMaximum(self.player.duration() // 1000)

        #  Выводим длину трека в минутах/секундах на экран
        minutes, seconds = self.player.duration() // 1000 // 60, self.player.duration() // 1000 % 60
        self.endTimeLabel.setText(str(minutes) + ':{:02d}'.format(seconds))

    def update_timeline_position(self):
        """Функция для обновления временной шкалы"""
        #  Выводим текущее положение плеера в минутах/секундах
        minutes, seconds = self.player.position() // 1000 // 60, self.player.position() // 1000 % 60
        self.currentTimeLabel.setText(str(minutes) + ':{:02d}'.format(seconds))

        #  Чтобы не "вырывать" язычок слайдера из рук пользователя,
        #  проверяем, что пользователь НЕ взаимодейтсвует с таймлайном.
        if not self.is_timeline_dragged:
            self.timeline.setValue(minutes * 60 + seconds)

    def loop_or_unloop_current_track(self):
        """Мини-функция для зацикливания данного трека"""
        if not self.is_looped_current_track:
            #  Зацикливаем
            self.is_looped_current_track = True
            self.queue.setPlaybackMode(QMediaPlaylist.CurrentItemInLoop)
            #  Меняем картинку на перечёркнутый круг
            self.loopBtn.setStyleSheet('background-image: url(icons/unloop.png)')
        else:
            #  убираем цикл
            self.is_looped_current_track = False
            self.queue.setPlaybackMode(self.playlist_handler.mode)
            self.loopBtn.setStyleSheet('background-image: url(icons/loop.png)')

    def next_audio(self):
        """Функция для перемотки на следующий в списке трек"""
        if self.queue.mediaCount() - 1 == self.queue.currentIndex():
            #  Если трек ппоследний в списке, возвращаемся к первому
            self.queue.setCurrentIndex(0)
        else:
            #  Иначе просто перемещаемся к следующему
            self.queue.next()

    def prev_audio(self):
        """Функция для перемотки на предыдущий в списке трек"""
        if 0 == self.queue.currentIndex():
            #  Если трек первый в списке, возвращаемся к последнему
            self.queue.setCurrentIndex(self.queue.mediaCount() - 1)
        else:
            #  Иначе просто возвращаемся к предыдущему
            self.queue.previous()

    def play_or_pause(self):
        """Функция для запуска или остановки проигрывателя"""
        if self.queue.isEmpty():
            #  Меняем картинку на стрелочку (проигрывание)
            self.is_playing = False
            self.playBtn.setStyleSheet('background-image: url(icons/play.png)')
            #  Ставим на паузу
            self.player.pause()
            return
        if self.is_playing:
            #  Меняем картинку на стрелочку (проигрывание)
            self.is_playing = False
            self.playBtn.setStyleSheet('background-image: url(icons/play.png)')
            #  Ставим на паузу
            self.player.pause()
        else:
            #  Меняем картинку на 2 палочки (пауза)
            self.is_playing = True
            self.playBtn.setStyleSheet('background-image: url(icons/pause.png)')
            #  Запускаем звук
            self.player.play()

    def change_volume(self):
        """Мини-Функция для передачи уровня громкости в плеер"""
        #  Функцию использует несколько объектов сразу, проверяем вызывателя
        if self.sender() == self.volumeBtn:
            #  Если функцию вызвала кнопка, то включаем/выключаем отображение слайдера
            if not self.volumeSlider.isHidden():
                self.volumeSlider.hide()
            else:
                self.volumeSlider.show()
        else:
            #  Иначе функцию вызвал сам слайдер. Значит, меняем значение
            self.player.setVolume(self.volumeSlider.value())
            self.equalizer.setValue(self.volumeSlider.value())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    ex = MyWidget()
    app.setPalette(ex.palette())
    ex.show()
    sys.exit(app.exec_())
