from PyQt5.QtCore import QObject, pyqtSignal, QThreadPool
from gui.connection import GetConnectionWorker
from gui.default_config import default_config
from omegaconf import OmegaConf

class GPTSovitsCore(QObject):
    updateConnectionStatus = pyqtSignal(str)
    updateHost = pyqtSignal(str, bool)
    connectionBusy = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.host = None
        self.is_local : bool = False
        self.thread_pool = QThreadPool()
        self.cfg = OmegaConf.create(default_config)
        
    def try_connect(self,
        host : str):
        worker = GetConnectionWorker(host)
        def lam1(h):
            self.host = h
            self.is_local = ('127.0.0.1' in h or 'localhost' in h)
            self.updateHost.emit(self.host, self.is_local)

        worker.emitters.updateHost.connect(lam1)
        worker.emitters.updateStatus.connect(lambda status: 
        self.updateConnectionStatus.emit(status))
        worker.emitters.isBusy.connect(self.connectionBusy)

        self.thread_pool.start(worker)