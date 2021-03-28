"""
Morse decode PyQt5 app.
"""
import sys
import sounddevice as sd
import queue
import numpy as np

import matplotlib
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PyQt5 import QtCore
from PyQt5 import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QToolBar, QAction, QLabel, QVBoxLayout, QWidget
from PyQt5.QtWidgets import QSpinBox, QHBoxLayout

import dsp
import cw_decode as cwd

matplotlib.use('Qt5Agg')


class MplCanvas(FigureCanvas):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        self.axes.set_ylim(-1, 1)
        super(MplCanvas, self).__init__(fig)


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.default_font_pt = 12

        # Set up data arrays
        global fs
        self.plot_time = 10
        # self.plot_time = 5
        self.plot_size = self.plot_time * fs
        self.plot_sig = np.zeros((self.plot_size,))
        self.t = np.arange(0, self.plot_size) / fs

        # Morse decoder
        self.decoder = cwd.Decoder(speed=10)

        # Set up GUI
        ############
        self.setWindowTitle('Key Fist Analyzer')
        layout = QVBoxLayout()

        tb = QToolBar("Main Toolbar")
        self.addToolBar(tb)

        self.speed = 20
        self.lbl_placeholder = QLabel(f"Toolbar Placeholder")
        tb.addWidget(self.lbl_placeholder)

        # Controls layout
        layout_ctrls = QHBoxLayout()

        # Label for speed spinbox
        self.lbl_speed = QLabel(f"Speed (wpm):")
        f = self.lbl_speed.font()
        f.setPointSize(self.default_font_pt)
        self.lbl_speed.setFont(f)
        self.lbl_speed.setMaximumWidth(100)
        layout_ctrls.addWidget(self.lbl_speed)

        # Spinbox for speed
        spin_speed = QSpinBox()
        spin_speed.setRange(0, 80)
        spin_speed.valueChanged.connect(self.on_speed_change)
        spin_speed.setValue(self.speed)
        f = spin_speed.font()
        f.setPointSize(self.default_font_pt)
        spin_speed.setFont(f)
        layout_ctrls.addWidget(spin_speed, alignment=QtCore.Qt.AlignLeft)

        layout.addLayout(layout_ctrls)

        # Set up plot
        self.canvas = MplCanvas(self, width=5, height=4, dpi=100)
        layout.addWidget(self.canvas)
        self._plot_ref = None

        # Box for decoded text
        self.lbl_desc_decode = QLabel("Decoded text:")
        self.lbl_decode = QLabel('Decoded text here')
        f = self.lbl_decode.font()
        f.setPointSize(self.default_font_pt)
        self.lbl_desc_decode.setFont(f)
        f.setPointSize(16)
        self.lbl_decode.setFont(f)
        self.lbl_desc_decode.setMaximumHeight(30)
        self.lbl_decode.setMaximumHeight(30)
        layout.addWidget(self.lbl_desc_decode)
        layout.addWidget(self.lbl_decode)

        # Initialize plot
        self.update_plot()

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        self.show()

        # Setup a timer for calling update_plot.
        self.timer = QtCore.QTimer()
        self.timer.setInterval(200)
        # self.timer.setInterval(100)
        # self.timer.setInterval(50)
        self.timer.timeout.connect(self.update_plot)
        self.timer.start()

    def update_plot(self):
        # print('update_plot')
        global fs, audio_q
        # Update data arrays with new data from q (new data from stream)
        while True:
            try:
                data = audio_q.get_nowait()
            except queue.Empty:
                break
            shift = len(data)
            self.plot_sig = np.roll(self.plot_sig, -shift, axis=0)
            self.plot_sig[-shift:] = dsp.reshape(data)
            self.t = np.roll(self.t, -shift)
            self.t[-shift:] = (np.arange(1, shift + 1) / fs) + self.t[-shift - 1]

        if self._plot_ref is None:
            # First time we have no plot reference, so do a normal plot.
            # .plot returns a list of line <reference>s, as we're
            # only getting one we can take the first element.
            plot_refs = self.canvas.axes.plot(self.t, self.plot_sig)
            self._plot_ref = plot_refs[0]
        else:
            # We have a reference, we can use it to update the data for that line.
            # self._plot_ref.set_ydata(self.ydata)
            self._plot_ref.set_ydata(self.plot_sig)
            self._plot_ref.set_xdata(self.t)
            self.canvas.axes.set_xlim(self.t[0], self.t[-1])

        # Trigger the canvas to update and redraw.
        self.canvas.draw()

        # CW (Morse) decode of the signal
        text = self.decoder.decode(self.plot_sig)
        if text ==' ':
            t_print = 'No cw detected'
        else:
            t_print = text
        self.lbl_decode.setText(t_print)
        print(t_print)

    def on_btn_click(self, s):
        print(f'Clicked, {s}')
        if s:
            self.speed = 10
        else:
            self.speed = 30

        self.decoder.update_speed_wpm(self.speed)
        self.lbl_speed.setText(f'speed: {self.speed}')

    def on_speed_change(self, i):
        self.speed = i
        self.decoder.update_speed_wpm(self.speed)


# Queue for sharing between threads. One thread is the PyQt5 app which calls update_plot
# periodically and the other is
# sounddevice which calls audio_callback
audio_q = queue.Queue()


def audio_callback(indata, frames, time, status):
    """
    This is the callback function that will be called by sounddevice.
    """
    # print('in audio_callback')
    if status:
        print(status)

    # Make a copy of the data and place on queue
    audio_q.put(np.copy(indata), 0)  # Copy is necessary


# Set up audio input stream
fs = 44100
stream = sd.InputStream(samplerate=fs, channels=1, callback=audio_callback)
stream.start()


# Set up PyQt app
app = QApplication(sys.argv)
# app.setStyle('Fusion')
w = MainWindow()
app.exec_()
