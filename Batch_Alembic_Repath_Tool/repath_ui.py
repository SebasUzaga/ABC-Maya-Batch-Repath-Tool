# repath_ui.py
# Standalone UI to launch a mayapy-driven batch repath script and stream logs

import os
import sys
import json
from pathlib import Path

qt = None
try:
    from PySide6 import QtCore, QtWidgets, QtGui
    qt = 'PySide6'
except Exception:
    try:
        from PySide2 import QtCore, QtWidgets, QtGui
        qt = 'PySide2'
    except Exception:
        from PyQt5 import QtCore, QtWidgets, QtGui 
        qt = 'PyQt5'

CONFIG_PATH = Path.home() / ".repath_ui_config.json"
APP_DIR = Path(__file__).parent  

class PathPicker(QtWidgets.QWidget):
    def __init__(self, label: str, mode: str = "file", parent=None):
        super().__init__(parent)
        self.mode = mode  
        self.le = QtWidgets.QLineEdit()
        self.btn = QtWidgets.QPushButton("Browse…")
        self.btn.clicked.connect(self.browse)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(self.le)
        layout.addWidget(self.btn)
        self.setToolTip(label)

    def browse(self):
        if self.mode == "dir":
            path = QtWidgets.QFileDialog.getExistingDirectory(
                self, "Select Folder", self.le.text() or str(Path.home()))
        elif self.mode == "save":
            path, _ = QtWidgets.QFileDialog.getSaveFileName(
                self, "Save Report File", self.le.text() or str(Path.home()/ "report.txt"),
                "Text files (*.txt);;All Files (*)")        
        else:
            path, _ = QtWidgets.QFileDialog.getOpenFileName(
                self, "Select File", self.le.text() or str(Path.home()))
        if path:
            self.le.setText(path)

    def text(self) -> str:
        return self.le.text().strip()

    def setText(self, t: str):
        self.le.setText(t)

