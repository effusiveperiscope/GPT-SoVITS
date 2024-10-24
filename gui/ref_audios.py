from PyQt5.QtWidgets import (
    QGroupBox, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QCheckBox, QPushButton, QFrame, QHBoxLayout,
    QLabel, QLineEdit, QComboBox)
from PyQt5.QtCore import pyqtSignal, Qt, QSize
from gui.core import GPTSovitsCore
from gui.database import GPTSovitsDatabase, CLIENT_DB_FILE, RefAudio
from gui.util import ppp_parse, AUDIO_EXTENSIONS
from gui.audio_preview import AudioPreviewWidget
from gui.file_button import FileButton
from pathlib import Path
from functools import partial
from typing import Optional
import soundfile as sf
import hashlib
import os

class RefAudiosContext:
    def __init__(self, core : GPTSovitsCore):
        self.core = core
        self.database = GPTSovitsDatabase(db_file=CLIENT_DB_FILE)
        
        self.autoload_from_dir()
        
    def autoload_from_dir(self):
        cfg = self.core.cfg
        os.makedirs(cfg['ref_audios_dir'], exist_ok=True)
        ref_audios_dir = Path(cfg['ref_audios_dir'])
        i = len(self)
        for path in ref_audios_dir.rglob('*'):
            if path.suffix.lower() in AUDIO_EXTENSIONS:
                path = path.absolute()
                self.add_ref_audio(path, override_list_position=i)
                i = i + 1

    def get_ref_audios(self):
        return self.database.list_ref_audio()
    
    def __len__(self):
        return RefAudio.select().count()
    
    def add_ref_audio(
        self,
        local_filepath: Path,
        override_list_position: Optional[int] = None):
        assert local_filepath.exists()
        
        sha256_hash = hashlib.sha256()
        with open(local_filepath, 'rb') as audio_file:
            for byte_block in iter(lambda: audio_file.read(4096), b""):
                sha256_hash.update(byte_block)
                
        # If this is a PPP-style audio name,
        # we can try roughly parsing it for extra data
        ppp_meta = ppp_parse(str(local_filepath))
        character = None 
        utterance = None
        if ppp_meta is not None:
            character = ppp_meta['char']
            utterance = ppp_meta['transcr']
            
        list_position = None
        if override_list_position is not None:
            list_position = list_position
        else:
            list_position = len(self)
                
        # Append to end of list
        self.database.update_with_ref_audio(
            audio_hash=sha256_hash.hexdigest(),
            local_filepath=str(local_filepath),
            character=character,
            utterance=utterance,
            list_position=list_position)

    def update_ref_audio(
        self,
        audio_hash: str,
        local_filepath: str = None,
        utterance: str = None,
        character: str = None):
        ref_audio = self.database.get_ref_audio(
            audio_hash)
        if local_filepath is not None:
            ref_audio.local_filepath = utterance
        if utterance is not None:
            ref_audio.utterance = utterance
        if character is not None:
            ref_audio.character = character
        
    # this won't handle uploading; that only happens once we actually
    # need to send TTS requests
    # or will it? maybe it's better to passively upload reference audios in
    # idle time?

