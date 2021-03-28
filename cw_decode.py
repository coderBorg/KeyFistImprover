"""
CW (Morse) decoding meant for practicing sending. Input signal should be the output of
a practice oscillator (audio tone when key is closed and nothing when key is open.
Speed set by user
"""

import dsp
import cw_symbols as cws


class Decoder:
    """
    Decode morse code from "audio" such as the output of a practice oscillator.
    """

    def __init__(self, speed=20, dot=None, dash=None):
        """
        Constructor
        :param speed: speed in wpm
        :param dot: time length of dot (seconds)
        """
        if speed is not None and dot is not None:
            raise ValueError("Cannot specify both speed and dot width")
        elif speed is not None:
            self.dot = 60 / (50 * speed)
        else:
            self.dot = dot

        if dash is not None:
            self.dash = dash
        else:
            self.dash = 3 * self.dot
        self.space = self.dot
        self.ch_space = 3 * self.dot
        self.w_space = 7 * self.dot

        self.fs = 44100  # Sample rate
        self.fc = 10  # LPF corner frequency
        self.lpf = dsp.FilterLowPass(self.fc, sample_rate=self.fs)
        self.bin_thresh = 0.043

        self.correlator = dsp.DotDashCorr(self.dot, self.dash, self.space, self.fs)

        self.corr_pk_th = 0.6  # Peak threshold for correlation peaks
        self.pk_find = dsp.GetPeaks(self.corr_pk_th, self.fs)

        # Variables for saving signals at intermediate steps
        self.sig = None
        self.binary = None
        self.sym_str = None
        self.text = None

    def update_speed_wpm(self, speed):
        self.dot = 60 / (50 * speed)
        self.dash = 3 * self.dot
        self.space = self.dot
        self.ch_space = 3 * self.dot
        self.w_space = 7 * self.dot
        self.correlator = dsp.DotDashCorr(self.dot, self.dash, self.space, self.fs)

    def decode(self, sig):
        self.sig = dsp.reshape(sig)
        self.binary = dsp.binarize(self.lpf.filter(dsp.full_wave_rectify(self.sig)), self.bin_thresh)
        dots = self.pk_find.compute_peaks(self.correlator.corr_dot(self.binary))
        dashes = self.pk_find.compute_peaks(self.correlator.corr_dash(self.binary))

        # Compute numpy array representing dots, dashes, and their time of occurance
        symbols = cws.MessageSymbols.fr_pks(self.dot, self.dash, self.space, self.ch_space, self.w_space, dots[:, 0],
                                            dashes[:, 0])

        # Convert the numpy array to string built of characters
        # "." = dot, "_" = dash, "c" = character space, "w" = word space
        self.sym_str = symbols.sym_2_str()

        # Decode string of morse symbols to string of text
        self.text = symbols.str_to_alpha(self.sym_str)
        return self.text