class Launcher(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Batch Alembic Repath – Launcher")
        self.resize(820, 600)
        self.proc = None

       
        icon_file = APP_DIR / "icon.png"
        if icon_file.exists():
            self.setWindowIcon(QtGui.QIcon(str(icon_file)))

    
        self.scenes = PathPicker("Scenes Folder", mode="dir")
        self.new_alembics = PathPicker("New Alembics Folder", mode="dir")
        self.mayapy = PathPicker("mayapy Executable", mode="file")
        self.script = PathPicker("Repath Script (Python)", mode="file")
        self.report = PathPicker("Report File (optional)", mode="save")

     
        self.overwrite_cb = QtWidgets.QCheckBox("Overwrite original scenes")
        self.overwrite_cb.setToolTip(
            "If checked, modifies and saves scenes in-place.\n"
            "If unchecked, creates *_fixed copies."
        )

      
        self.log = QtWidgets.QTextEdit()
        self.log.setReadOnly(True)
        self.log.setPlaceholderText("Logs will appear here…")

      
        self.run_btn = QtWidgets.QPushButton("Run")
        self.stop_btn = QtWidgets.QPushButton("Stop")
        self.stop_btn.setEnabled(False)

      
        run_icon = APP_DIR / "run.png"
        stop_icon = APP_DIR / "stop.png"
        if run_icon.exists():
            self.run_btn.setIcon(QtGui.QIcon(str(run_icon)))
        if stop_icon.exists():
            self.stop_btn.setIcon(QtGui.QIcon(str(stop_icon)))

        self.run_btn.clicked.connect(self.on_run)
        self.stop_btn.clicked.connect(self.on_stop)

    
        form = QtWidgets.QFormLayout()
        form.addRow("Scenes folder:", self.scenes)
        form.addRow("New Alembics folder:", self.new_alembics)
        form.addRow("mayapy path:", self.mayapy)
        form.addRow("Script path:", self.script)
        form.addRow("Report file:", self.report)
        form.addRow("", self.overwrite_cb)

        btns = QtWidgets.QHBoxLayout()
        btns.addStretch(1)
        btns.addWidget(self.run_btn)
        btns.addWidget(self.stop_btn)

        main = QtWidgets.QVBoxLayout(self)
        main.addLayout(form)
        main.addLayout(btns)
        main.addWidget(self.log, 1)

       
        self.load_config()
        self.apply_defaults()
        self.append_log(f"Qt backend: {qt}")

    def apply_defaults(self):
        """If fields are empty, set them to defaults in app folder."""
        if not self.script.text():
            default_script = APP_DIR / "repath.py"
            if default_script.exists():
                self.script.setText(str(default_script))

    
    def load_config(self):
        if CONFIG_PATH.exists():
            try:
                data = json.loads(CONFIG_PATH.read_text())
                self.scenes.setText(data.get("scenes", ""))
                self.new_alembics.setText(data.get("new_alembics", ""))
                self.mayapy.setText(data.get("mayapy", ""))
                self.script.setText(data.get("script", ""))
                self.report.setText(data.get("report", ""))
                self.overwrite_cb.setChecked(data.get("overwrite", False))
            except Exception as e:
                self.append_log(f"[WARN] Failed to load config: {e}")

    def save_config(self):
        data = {
            "scenes": self.scenes.text(),
            "new_alembics": self.new_alembics.text(),
            "mayapy": self.mayapy.text(),
            "script": self.script.text(),
            "report": self.report.text(),
            "overwrite": self.overwrite_cb.isChecked(),
        }
        try:
            CONFIG_PATH.write_text(json.dumps(data, indent=2))
        except Exception as e:
            self.append_log(f"[WARN] Failed to save config: {e}")

    
    def append_log(self, text: str):
        self.log.append(text)
        self.log.verticalScrollBar().setValue(self.log.verticalScrollBar().maximum())

    
    def validate_inputs(self) -> bool:
        ok = True
        scenes = self.scenes.text()
        new_alembics = self.new_alembics.text()
        mayapy = self.mayapy.text()
        script = self.script.text()

        def exists_dir(p, label):
            if not p or not os.path.isdir(p):
                self.append_log(f"[ERROR] {label} is missing or not a folder: {p}")
                return False
            return True

        def exists_file(p, label):
            if not p or not os.path.isfile(p):
                self.append_log(f"[ERROR] {label} is missing or not a file: {p}")
                return False
            return True

        ok &= exists_dir(scenes, "Scenes folder")
        ok &= exists_dir(new_alembics, "New Alembics folder")
        ok &= exists_file(mayapy, "mayapy path")
        ok &= exists_file(script, "Script path")
        return bool(ok)

    
    def on_run(self):
        if self.proc is not None:
            self.append_log("[WARN] A process is already running.")
            return
        if not self.validate_inputs():
            return

        self.save_config()

        mayapy = self.mayapy.text()
        script = self.script.text()
        scenes = self.scenes.text()
        new_alembics = self.new_alembics.text()
        report = self.report.text()
        overwrite = self.overwrite_cb.isChecked()

        
        args = [script, "--scenes", scenes, "--new", new_alembics]
        if overwrite:
            args.append("--overwrite")
        if report:
            args += ["--report", report]

        self.append_log("\n[RUN] Launching mayapy with:")
        self.append_log(f"      {mayapy} {' '.join(a if ' ' not in a else repr(a) for a in args)}")

        self.proc = QtCore.QProcess(self)
        self.proc.setProcessChannelMode(QtCore.QProcess.MergedChannels)
        self.proc.readyReadStandardOutput.connect(self.on_ready_read)
        self.proc.readyReadStandardError.connect(self.on_ready_read)
        self.proc.finished.connect(self.on_finished)

        self.proc.start(mayapy, args)
        started = self.proc.waitForStarted(3000)
        if not started:
            self.append_log("[ERROR] Failed to start mayapy. Check the path and permissions.")
            self.proc = None
            return

        self.run_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

    def on_stop(self):
        if self.proc is None:
            return
        self.append_log("[STOP] Terminating process…")
        self.proc.terminate()
        if not self.proc.waitForFinished(3000):
            self.append_log("[STOP] Forcing kill…")
            self.proc.kill()

    def on_ready_read(self):
        if not self.proc:
            return
        data = bytes(self.proc.readAll())
        try:
            text = data.decode(errors='replace')
        except Exception:
            text = str(data)
        if text:
            text = text.replace("\r\n", "\n")
            self.append_log(text)

    def on_finished(self, code: int, status: QtCore.QProcess.ExitStatus):
        if status == QtCore.QProcess.CrashExit:
            self.append_log(f"[DONE] Process crashed (code {code}).")
        else:
            self.append_log(f"[DONE] Process finished with code {code}.")
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.proc = None

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = Launcher()
    w.show()
    sys.exit(app.exec())


