"""
DSP functions
Input and output are numpy arrays. Signals should be shape (n,). Use reshape if needed
"""
import numpy as np
from scipy import signal


def binarize(sig, thresh, high=1, low=-1):
    """
    Use a threshold to convert signal into a resule where each value is either high or low
    :param sig:
    :param thresh:
    :param high:
    :param low:
    :return:
    """
    return np.where(sig > thresh, high, low)


class DotDashCorr:
    def __init__(self, dot_len, dash_len, btwn_len, fs, high=1, low=-1):
        self.dot_len = dot_len
        self.dash_len = dash_len
        self.btwn_len = btwn_len
        self.fs = fs
        self.high = high
        self.low = low
        self.prefix_suffix_len = (btwn_len * fs) / 2
        self.dot_sig = np.repeat([low, high, low], [self.prefix_suffix_len, dot_len * fs, self.prefix_suffix_len])
        self.dash_sig = np.repeat([low, high, low], [self.prefix_suffix_len, dash_len * fs, self.prefix_suffix_len])

    def corr_dot(self, sig):
        return signal.correlate(sig, self.dot_sig, mode='same') / len(self.dot_sig)

    def corr_dash(self, sig):
        return signal.correlate(sig, self.dash_sig, mode='same') / len(self.dash_sig)


class FilterLowPass:
    def __init__(self, corner_freq, sample_rate=44100):
        # self.order = 10
        self.order = 5
        self.pb_ripple = 3
        self.corner_freq = corner_freq
        self.fs = sample_rate
        # self.sos = signal.cheby1(self.order, self.pb_ripple, corner_freq, fs=self.fs, output='sos')
        # self.sos = signal.butter(self.order, corner_freq, fs=self.fs, output='sos')
        # self.fir = signal.firwin(40, corner_freq, fs=self.fs)
        self.fir = signal.firwin(320, corner_freq, fs=self.fs)

    def filter(self, sig):
        # return signal.sosfilt(self.sos, sig)
        return signal.lfilter(self.fir, 1, sig)


class GetPeaks:
    def __init__(self, min_height, fs):
        self.min_height = min_height
        self.fs = fs

    def compute_peaks(self, sig):
        """
        Find peaks in sig.
        :param sig:
        :return: numpy array with shape (n, 2) where peaks[:, 0] are time values and peaks[:, 1] are peak values
        """
        pk_idxs, _ = signal.find_peaks(sig, height=self.min_height)
        t = np.arange(0, len(sig)) / self.fs
        pk_vals = sig[pk_idxs]
        t_vals = t[pk_idxs]

        # Create single numpy ndarray of shape (n, 2) where t values are in peaks[:, 0
        # and peak values are in peaks[:, 1]
        peaks = np.stack((t_vals, pk_vals), axis=-1)
        return peaks


def full_wave_rectify(sig):
    return abs(sig)


def reshape(sig, ch='left'):
    """
    There are several shapes of audio signals
    sounddevice  mono recordings have shape (n, 1)
    sounddevice  stereo recordings have shape (n, 2)
    soundfile read function on mono wav file returns shape (n,)
    """
    if len(sig.shape) == 1:
        return sig
    elif sig.shape[1] == 1:
        return sig[:, 0]
    elif sig.shape[1] == 2:
        if ch == 'left':
            return sig[:, 0]
        elif ch == 'right':
            return sig[:, 1]
    else:
        return None
