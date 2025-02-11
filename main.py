import sys
import os
import random
import pygame
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QListWidget, QListWidgetItem, QSlider, QFileDialog, QSizePolicy
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QIcon

# Initialize pygame mixer for audio playback.
pygame.mixer.init()

class MusicPlayer(QWidget):
    def __init__(self):
        super().__init__()

        # Define the app window settings.
        self.setWindowTitle('RyMusic')
        app_icon_path = self.get_resource_path('icons/app_icon.png')
        self.setWindowIcon(QIcon(app_icon_path))
        self.setFixedSize(400, 600)

        # Load CSS for style.
        self.load_stylesheet()

        # Add user interface for the application.
        self.layout = QVBoxLayout()

        # Add a layout with options to edit playlist and playback settings.
        self.playlist_settings_layout = QHBoxLayout()

        self.add_audio_files_button = QPushButton("+", self)
        self.add_audio_files_button.clicked.connect(self.add_audio_files)
        self.add_audio_files_button.setToolTip(
            "Opens a file explorer so you can select new songs to add to the playlist."
        )
        self.playlist_settings_layout.addWidget(self.add_audio_files_button)

        self.remove_audio_file_button = QPushButton("-", self)
        self.remove_audio_file_button.clicked.connect(self.remove_audio_file)
        self.remove_audio_file_button.setToolTip("Removes the selected song from the playlist.")
        self.playlist_settings_layout.addWidget(self.remove_audio_file_button)

        self.clear_playlist_button = QPushButton("", self)
        self.clear_playlist_button.clicked.connect(self.clear_playlist)
        self.clear_playlist_button.setToolTip("Clears the entire playlist.")
        clear_all_icon_path = self.get_resource_path('icons/clear_all.png')
        self.clear_playlist_button.setIcon(QIcon(clear_all_icon_path))
        self.playlist_settings_layout.addWidget(self.clear_playlist_button)

        shuffle_icon_path = self.get_resource_path('icons/shuffle_icon.png')
        self.shuffle_button = QPushButton("", self)
        self.shuffle_button.setIcon(QIcon(shuffle_icon_path))
        self.shuffle_button.setCheckable(True)
        self.shuffle_button.setChecked(True)
        self.shuffle_button.setToolTip("Toggles shuffling for audio files.")
        self.shuffle_button.clicked.connect(self.toggle_shuffle)
        self.playlist_settings_layout.addWidget(self.shuffle_button)

        loop_icon_path = self.get_resource_path('icons/loop_icon.png')
        self.loop_button = QPushButton("", self)
        self.loop_button.setIcon(QIcon(loop_icon_path))
        self.loop_button.setCheckable(True)
        self.loop_button.setChecked(False)
        self.loop_button.setToolTip("Toggles looping for the audio file being played.")
        self.playlist_settings_layout.addWidget(self.loop_button)

        # Add the playlist settings layout to the apps main layout.
        self.layout.addLayout(self.playlist_settings_layout)

        # Add a widget for the song playlist.
        self.playlist_widget = QListWidget(self)
        self.playlist_widget.itemDoubleClicked.connect(self.play_selected_audio_file)
        self.layout.addWidget(self.playlist_widget)

        # Add a label for the current song playing.
        self.active_audio_name_label = QLabel("No Song Playing", self)
        self.active_audio_name_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.active_audio_name_label)

        # Add a bar for the current playtime, the total duration of the song, and the seek slider.
        self.slider_layout = QHBoxLayout()

        self.current_playtime_label = QLabel("0:00", self)
        self.slider_layout.addWidget(self.current_playtime_label)

        self.seek_slider = QSlider(Qt.Horizontal, self)
        self.seek_slider.setMinimum(0)
        self.seek_slider.setValue(0)
        self.seek_slider.sliderPressed.connect(self.seek_slider_grabbed)
        self.seek_slider.sliderReleased.connect(self.seek_slider_released)
        self.slider_layout.addWidget(self.seek_slider)

        self.audio_length_label = QLabel("0:00", self)
        self.slider_layout.addWidget(self.audio_length_label)

        self.layout.addLayout(self.slider_layout)

        # Add a layout for playing, pausing, trigger the next or previous song.
        self.controls_layout = QHBoxLayout()

        self.prev_button = QPushButton("|◁", self)
        self.prev_button.clicked.connect(self.play_previous_audio_file)
        self.prev_button.setToolTip("Plays the previous audio file.")
        self.prev_button.setFixedHeight(40)
        self.controls_layout.addWidget(self.prev_button)

        self.play_button = QPushButton("▶", self)
        self.play_button.clicked.connect(self.trigger_play_button)
        self.play_button.setToolTip("Plays the currently selected audio file.")
        self.play_button.setFixedHeight(40)
        self.controls_layout.addWidget(self.play_button)

        self.next_button = QPushButton("▷|", self)
        self.next_button.clicked.connect(self.play_next_audio_file)
        self.next_button.setToolTip("Plays the next audio file.")
        self.next_button.setFixedHeight(40)
        self.controls_layout.addWidget(self.next_button)

        self.layout.addLayout(self.controls_layout)
        self.setLayout(self.layout)

        # Add a timer to update the seek bar.
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.timer_trigger)
        self.timer.start(100)

        # Enable drag and drop functionality so users can
        # drag and drop their audio files into the app.
        self.setAcceptDrops(True)

        # Set variables for handling audio playback.
        self.active_playlist_index = -1
        self.audio_file_paths = []
        self.shuffled_playlist = []
        self.paused = False
        self.slider_grabbed = False
        self.last_seek_position = 0

    def load_stylesheet(self):
        '''Loads external CSS styling.'''
        try:
            css_path = self.get_resource_path('style.css')
            with open(css_path, 'r') as f:
                css = f.read()
                self.setStyleSheet(css)
        except FileNotFoundError:
            print("CSS file not found!")

    def toggle_shuffle(self):
        '''Toggles shuffling for audio files.'''
        if self.shuffle_button.isChecked():
            self.shuffle_playlist()

    def add_audio_files(self):
        '''Opens a file browser so the user can select audio files to add to the playlist.'''
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setNameFilter("Audio Files (*.mp3 *.wav *.ogg *.flac)")
        added_file = False
        if file_dialog.exec_():
            files = file_dialog.selectedFiles()
            for file_path in files:
                self.add_audio_file(file_path)
                added_file = True

        # If at least one file was added, shuffle the playlist.
        if added_file:
            self.shuffle_playlist()

        # Select the last audio file in the playlist.
        self.reset_selected_audio_file()

    def add_audio_file(self, file_path):
        '''Adds an audio file to the playlist.'''
        audio_file_name = os.path.basename(file_path)
        audio_file_name = os.path.splitext(audio_file_name)[0]
        item = QListWidgetItem(audio_file_name)
        self.playlist_widget.addItem(item)

        # Log the newly added files.
        print("Added audio file: " + audio_file_name)
        self.audio_file_paths.append(file_path)
        print("Added audio path: " + file_path)

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

    def reset_selected_audio_file(self):
        '''Re-selects the audio file currently being played.'''

        # If there are no files in the playlist, reset
        # the active index to -1.
        if self.playlist_widget.count() <= 0:
            self.active_playlist_index = -1
            return

        # If an audio file is playing, select that one.
        audio_name = self.active_audio_name_label.text()
        audio_index = self.get_playlist_index_by_name(audio_name)
        if audio_index != -1:
            self.active_playlist_index = audio_index
            playlist_item = self.playlist_widget.item(self.active_playlist_index)
            self.playlist_widget.clearSelection()
            playlist_item.setSelected(True)

        # Otherwise select the first index.
        else:
            playlist_item = self.playlist_widget.item(0)
            self.playlist_widget.clearSelection()
            playlist_item.setSelected(True)

    def clear_playlist(self):
        '''Clears the entier audio playlist.'''
        self.playlist_widget.clear()
        self.audio_file_paths.clear()
        pygame.mixer.music.stop()

        # Reset variables and UI.
        self.active_audio_name_label.setText("No Song Playing")
        self.active_playlist_index = -1
        self.last_seek_position = 0
        self.current_playtime_label.setText("0:00")
        self.audio_length_label.setText("0:00")
        self.play_button.setText("▶")
        self.seek_slider.setValue(0)

    def play_audio(self, playlist_index):
        '''Updates the audio currently being played.'''

        # If there is no audio files in the playlist, do nothing.
        if self.playlist_widget.count() <= 0:
            print("No audio in the playlist to play.")
            return

        # Clamp active playlist index between 0 and the playlist length.
        playlist_index = max(
            0,
            min(playlist_index, self.playlist_widget.count())
        )

        # Update the playlist index to the next index that should be played.
        self.active_playlist_index = playlist_index
        playlist_item = self.playlist_widget.item(self.active_playlist_index)
        self.playlist_widget.clearSelection()
        playlist_item.setSelected(True)

        # Play the audio file.
        audio_path = self.audio_file_paths[self.active_playlist_index]
        pygame.mixer.music.load(audio_path)
        pygame.mixer.music.play(start=0)

        # Update the active audio name label.
        self.active_audio_name_label.setText(playlist_item.text())

        # Reset the current playtime label.
        self.current_playtime_label.setText("0:00")

        # Update the audio length label.
        sound = pygame.mixer.Sound(audio_path)
        audio_length = sound.get_length()
        formatted_audio_length = self.format_time(audio_length)
        self.audio_length_label.setText(formatted_audio_length)

        # Change the play button to a pause button.
        self.paused = False
        self.play_button.setText("||")

        # Reset the stored seek position.
        self.last_seek_position = 0

    def play_selected_audio_file(self):
        '''Plays the audio file from the playlist.'''
        selected_items = self.playlist_widget.selectedItems()
        selected_index = self.playlist_widget.row(selected_items[0])
        if self.active_playlist_index != selected_index:
            self.play_audio(selected_index)
            return

    def trigger_play_button(self):
        '''Trigger function for the play button.'''

        # If the user has selected a different audio file other
        # than the one playing, play that file instead.
        selected_items = self.playlist_widget.selectedItems()
        if selected_items:
            selected_item = selected_items[0]
            selected_index = self.playlist_widget.row(selected_item)
            if self.active_playlist_index != selected_index:
                self.play_audio(selected_index)
                print("Playing user selected track.")
                return

        # If there is no audio playing, always play audio.
        if self.active_playlist_index == -1:
            self.play_audio(self.active_playlist_index)
            print("Playing song, no audio was playing.")
            return

        # If the audio is paused, unpause it.
        if self.paused is True:
            pygame.mixer.music.unpause()
            self.paused = False
            self.play_button.setText("||")
            print("Unpaused audio playback.")

        # Otherwise pause the audio.
        else:
            pygame.mixer.music.pause()
            self.play_button.setText("▶")
            self.paused = True
            print("Paused audio playback.")

    def shuffle_playlist(self):
        '''Randomly re-orders all audio files in the playlist.'''

        # If shuffle is disabled, do nothing.
        if self.shuffle_button.isChecked() is False:
            return

        # If there are no audio files to shuffle, do nothing.
        if self.playlist_widget.count() <= 0:
            return

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

        # If an audio file was playing when the playlist was shuffled,
        # select the currently playing audio file.
        audio_name = self.active_audio_name_label.text()
        audio_index = self.get_playlist_index_by_name(audio_name)
        if audio_index != -1:
            self.active_playlist_index = audio_index
            playlist_item = self.playlist_widget.item(self.active_playlist_index)
            self.playlist_widget.clearSelection()
            playlist_item.setSelected(True)

        print("Shuffled playlist.")

    def play_next_audio_file(self):
        '''Plays the next audio file in the playlist.'''

        # If there are no songs to play, do nothing.
        if self.playlist_widget.count() <= 0:
            print("No audio files in playlist to play.")
            return

        # Play and select the next audio file in the playlist.
        if self.active_playlist_index < self.playlist_widget.count() - 1:
            self.play_audio(self.active_playlist_index + 1)

        # If the last song in the playlist was being played, reset the playlist.
        else:
            self.active_playlist_index = 0
            self.shuffle_playlist()
            self.play_audio(self.active_playlist_index)

    def play_previous_audio_file(self):
        '''Plays the previous audio file in the playlist.'''

        # If there are no songs to play, do nothing.
        if self.playlist_widget.count() <= 0:
            print("No audio files in playlist to play.")
            return

        # Play and select the next audio file in the playlist.
        if self.active_playlist_index > 0:
            self.play_audio(self.active_playlist_index - 1)

        # If the last song in the playlist was being played, reset the playlist.
        else:
            self.active_playlist_index = 0
            self.shuffle_playlist()
            self.play_audio(self.active_playlist_index)

    def dragEnterEvent(self, event: QDragEnterEvent):
        '''Handles drag enter events to support dragging and dropping files into the app.'''
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        '''Handles drag and dropping files into the app.'''
        file_added = False
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if os.path.isfile(file_path):
                self.add_audio_file(file_path)
                file_added = True

        # If at least one audio file was added, shuffle the playlist.
        if file_added:
            self.shuffle_playlist()

        # Select the last audio file in the playlist.
        self.reset_selected_audio_file()

    def get_playlist_index_by_name(self, audio_name):
        '''Returns the index of the song by searching for the playlist name.'''
        matching_items = self.playlist_widget.findItems(audio_name, Qt.MatchExactly)
        if matching_items:
            return self.playlist_widget.row(matching_items[0])
        else:
            return -1

    def timer_trigger(self):
        '''Triggers updates for user interface every few miliseconds.'''

        # Update the seek slider position, excluding when it's
        # not playing music, or manually grabbed.
        if pygame.mixer.music.get_busy() is True:
            if self.slider_grabbed is False:
                self.update_seek_slider_position()

        # If the song has ended, play the next song.
        if self.audio_length_label.text() != "0:00":
            if self.current_playtime_label.text() == self.audio_length_label.text():
                if self.loop_button.isChecked() is True:
                    audio_name = self.active_audio_name_label.text()
                    loop_index = self.get_playlist_index_by_name(audio_name)
                    self.play_audio(loop_index)
                else:
                    self.play_next_audio_file()

    def update_seek_slider_position(self):
        '''Updates the current seek sliders position.'''
        if hasattr(self, 'last_seek_position') and self.last_seek_position is not None:
            current_position = self.last_seek_position + (pygame.mixer.music.get_pos() / 1000)
        else:
            current_position = pygame.mixer.music.get_pos() / 1000

        self.seek_slider.setValue(int(current_position))

        total_duration = self.time_to_seconds(self.audio_length_label.text())
        self.seek_slider.setMaximum(int(total_duration))

        current_playtime = self.format_time(current_position)
        self.current_playtime_label.setText(current_playtime)

    def seek_slider_grabbed(self):
        '''Triggers when the seek slider is grabbed.'''
        self.slider_grabbed = True
        print("User grabbed the seek slider.")

    def seek_slider_released(self):
        '''Triggers when the seek slider is released.'''
        self.slider_grabbed = False
        print("User released seek slider.")

        seek_time = self.seek_slider.value()
        print("User seeked to: " + str(seek_time))

        pygame.mixer.music.pause()
        pygame.mixer.music.play(start=seek_time)

        self.last_seek_position = seek_time
        self.update_seek_slider_position()

    def format_time(self, seconds):
        '''Formats song time into minutes and seconds.'''
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes}:{seconds:02d}"

    def time_to_seconds(self, time):
        '''Converts time in mm:ss format to seconds.'''
        minutes, seconds = map(int, time.split(":"))
        return minutes * 60 + seconds

    def get_resource_path(self, relative_path):
        """ Get the absolute path to a resource, works for PyInstaller bundling. """
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.abspath("."), relative_path)

def main():
    '''Primary function for running the Python application.'''
    app = QApplication(sys.argv)
    player = MusicPlayer()
    player.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