class RefAudiosFrame(QGroupBox):
    shouldBuildTable = pyqtSignal()
    def __init__(self, core : GPTSovitsCore):
        super().__init__(title="Reference Audios")
        self.context = RefAudiosContext(core)
        self.lay = QVBoxLayout(self)
        self.table = None
        
        self.hashesCheckedSet : set[str] = set()
        self.hashToPathMap = dict()
        
        self.shouldBuildTable.connect(self.build_table)
        
        #pb = QPushButton("Rebuild table")
        #pb.clicked.connect(self.shouldBuildTable)
        #self.lay.addWidget(pb)
        
        bf = QFrame()
        bflay = QHBoxLayout(bf)

        self.add_ref_button = FileButton(
            label="Add reference audio",
            dialog_filter = "All Audio Files (*.wav *.mp3 *.ogg *.flac *.aac)"
        )
        bflay.addWidget(self.add_ref_button)
        self.add_ref_button.filesSelected.connect(
            self.add_selected_ref_audios            
        )
        self.delete_button = QPushButton("Delete highlighted rows (n)")
        bflay.addWidget(self.delete_button)
        
        bf2 = QFrame()
        bflay = QHBoxLayout(bf2)
        bflay.addWidget(QLabel("Filter by character"))
        bflay.addWidget(QComboBox())
        bflay.addWidget(QLabel("Filter by utterance"))
        bflay.addWidget(QLineEdit())

        tbf = QFrame()
        self.tbflay = QVBoxLayout(tbf)
        self.lay.addWidget(tbf)
        self.lay.addWidget(bf)
        self.lay.addWidget(bf2)

        self.build_table()
        
    def update_hashes_set(self, 
        check_box: QCheckBox,
        audio_hash: str):
        if check_box.isChecked():
            self.hashesCheckedSet.add(audio_hash)
        else:
            self.hashesCheckedSet.remove(audio_hash)
            
    def add_selected_ref_audios(self, 
        ras : list[str]):
        if not len(ras):
            return
        for ra in ras:
            ra : str
            self.context.add_ref_audio(Path(ra))
        self.shouldBuildTable.emit()
        
    def build_table(self):
        if isinstance(self.table, QTableWidget):
            self.table.deleteLater()
            del self.table
        self.table = QTableWidget()
        table_cols = [
            'Filepath', 'Character', 'Utterance', 'Hash', 'Select', 'Play']

        self.table.setColumnCount(len(table_cols))
        self.table.setHorizontalHeaderLabels(table_cols)
        self.table.setMinimumWidth(900)
        self.table.setMinimumHeight(400)
        
        self.table.setColumnWidth(0, 80)
        self.table.setColumnWidth(1, 120)
        self.table.setColumnWidth(3, 120)
        self.table.setColumnWidth(4, 60)
        self.table.setColumnWidth(5, 60)
        
        self.table.horizontalHeader().setSectionResizeMode(0,
            QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(1,
            QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(2,
            QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3,
            QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(4,
            QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(5,
            QHeaderView.Fixed)

        ras : list[RefAudio] = self.context.get_ref_audios()
        ras.sort(reverse=True, # So most recent files appear at top
            key=lambda ra:
            (ra.list_position if ra.list_position is not None else 0))
        self.hashToPathMap = {
            ra.audio_hash : ra.local_filepath for ra in ras
        }
        self.table.setRowCount(len(ras))
        for i,ra in enumerate(ras):
            ra : RefAudio
            filepath_item = QTableWidgetItem(ra.local_filepath)
            filepath_item.setFlags(filepath_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(
                i, 0, filepath_item)
            self.table.setItem(
                i, 1, QTableWidgetItem(ra.character))
            utterance_item = QTableWidgetItem(ra.utterance)
            #utterance_item.stateChanged
            self.table.setItem(
                i, 2, utterance_item)
            hash_item = QTableWidgetItem(ra.audio_hash[:7])
            hash_item.setFlags(hash_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(
                i, 3, hash_item)
            check_box = QCheckBox()
            if ra.audio_hash in self.hashesCheckedSet:
                check_box.setChecked(True)
            check_box.stateChanged.connect(
                partial(self.update_hashes_set,
                check_box = check_box,
                audio_hash = ra.audio_hash)
            )
            self.table.setCellWidget(i, 4, check_box)
            preview_button = AudioPreviewWidget(
                button_only=True, drag_enabled=False, pausable=False)
            preview_button.from_file(ra.local_filepath)
            self.table.setCellWidget(i, 5, preview_button)
            
        self.tbflay.addWidget(self.table)
        
    # TODO: Manipulation buttons:
    # Add from file (drag and drop)
    # Delete (should we actually delete or just set a 'delete' flag?)
    # You should be able to edit the character and text inplace
    # But not the file path or hash
    # TODO: Search buttons
    # You should also get a search/filter for utterance/character