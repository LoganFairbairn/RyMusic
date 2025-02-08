import sys
import os
import pygame
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QListWidget, QListWidgetItem, QSlider, QFileDialog, QMenu, QAction
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QIcon
import random

# Initialize pygame mixer
pygame.mixer.init()

class MusicPlayer(QWidget):
    def __init__(self):
        super().__init__()

        # Define the app window settings.
        self.setWindowTitle('RyMusic')
        self.setFixedSize(400, 600)

        # Load CSS for style.
        self.load_stylesheet()

        # Add user interface for the application.
        self.layout = QVBoxLayout()

        # Add a layout with options to edit playlist and playback settings.
        self.playlist_settings_layout = QHBoxLayout()

        self.add_audio_files_button = QPushButton("+", self)
        self.add_audio_files_button.clicked.connect(self.add_audio_files)
        self.add_audio_files_button.setFixedSize(40, 40)
        self.add_audio_files_button.setToolTip(
            "Opens a file explorer so you can select new songs to add to the playlist."
        )
        self.playlist_settings_layout.addWidget(self.add_audio_files_button)

        self.remove_audio_file_button = QPushButton("-", self)
        self.remove_audio_file_button.clicked.connect(self.remove_audio_file)
        self.remove_audio_file_button.setFixedSize(40, 40)
        self.remove_audio_file_button.setToolTip("Removes the selected song from the playlist.")
        self.playlist_settings_layout.addWidget(self.remove_audio_file_button)

        self.clear_playlist_button = QPushButton("", self)
        self.clear_playlist_button.clicked.connect(self.clear_playlist)
        self.clear_playlist_button.setFixedSize(40, 40)
        self.clear_playlist_button.setToolTip("Clears the entier playlist.")
        self.clear_playlist_button.setIcon(QIcon("./icons/clear_all.png"))
        self.playlist_settings_layout.addWidget(self.clear_playlist_button)

        # Add a settings menu (hamburger) button on the right side of this layout.
        settings_menu_layout = QHBoxLayout()
        settings_menu_layout.addStretch()
        self.settings_menu = QPushButton("☰", self)
        self.settings_menu.setFixedSize(40, 40)
        self.settings_menu.setStyleSheet("font-size: 18px; padding: 5px; border: none;")
        settings_menu_layout.addWidget(self.settings_menu)
        self.playlist_settings_layout.addLayout(settings_menu_layout)
        self.settings_menu.clicked.connect(self.show_settings_menu)

        # Add settings to the settings menu.
        self.menu = QMenu(self)
        self.loop_action = QAction("Loop", self, checkable=True)
        self.menu.addAction(self.loop_action)

        self.shuffle_action = QAction("Shuffle", self, checkable=True)
        self.shuffle_action.setChecked(True)
        self.menu.addAction(self.shuffle_action)

        self.crossfade_action = QAction("Crossfade", self, checkable=True)
        self.menu.addAction(self.crossfade_action)

        # Add the playlist settings layout to the apps main layout.
        self.layout.addLayout(self.playlist_settings_layout)

        # Add a widget for the song playlist.
        self.playlist_widget = QListWidget(self)
        self.layout.addWidget(self.playlist_widget)

        # Add a label for the current song playing,
        self.current_song_label = QLabel("No Song Playing", self)
        self.current_song_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.current_song_label)

        # Add a bar for the current playtime, the total duration of the song, and the seek slider.
        self.slider_layout = QHBoxLayout()

        self.current_time_label = QLabel("0:00", self)
        self.slider_layout.addWidget(self.current_time_label)

        self.seek_slider = QSlider(Qt.Horizontal, self)
        self.seek_slider.setRange(0, 100)
        #self.seek_slider.sliderReleased.connect(self.scrub_song)
        self.slider_layout.addWidget(self.seek_slider)

        self.song_length_label = QLabel("0:00", self)
        self.slider_layout.addWidget(self.song_length_label)

        self.layout.addLayout(self.slider_layout)

        # Add a layout for playing, pausing, trigger the next or previous song.
        self.controls_layout = QHBoxLayout()

        self.prev_button = QPushButton("|◁", self)
        self.prev_button.clicked.connect(self.prev_song)
        self.prev_button.setToolTip("Plays the previous audio file.")
        self.controls_layout.addWidget(self.prev_button)

        self.play_button = QPushButton("▶", self)
        self.play_button.clicked.connect(self.toggle_play_pause)
        self.play_button.setToolTip("Plays the currently selected audio file.")
        self.controls_layout.addWidget(self.play_button)

        self.next_button = QPushButton("▷|", self)
        self.next_button.clicked.connect(self.next_song)
        self.next_button.setToolTip("Plays the next audio file.")
        self.controls_layout.addWidget(self.next_button)

        self.layout.addLayout(self.controls_layout)
        self.setLayout(self.layout)

        # Enable drag and drop functionality so users can
        # drag and drop their audio files into the app.
        self.setAcceptDrops(True)

        # Set variables for handling audio playback.
        self.audio_file_paths = []
        self.shuffled_playlist = []
        self.paused = False
        self.current_song = ""

        # Add variables for playback settings.
        self.loop = False
        self.shuffle = True
        self.crossfade = True

    def show_settings_menu(self):
        '''Shows the settings menu without the automatic drop-down arrow.'''
        self.menu.exec_(self.settings_menu.mapToGlobal(self.settings_menu.rect().bottomLeft()))

    def load_stylesheet(self):
        '''Loads external CSS styling.'''
        try:
            with open('style.css', 'r') as f:
                css = f.read()
                self.setStyleSheet(css)
        except FileNotFoundError:
            print("CSS file not found!")

    def add_audio_files(self):
        '''Opens a file browser so the user can select audio files to add to the playlist.'''
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setNameFilter("Audio Files (*.mp3 *.wav *.ogg *.flac)")
        if file_dialog.exec_():
            files = file_dialog.selectedFiles()
            for file_path in files:
                self.add_audio_file(file_path)
        self.shuffle_playlist()

    def add_audio_file(self, file_path):
        '''Adds an audio file to the playlist.'''
        audio_file_name = os.path.basename(file_path)
        audio_file_name = os.path.splitext(audio_file_name)[0]
        item = QListWidgetItem(audio_file_name)
        self.playlist_widget.addItem(item)
        print("Added audio file: " + audio_file_name)
        self.audio_file_paths.append(file_path)
        print("Added audio path: " + file_path)
        self.reselect_audio_file()

    def remove_audio_file(self):
        '''Removes all selected audio files from the playlist.'''
        selected_items = self.playlist_widget.selectedItems()
        if not selected_items:
            return

        for item in selected_items:
            index = self.playlist_widget.row(item)
            print("Removing index: " + str(index))

            audio_file_path = self.audio_file_paths[index]
            self.audio_file_paths.pop(index)
            print("Removed audio path: " + audio_file_path)

            audio_file_name = item.text()
            self.playlist_widget.takeItem(index)
            print("Removed audio file: " + audio_file_name)

            self.reselect_audio_file()

    def reselect_audio_file(self):
        '''Reselects an audio file from the playlist if no audio file is selected.'''
        any_audio_file_selected = False
        for row in range(self.playlist_widget.count()):
            item = self.playlist_widget.item(row)
            if item.isSelected():
                any_audio_file_selected = True
                break

        if not any_audio_file_selected and self.playlist_widget.count() > 0:
            self.playlist_widget.setCurrentRow(self.playlist_widget.count() - 1)

    def clear_playlist(self):
        '''Clears the entier audio playlist.'''
        self.playlist_widget.clear()
        self.audio_file_paths.clear()

    def toggle_play_pause(self):
        '''Toggles between pause and play to batch functionality into one button.'''
        if self.paused:
            self.play_music()
        else:
            self.pause_music()

    def play_music(self):
        '''Plays the selected audio file from the playlist.'''
        selected_items = self.playlist_widget.selectedItems()

        # Gets the index of the selected audio file in the playlist.
        if selected_items:
            selected_index = self.playlist_widget.row(selected_items[0])
            audio_file_name = selected_items[0].text()
            audio_path = self.audio_file_paths[selected_index]

        # If there is no song selected, do nothing.
        else:
            return

        # If the user is selecting a different song other than
        # the one being played, play that song.
        if self.current_song != audio_file_name:
            pygame.mixer.music.load(audio_path)
            pygame.mixer.music.play()
            self.paused = False
            self.current_song = audio_file_name

        else:
            # If the audio isn't paused, play the song from the beginning.
            if not self.paused:
                pygame.mixer.music.load(audio_path)
                pygame.mixer.music.play()
                self.paused = False
                self.current_song = audio_file_name

            # Otherwise, unpause the audio.
            else:
                pygame.mixer.music.unpause()
                self.paused = False

        # Update UI elements.
        self.play_button.setText("||")
        self.current_song_label.setText(audio_file_name)

    def pause_music(self):
        '''Pauses the audio file being played.'''
        pygame.mixer.music.pause()
        self.play_button.setText("▶")
        self.paused = True

    def shuffle_playlist(self):
        '''Randomly re-orders all audio files in the playlist.'''
        if self.playlist_widget.count() > 0:
            # Create a list of audio names and their corresponding file paths.
            audio_names = [
                self.playlist_widget.item(i).text() for i in range(self.playlist_widget.count())
            ]
            audio_paths = self.audio_file_paths

            # Shuffle the combined list of paths and names.
            combined = list(zip(audio_paths, audio_names))
            random.shuffle(combined)

            # Unzip the shuffled combined list back into audio_paths and audio_names.
            self.audio_file_paths, shuffled_audio_names = zip(*combined)

            # Convert back to lists.
            self.audio_file_paths = list(self.audio_file_paths)
            shuffled_audio_names = list(shuffled_audio_names)

            # Update the items in the playlist widget.
            self.playlist_widget.clear()
            self.playlist_widget.addItems(shuffled_audio_names)

            print("Shuffled playlist.")

    def next_song(self):
        '''Plays the next audio file in the playlist.'''

        # If there are no songs to play, do nothing.
        if self.playlist_widget.count() <= 0:
            print("No audio files in playlist to play.")
            return

        # If the current song isn't defined,
        # play the first song in the playlist.
        if self.current_song == "":
            audio_path = self.audio_file_paths[0]
            playlist_item = self.playlist_widget.item(0)
            audio_file_name = playlist_item.text()
            pygame.mixer.music.load(audio_path)
            pygame.mixer.music.play()
            self.paused = False
            self.current_song = audio_file_name

            # Reset the selection.
            self.playlist_widget.clearSelection()
            playlist_item.setSelected(True)

    def prev_song(self):
        '''Plays the previous audio file in the playlist.'''

        # If there are no songs to play, do nothing.
        if self.playlist_widget.count() <= 0:
            print("No audio files in playlist to play.")
            return
        
        # If the current song isn't defined,
        # play the first song in the playlist.
        # If the current song isn't defined,
        # play the first song in the playlist.
        if self.current_song == "":
            audio_path = self.audio_file_paths[0]
            playlist_item = self.playlist_widget.item(0)
            audio_file_name = playlist_item.text()
            pygame.mixer.music.load(audio_path)
            pygame.mixer.music.play()
            self.paused = False
            self.current_song = audio_file_name

            # Reset the selection.
            self.playlist_widget.clearSelection()
            playlist_item.setSelected(True)

    def dragEnterEvent(self, event: QDragEnterEvent):
        '''Handles drag enter events to support dragging and dropping files into the app.'''
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        '''Handles drag and dropping files into the app.'''
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if os.path.isfile(file_path):
                self.add_audio_file(file_path)

        # Play the next song after the user drops music into the application.
        self.next_song()

    def format_time(self, seconds):
        '''Formats song time into minutes and seconds.'''
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes}:{seconds:02d}"

def main():
    '''Primary function for running the Python application.'''
    app = QApplication(sys.argv)
    player = MusicPlayer()
    player.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
