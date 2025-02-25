import sys
import os
import datetime
import shutil
import random
import pygame
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, QPushButton, QLabel, QInputDialog, QMessageBox, QHBoxLayout, QSlider, QAbstractItemView, QMenu, QAction, QLineEdit, QHeaderView
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QTimer, QPoint

# Initialize pygame mixer for audio playback.
pygame.mixer.init()

SUPPORTED_AUDIO_EXTENSIONS = {
    '.wav',  # .wav files
    '.ogg',  # .ogg files (Ogg Vorbis)
    '.mp3',  # .mp3 files
    '.mid',  # .mid files (MIDI)
    '.midi', # .midi files (MIDI)
    '.flac', # .flac files
    '.aif',  # .aif files (Audio Interchange File Format)
    '.aiff', # .aiff files (Audio Interchange File Format)
    '.mp2',  # .mp2 files (MPEG Layer II Audio)
}

class AudioPlayer(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_files()

        # Add a timer to update the seek slider.
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.timer_trigger)
        self.timer.start(100)

        # Define audio player variables.
        self.paused = False
        self.last_seek_position = 0
        self.clipboard = []
        self.cut_mode = False
        self.active_playlist_index = -1
        self.slider_grabbed = False
    
    def init_ui(self):
        '''Initializes the app UI.'''

        # Define the main layout, window settings and styling.
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.setWindowTitle("RyMusic")
        self.resize(600, 800)
        self.load_stylesheet()

        # Initialize the app in chunks.
        self.init_menu_bar()
        self.init_file_browser()
        self.init_audio_controls()
        self.layout.addLayout(self.controls_layout)
        self.setLayout(self.layout)
    
    def init_menu_bar(self):
        '''Initializes the menu bar.'''
        self.menu_layout = QHBoxLayout()

        # Add a button to go to the parent folder.
        self.parent_folder_button = QPushButton("^", self)
        self.parent_folder_button.setToolTip("Go to the parent folder.")
        self.parent_folder_button.clicked.connect(self.go_to_parent_directory)
        self.parent_folder_button.setFixedSize(30, 30)
        self.menu_layout.addWidget(self.parent_folder_button)

        # Create a layout with the input field for the folder path and folder navigation options.
        self.folder_path_field = QLineEdit(self)
        self.folder_path_field.setText("/media/logan/xfiles/music")
        self.folder_path_field.setFixedHeight(30)
        self.folder_path_field.textChanged.connect(self.load_files)
        self.menu_layout.addWidget(self.folder_path_field)
        
        # Create an options menu.
        self.settings_menu = QMenu(self)

        self.loop_audio_action = QAction("Loop Audio", self)
        self.loop_audio_action.setCheckable(True)
        self.loop_audio_action.setChecked(False)
        self.settings_menu.addAction(self.loop_audio_action)

        # Create a hamburger menu button
        icon_path = self.get_resource_path('icons/hamburger_menu_icon.svg')
        self.hamburger_button = QPushButton(self)
        self.hamburger_button.setIcon(QIcon(icon_path))
        self.hamburger_button.setIconSize(self.hamburger_button.size())
        self.hamburger_button.setFixedSize(30, 30)
        self.hamburger_button.setStyleSheet("QPushButton::menu-indicator {image: none;}")
        self.hamburger_button.setMenu(self.settings_menu)
        self.menu_layout.addWidget(self.hamburger_button)

        self.layout.addLayout(self.menu_layout)

    def init_file_browser(self):
        '''Initializes file browser.'''
        self.file_browser = QTreeWidget()
        self.file_browser.setColumnCount(2)
        self.file_browser.setHeaderLabels(["Name", "Type"])
        self.file_browser.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.file_browser.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_browser.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.file_browser.customContextMenuRequested.connect(self.show_right_click_menu)
        self.file_browser.itemDoubleClicked.connect(self.file_item_double_clicked)

        # Set column resize modes.
        header = self.file_browser.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)  # Manually resize this column
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Auto-resize Type column
        header.setStretchLastSection(False)
        self.layout.addWidget(self.file_browser)

        # Delay setting column widths until the widget is fully shown
        QTimer.singleShot(0, self.resize_columns)

    def resize_columns(self):
        """Adjusts column widths after widget is fully displayed."""
        total_width = self.file_browser.viewport().width()
        if total_width > 0:
            name_width = int(total_width * 0.8)
            self.file_browser.setColumnWidth(0, name_width)

    def resizeEvent(self, event):
        """Ensures columns resize dynamically when the widget resizes."""
        super().resizeEvent(event)
        self.resize_columns()

    def init_audio_controls(self):
        '''Initializes audio controls.'''

        # Add a label for the current song playing.
        self.active_audio_name_label = QLabel("No Audio Playing", self)
        self.active_audio_name_label.setAlignment(Qt.AlignCenter)
        self.active_audio_name_label.setStyleSheet("font-size: 16pt; padding-top: 10px; padding-bottom: 10px;")
        self.layout.addWidget(self.active_audio_name_label)

        # Add a bar for the current playtime, the total duration of the song, and the seek slider.
        self.slider_layout = QHBoxLayout()

        self.current_playtime_label = QLabel("0:00", self)
        self.current_playtime_label.setStyleSheet("font-size: 20px; padding-right: 10px;")
        self.slider_layout.addWidget(self.current_playtime_label)

        self.seek_slider = QSlider(Qt.Horizontal, self)
        self.seek_slider.setMinimum(0)
        self.seek_slider.setValue(0)
        self.seek_slider.setDisabled(True)
        self.seek_slider.sliderPressed.connect(self.seek_slider_grabbed)
        self.seek_slider.sliderReleased.connect(self.seek_slider_released)
        self.slider_layout.addWidget(self.seek_slider)

        self.audio_length_label = QLabel("0:00", self)
        self.audio_length_label.setStyleSheet("font-size: 20px; padding-left: 10px;")
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
        self.play_button.setFixedHeight(40)
        self.controls_layout.addWidget(self.play_button)

        self.next_button = QPushButton("▷|", self)
        self.next_button.clicked.connect(self.play_next_audio_file)
        self.next_button.setToolTip("Plays the next audio file.")
        self.next_button.setFixedHeight(40)
        self.controls_layout.addWidget(self.next_button)

    def load_stylesheet(self):
        '''Loads external CSS styling.'''
        try:
            css_path = self.get_resource_path('style.css')
            with open(css_path, 'r') as f:
                css = f.read()
                self.setStyleSheet(css)
        except FileNotFoundError:
            print("CSS file not found!")

    def show_right_click_menu(self, pos: QPoint):
        menu = QMenu(self)

        selected_items = self.file_browser.selectedItems()
        if selected_items:
            play_action = QAction("Play")
            play_action.triggered.connect(self.play_first_selected_file)
            menu.addAction(play_action)

            rename_action = QAction("Rename", self)
            rename_action.triggered.connect(self.rename_file)
            if len(selected_items) > 1:
                rename_action.setEnabled(False)
            menu.addAction(rename_action)

            cut_action = QAction("Cut", self)
            cut_action.triggered.connect(self.cut_files)
            menu.addAction(cut_action)

            copy_action = QAction("Copy", self)
            copy_action.triggered.connect(self.copy_files)
            menu.addAction(copy_action)

            paste_action = QAction("Paste", self)
            paste_action.triggered.connect(self.paste_files)
            menu.addAction(paste_action)

            delete_action = QAction("Delete", self)
            delete_action.triggered.connect(self.delete_files)
            menu.addAction(delete_action)

        new_folder_action = QAction("Create New Folder")
        new_folder_action.triggered.connect(self.create_new_folder)
        menu.addAction(new_folder_action)

        refresh_directory_action = QAction("Refresh Directory")
        refresh_directory_action.triggered.connect(self.load_files)
        menu.addAction(refresh_directory_action)

        sort_az_action = QAction("Sort A - Z", self)
        sort_az_action.triggered.connect(self.sort_files)
        menu.addAction(sort_az_action)

        shuffle_action = QAction("Shuffle Audio Files", self)
        shuffle_action.triggered.connect(self.shuffle_audio_files)
        menu.addAction(shuffle_action)
        
        menu.exec_(self.file_browser.viewport().mapToGlobal(pos))
    
    def load_files(self):
        '''Loads files and folders into the file browser (QTreeWidget).'''
        self.file_browser.clear()

        # If the path does not exist, don't load any files.
        current_path = self.folder_path_field.text()
        if not os.path.exists(current_path):
            return

        folders = []
        audio_files = []

        try:
            for item in os.listdir(current_path):

                # Skip adding hidden folders.
                if item.startswith('.'):
                    continue
                
                # Add folders to the file browser.
                item_path = os.path.join(current_path, item)
                if os.path.isdir(item_path):
                    folders.append((item, f"Folder"))
                
                # Add audio files to the file browser.
                elif os.path.splitext(item)[1].lower() in SUPPORTED_AUDIO_EXTENSIONS:
                    name, ext = os.path.splitext(item)
                    audio_files.append((name, ext))

        except PermissionError:
            pass

        for folder, folder_info in sorted(folders):
            folder_item = QTreeWidgetItem([folder, folder_info])
            folder_item.setIcon(0, QIcon.fromTheme("folder"))
            self.file_browser.addTopLevelItem(folder_item)

        for name, file_type in sorted(audio_files):
            self.file_browser.addTopLevelItem(QTreeWidgetItem([name, file_type]))

        self.folder_path_field.setText(current_path)

        # Clear focus to avoid showing focus highlighting.
        self.file_browser.clearFocus()

    def file_item_double_clicked(self, item, column):
        '''Triggers when an item in the file browser is double clicked.'''

        # If a folder was double clicked, open it.
        current_path = self.folder_path_field.text()
        file_extension = item.text(1)

        new_path = os.path.join(current_path, item.text(0))
        if os.path.isdir(new_path):
            self.folder_path_field.setText(new_path)
            self.load_files()

        # Play an audio file if it was double clicked.
        elif file_extension in SUPPORTED_AUDIO_EXTENSIONS:
            audio_path = self.get_file_browser_item_path(item)
            self.play_audio(audio_path)
    
    def go_to_parent_directory(self):
        current_path = self.folder_path_field.text()
        parent_path = os.path.dirname(current_path)
        if parent_path and parent_path != current_path:
            self.folder_path_field.setText(parent_path)
            self.load_files()
    
    def play_audio(self, audio_path):
        '''Updates the audio currently being played.'''

        # If the provided audio path doesn't exist, do nothing.
        self.log(f"Attempting to play: {audio_path}")
        if not os.path.exists(audio_path):
            self.log("Invalid path.")
            return

        # Play the audio.
        pygame.mixer.music.load(audio_path)
        pygame.mixer.music.play(start=0)

        # Update the name of the audio file being played.
        audio_name = os.path.splitext(os.path.basename(audio_path))[0]
        self.active_audio_name_label.setText(audio_name)

        # Reset the playtime label and variables.
        self.current_playtime_label.setText("0:00")
        self.paused = False
        self.last_seek_position = 0
        self.seek_slider.setDisabled(False)
        
        # Update the label with the length of the audio file being played.
        sound = pygame.mixer.Sound(audio_path)
        audio_length = sound.get_length()
        formatted_audio_length = self.format_time(audio_length)
        self.audio_length_label.setText(formatted_audio_length)

        # Change the play button to have a pause icon.
        self.play_button.setText("||")

    def play_first_audio_in_folder(self):
        '''Plays the first audio file in the current folder.'''
        for i in range(self.file_browser.topLevelItemCount()):
            item = self.file_browser.topLevelItem(i)
            item_type = item.text(1)
            if item_type != "Folder":
                self.file_browser.clearSelection()
                item.setSelected(True)
                audio_path = self.get_file_browser_item_path(item)
                self.play_audio(audio_path)
                return

    def play_first_selected_file(self):
        '''Plays the first selected file.'''
        selected_items = self.file_browser.selectedItems()
        if selected_items:
            audio_path = self.get_file_browser_item_path(selected_items[0])
            self.play_audio(audio_path)

    def play_first_audio(self):
        '''Plays the first selected audio file, or the first audio file in the folder if no files are selected.'''

        # Play the first selected audio file.
        selected_items = self.file_browser.selectedItems()
        if selected_items:
            audio_path = self.get_file_browser_item_path(selected_items[0])
            self.play_audio(audio_path)

        # Play the first audio file in the folder.
        else:
            self.play_first_audio_in_folder()

    def trigger_play_button(self):
        '''Trigger function for the play button.'''

        # If no audio is playing, attempt to play something.
        if self.active_audio_name_label.text() == "No Audio Playing":
            self.play_first_audio()
        
        # If audio is playing, pause or unpause it.
        else:
            if self.paused:
                pygame.mixer.music.unpause()
                self.paused = False
                self.play_button.setText("||")

            else:
                pygame.mixer.music.pause()
                self.play_button.setText("▶")
                self.paused = True

    def play_next_audio_file(self):
        '''Plays the next audio file in the folder.'''

        # Get the item index of the audio being played.
        active_index = self.get_active_audio_index()
        if active_index != -1:

            # Play and select the next audio file in the folder.
            next_audio_item = self.file_browser.topLevelItem(active_index + 1)
            if next_audio_item:
                self.file_browser.clearSelection()
                next_audio_item.setSelected(True)
                audio_path = self.get_file_browser_item_path(next_audio_item)
                self.play_audio(audio_path)
                return
            
            # If the last audio file in the folder was being played, play the first audio file in the folder.
            else:
                self.play_first_audio_in_folder()
                return

        # If the index of the audio being played can't be determined,
        # attempt to play something from the current directory.
        else:
            self.play_first_audio()

    def play_previous_audio_file(self):
        '''Plays the previous audio file in the folder.'''

        # Get the item index of the audio being played.
        active_index = self.get_active_audio_index()
        if active_index != -1:

            # Play and select the next audio file in the folder.
            prev_audio_item = self.file_browser.topLevelItem(active_index - 1)
            if prev_audio_item:

                # If the previous item was a folder, play the last audio file in the directory.
                if prev_audio_item.text(1) == "Folder":
                    last_audio_item = self.file_browser.topLevelItem(self.file_browser.topLevelItemCount() - 1)
                    self.file_browser.clearSelection()
                    last_audio_item.setSelected(True)
                    audio_path = self.get_file_browser_item_path(last_audio_item)
                    self.play_audio(audio_path)
                    return

                # Otherwise play the previous audio file.
                else:
                    self.file_browser.clearSelection()
                    prev_audio_item.setSelected(True)
                    audio_path = self.get_file_browser_item_path(prev_audio_item)
                    self.play_audio(audio_path)
                    return
            
            # If the last audio file in the folder was being played, play the first audio file in the folder.
            else:
                self.play_first_audio_in_folder()
                return

        # If the index of the audio being played can't be determined,
        # attempt to play something from the current directory.
        else:
            self.play_first_audio()

    def rename_file(self):
        '''Renames the selected file or folder.'''
        current_path = self.folder_path_field.text()
        selected_items = self.file_browser.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Rename", "No file or folder selected.")
            return

        # Prompt the user to enter a new name for the file or folder path.
        item = selected_items[0]
        old_name = item.text(0)
        old_path = os.path.join(current_path, old_name)
        
        new_name, ok = QInputDialog.getText(self, "Rename", "Enter new name:", text=old_name)
        if not ok or not new_name.strip():
            return
        
        new_path = os.path.join(current_path, new_name)
        if os.path.exists(new_path):
            QMessageBox.warning(self, "Rename", "A file or folder with this name already exists.")
            return
        
        # Attempt to rename the file.
        try:
            file_extension = item.text(1)
            old_path = os.path.splitext(old_path)[0] + file_extension
            new_path = os.path.splitext(new_path)[0] + file_extension
            os.rename(old_path, new_path)
            self.load_files()
        except Exception as e:
            QMessageBox.critical(self, "Rename Error", f"Error renaming {old_name}: {e}")

    def cut_files(self):
        '''Deletes all selected items from the current location, but stores them in memory for pasting.'''
        self.clipboard = []
        self.cut_mode = True
        selected_items = self.file_browser.selectedItems()
        if selected_items:
            for item in selected_items:
                audio_path = self.get_file_browser_item_path(item)
                self.clipboard.append(audio_path)
        print("Cut items stored in clipboard:", self.clipboard)
    
    def copy_files(self):
        '''Copies all selected items into memory.'''
        self.clipboard = []
        self.cut_mode = False
        selected_items = self.file_browser.selectedItems()
        if selected_items:
            for item in selected_items:
                audio_path = self.get_file_browser_item_path(item)
                self.clipboard.append(audio_path)
        print("Copied items stored in clipboard:", self.clipboard)
    
    def paste_files(self):
        '''Pastes all selected items into the selected folder or current folder.'''
        # If the clipboard is empty, do nothing.
        if not self.clipboard:
            QMessageBox.warning(self, "Paste", "Clipboard is empty.")
            return

        current_path = self.folder_path_field.text()

        # Check if the user is selecting a folder.
        selected_items = self.file_browser.selectedItems()
        destination_path = ""
        for item in selected_items:
            item_type = item.text(1)
            if item_type == "Folder":
                folder_name = item.text(0)
                destination_path = os.path.join(current_path, folder_name)
                break

        # If the user is selecting a folder, paste into that folder.
        if destination_path == "":
            destination_path = current_path

        # Paste all of the items in clipboard memory.
        for item_path in self.clipboard:
            item_name = os.path.basename(item_path)
            new_path = os.path.join(destination_path, item_name)

            # If the file exists where the user is pasting the files,
            # add '_copy' to the end of the file name.
            if os.path.exists(new_path):
                base, ext = os.path.splitext(item_name)
                counter = 1
                while os.path.exists(new_path):
                    new_path = os.path.join(destination_path, f"{base}_copy{counter}{ext}")
                    counter += 1

            try:
                if os.path.isdir(item_path):
                    if self.cut_mode:
                        shutil.move(item_path, new_path)
                    else:
                        shutil.copytree(item_path, new_path)
                else:
                    if self.cut_mode:
                        shutil.move(item_path, new_path)
                    else:
                        shutil.copy2(item_path, new_path)

            except Exception as e:
                QMessageBox.critical(self, "Paste Error", f"Error pasting {item_name}: {e}")

        # Clear the clipboard if the user cut files.
        if self.cut_mode:
            self.clipboard = []
            self.cut_mode = False

        # Update files in the current directory.
        self.load_files()

    def delete_files(self):
        '''Deletes all selected files and folders.'''

        selected_items = self.file_browser.selectedItems()
        if selected_items:
            for item in selected_items:
                item_name = item.text(0)
                item_path = self.get_file_browser_item_path(item)

                reply = QMessageBox.question(self, "Delete", f"Are you sure you want to delete '{item_name}'?", QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.Yes:

                    # Delete folders.
                    if os.path.isdir(item_path):
                        for foldername, subfolders, filenames in os.walk(item_path, topdown=False):
                            for filename in filenames:
                                file_path = os.path.join(foldername, filename)
                                try:
                                    os.remove(file_path)
                                    self.log(f"Deleted: {file_path}")

                                except Exception as e:
                                    self.log(f"Error deleting {file_path}: {e}")

                            for subfolder in subfolders:
                                subfolder_path = os.path.join(foldername, subfolder)
                                try:
                                    os.rmdir(subfolder_path)
                                    self.log(f"Deleted subfolder path: {subfolder_path}")
                                except Exception as e:
                                    self.log(f"Error deleting folder: {subfolder_path}: {e}")
                                
                        os.rmdir(item_path)
                        self.log(f"Deleted folder: {item_path}")

                    # Delete files.
                    else:
                        os.remove(item_path)
                        self.log(f"Deleted audio file: {item_path}")
                    
                # Do nothing if the user doesn't want to delete files.
                else:
                    return

        # Update files in the current directory.
        self.load_files()      

    def create_new_folder(self):
        '''Creates a new file folder in the current directory.'''
        current_path = self.folder_path_field.text()
        folder_name, ok = QInputDialog.getText(self, "New Folder", "Enter folder name:")
        if ok and folder_name:
            os.mkdir(os.path.join(current_path, folder_name))
            self.load_files()

    def sort_files(self):
        '''Sorts files in alphabetical order.'''
        self.log("Sorted files.")
        self.load_files()
    
    def shuffle_audio_files(self):
        '''Shuffles the sorting for all audio files in the current directory.'''
        audio_items = []
        for i in range(self.file_browser.topLevelItemCount() - 1, -1, -1):
            item = self.file_browser.topLevelItem(i)
            if item and item.text(1) != "Folder":
                audio_items.append(self.file_browser.takeTopLevelItem(i))
        
        random.shuffle(audio_items)
        for item in audio_items:
            self.file_browser.addTopLevelItem(item)

        # If audio was being played before shuffling files, re-select it.
        for i in range(self.file_browser.topLevelItemCount()):
            item = self.file_browser.topLevelItem(i)
            audio_name = item.text(0)
            if audio_name == self.active_audio_name_label.text():
                self.file_browser.clearSelection()
                item.setSelected(True)
        
        # Clear focus to avoid showing focus highlighting.
        self.file_browser.clearFocus()

    def timer_trigger(self):
        '''Triggers updates for user interface every few miliseconds.'''

        # Update the seek slider position, excluding when it's not playing music, or manually grabbed.
        if pygame.mixer.music.get_busy() is True:
            if self.slider_grabbed is False:
                self.update_seek_slider_position()

        # If the song has ended, play the next song.
        else:
            if self.audio_length_label.text() != "0:00":
                if self.current_playtime_label.text() == self.audio_length_label.text():

                    # If looping is enabled, restart the same song.
                    if self.loop_audio_action.isChecked():
                        pygame.mixer.music.play(start=0)
                        self.current_playtime_label.setText("0:00")
                        self.paused = False
                        self.last_seek_position = 0
                        self.seek_slider.setDisabled(False)
                    
                    # Otherwise play the next audio file.
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
        self.log("User grabbed the seek slider.")

    def seek_slider_released(self):
        '''Triggers when the seek slider is released.'''
        self.slider_grabbed = False
        self.log("User released seek slider.")

        seek_time = self.seek_slider.value()
        self.log(f"User seeked to: {seek_time}")

        pygame.mixer.music.pause()
        pygame.mixer.music.play(start=seek_time)

        self.last_seek_position = seek_time
        self.update_seek_slider_position()


    #------------------------------ Helper Functions ------------------------------#


    def log(self, message, error=False):
        '''Debug logging operation that includes the current time in the output.'''
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        error_tag = "[ERROR]" if error else ""
        print(f"[{current_time}]{error_tag}: {message}")

    def get_resource_path(self, relative_path):
        ''' Get the absolute path to a resource, works for pyinstaller bundling. '''
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.abspath("."), relative_path)

    def get_file_browser_item_path(self, item):
        '''Returns the path for an item in the file browser (QTreeWidget).'''
        current_path = self.folder_path_field.text()
        file_name = item.text(0)
        file_type = item.text(1)

        # Create the file path for audio files.
        if file_type != "Folder":
            file_path = os.path.join(current_path, file_name) + file_type
        
        # Create the file path for folders.
        else:
            file_path = os.path.join(current_path, file_name)
        
        # Return the correct file path.
        return file_path

    def get_active_audio_index(self):
        '''Returns the index in the file browser for the active audio.'''
        for i in range(self.file_browser.topLevelItemCount()):
            item = self.file_browser.topLevelItem(i)
            audio_name = item.text(0)
            if audio_name == self.active_audio_name_label.text():
                self.log(f"Active audio index: {i}")
                return i
            
        # Return -1 if the audio being played can't be found.
        self.log("Index for active audio not found.")
        return -1
    
    def time_to_seconds(self, time):
        '''Converts time in mm:ss format to seconds.'''
        minutes, seconds = map(int, time.split(":"))
        return minutes * 60 + seconds

    def format_time(self, seconds):
        '''Formats song time into minutes and seconds.'''
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes}:{seconds:02d}"


#------------------------------ Application Start ------------------------------#


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AudioPlayer()
    window.show()
    sys.exit(app.exec_())
