#! /usr/bin/env python3
#
# PyQt5-based video-sync example for VLC Python bindings
# Copyright (C) 2009-2010 the VideoLAN team
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston MA 02110-1301, USA.
#
"""
This module contains a bare-bones VLC player class to play videos.

Author: Saveliy Yusufov, Columbia University, sy2685@columbia.edu
Date: 25 January 2019
"""

import os
import sys
import queue
import platform

from PyQt5 import QtWidgets, QtGui, QtCore
import vlc


class MiniPlayer(QtWidgets.QMainWindow):
    """Stripped-down PyQt5-based media player class to sync with "master" video.
    """

    def __init__(self, data_queue, master=None):
        QtWidgets.QMainWindow.__init__(self, master)
        self.setWindowTitle("Mini Player")
        self.statusbar = self.statusBar()
        self.statusbar.showMessage("Ready")

        # Create a basic vlc instance
        self.instance = vlc.Instance()

        self.video_media = None
        self.audio_media = None

        # Create an empty vlc media player for video
        self.video_mediaplayer = self.instance.media_player_new()

        # Create an empty vlc media player for audio
        self.audio_mediaplayer = self.instance.media_player_new()

        self.init_ui()
        self.open_files()

        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(10)
        self.timer.timeout.connect(self.update_ui)

        self.data_queue = data_queue
        self.timer.start()

    def init_ui(self):
        """Set up the user interface
        """
        self.widget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.widget)

        # Create a stacked layout
        self.stacked_layout = QtWidgets.QStackedLayout()

        # In this widget, the video will be drawn
        if platform.system() == "Darwin":  # for MacOS
            self.videoframe = QtWidgets.QMacCocoaViewContainer(0)
        else:
            self.videoframe = QtWidgets.QFrame()

        self.palette = self.videoframe.palette()
        self.palette.setColor(QtGui.QPalette.Window, QtGui.QColor(0, 0, 0))
        self.videoframe.setPalette(self.palette)
        self.videoframe.setAutoFillBackground(True)

        self.stacked_layout.addWidget(self.videoframe)
        self.widget.setLayout(self.stacked_layout)

    def open_files(self):
        """Open media files in media players
        """
        dialog_txt = "Choose Video File"
        filename_video = QtWidgets.QFileDialog.getOpenFileName(self, dialog_txt, os.path.expanduser('~'))
        if not filename_video[0]:
            return

        dialog_txt = "Choose Audio File"
        filename_audio = QtWidgets.QFileDialog.getOpenFileName(self, dialog_txt, os.path.expanduser('~'))
        if not filename_audio[0]:
            return

        # getOpenFileName returns a tuple, so use only the actual file name
        self.video_media = self.instance.media_new(filename_video[0])
        self.audio_media = self.instance.media_new(filename_audio[0])

        # Put the media in the media players
        self.video_mediaplayer.set_media(self.video_media)
        self.audio_mediaplayer.set_media(self.audio_media)

        # Parse the metadata of the files
        self.video_media.parse()
        self.audio_media.parse()

        # Set the title of the track as the window title
        self.setWindowTitle("{}".format(self.video_media.get_meta(0)))

        # The media players have to be 'connected' to the respective QFrames
        # This is platform specific, so we must give the IDs of the QFrames (or similar objects) to vlc
        if platform.system() == "Linux":  # for Linux using the X Server
            self.video_mediaplayer.set_xwindow(int(self.videoframe.winId()))
            self.audio_mediaplayer.set_xwindow(int(self.videoframe.winId()))
        elif platform.system() == "Windows":  # for Windows
            self.video_mediaplayer.set_hwnd(int(self.videoframe.winId()))
            self.audio_mediaplayer.set_hwnd(int(self.videoframe.winId()))
        elif platform.system() == "Darwin":  # for MacOS
            self.video_mediaplayer.set_nsobject(int(self.videoframe.winId()))
            self.audio_mediaplayer.set_nsobject(int(self.videoframe.winId()))

        # Start playing the video and audio as soon as they load
        self.video_mediaplayer.play()
        self.audio_mediaplayer.play()

    def update_ui(self):
        self.update_statusbar()

        try:
            val = self.data_queue.get(block=False)
        except queue.Empty:
            return

        val = int(val)
        if val != self.video_mediaplayer.get_time():
            self.video_mediaplayer.set_time(val)
        if val != self.audio_mediaplayer.get_time():
            self.audio_mediaplayer.set_time(val)

    def update_statusbar(self):
        mtime = QtCore.QTime(0, 0, 0, 0)
        time_video = mtime.addMSecs(self.video_mediaplayer.get_time())
        time_audio = mtime.addMSecs(self.audio_mediaplayer.get_time())

        if self.video_mediaplayer.is_playing():
            self.statusbar.showMessage("Video: " + time_video.toString())
        elif self.audio_mediaplayer.is_playing():
            self.statusbar.showMessage("Audio: " + time_audio.toString())


def main():
    """Entry point for our simple vlc player
    """
    app = QtWidgets.QApplication(sys.argv)

    data_queue = queue.Queue()

    player = MiniPlayer(data_queue)
    player.show()
    player.resize(480, 480)

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
