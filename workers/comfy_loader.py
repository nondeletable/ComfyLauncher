from PyQt6.QtCore import QObject, pyqtSignal
import time

from launcher import ensure_comfyui_running, get_comfy_process, is_port_open
from config import COMFYUI_PORT, STARTUP_STALL_TIMEOUT
from utils.startup_watch import ProcessActivity, StartupState, decide


class ComfyLoaderWorker(QObject):
    # ── Signals ─────────────────────────────
    started = pyqtSignal()
    ready = pyqtSignal()
    timeout = pyqtSignal()
    exited = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, comfy_path: str):
        super().__init__()
        self.comfy_path = comfy_path
        self._running = True

    def stop(self):
        """Allows you to gently stop the worker if necessary."""
        self._running = False

    def run(self):
        """
        Main logic:
        - ComfyUI start
        - wait for the port while the process shows signs of life
        - result signal
        """
        try:
            self.started.emit()  # type: ignore

            # 1️⃣ Launch ComfyUI (if it's already running, the function will figure it out automatically)
            ensure_comfyui_running(self.comfy_path)

            # 2️⃣ We're waiting for the server to go up. No fixed deadline: only a
            # dead process or one that stopped doing anything ends the wait.
            proc, wrapped = get_comfy_process()
            activity = ProcessActivity(proc.pid, wrapped) if proc else None
            last_active = time.monotonic()

            while self._running:
                port_open = is_port_open(COMFYUI_PORT)

                alive = None
                if activity:
                    alive, active = activity.sample()
                    if active:
                        last_active = time.monotonic()

                state = decide(
                    port_open,
                    alive,
                    time.monotonic() - last_active,
                    STARTUP_STALL_TIMEOUT,
                )

                if state is StartupState.READY:
                    self.ready.emit()  # type: ignore
                    return
                if state is StartupState.EXITED:
                    self.exited.emit()  # type: ignore
                    return
                if state is StartupState.STALLED:
                    self.timeout.emit()  # type: ignore
                    return

                time.sleep(0.3)

        except Exception as e:
            self.error.emit(str(e))  # type: ignore
