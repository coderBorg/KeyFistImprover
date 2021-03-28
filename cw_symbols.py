"""
Code to process CW (Morse) symbols. Inputs will include a numpy array of shape (n, 2). input[:, 0] will be time values
and input[:, 1] values will indicate dot or dash with dot represented by value 0
and dash represented by value 1. Inputs will also include some timing info such as time width of:
dot
dash
space
character space
word space
Outputs will include decoded message text
"""
import numpy as np
import json
from statistics import mean

TO_ALPHA = {'._': 'A', '_...': 'B', '_._.': 'C', '_..': 'D', '.': 'E', '.._.': 'F', '__.': 'G',
            '....': 'H', '..': 'I', '.___': 'J', '_._': 'K', '._..': 'L', '__': 'M', '_.': 'N',
            '___': 'O', '.__.': 'P', '__._': 'Q', '._.': 'R', '...': 'S', '_': 'T', '.._': 'U',
            '..._': 'V', '.__': 'W', '_.._': 'X', '_.__': 'Y', '__..': 'Z',
            '.____': '1', '..___': '2', '...__': '3', '...._': '4', '.....': '5',
            '_....': '6', '__...': '7', '___..': '8', '____.': '9', '_____': '0',
            '_.._.': '/', '__..__': ',', '..__..': '?', '._._._': '.', '..._._': '*', '._._.': '+', '_..._': '='}


class MessageSymbols:
    def __init__(self, dot=None, dash=None, space=None, ch_space=None, w_space=None, symbols=None):
        self.dash = dash
        self.dot = dot
        self.space = space
        self.ch_space = ch_space
        self.w_space = w_space
        self.symbols = symbols

    def sym_2_str(self):
        """
        Parse symbols to string where we use '._cw' for dot, dash, character space,
        and word space. If this function returns a string of '.._.c_...w___c__' it would later be
        decoded into "FB OM" (Ham radio abbreviations meaning "Fine Business Old Man")
        :return:
        """

        dot_dot = self.dot + self.space
        mixed = self.dot/2 + self.space + self.dash/2
        dash_dash = self.dash + self.space
        ch_dot_dot = self.dot + self.ch_space
        ch_mixed = self.dot/2 + self.ch_space + self.dash/2
        ch_dash_dash = self.dash + self.ch_space
        w_dot_dot = self.dot + self.w_space
        w_mixed = self.dot / 2 + self.w_space + self.dash / 2
        w_dash_dash = self.dash + self.w_space
        spacings = {(0, 0): [dot_dot, ch_dot_dot, w_dot_dot],
                    (0, 1): [mixed, ch_mixed, w_mixed],
                    (1, 0): [mixed, ch_mixed, w_mixed],
                    (1, 1): [dash_dash, ch_dash_dash, w_dash_dash]}
        thresh = {k: [mean([v[0], v[1]]), mean([v[1], v[2]])] for k, v in spacings.items()}

        str_sym = {0: '.', 1: '_'}
        # print(thresh)

        if len(self.symbols) == 0:
            s =  ''
        else:
            s = str_sym[self.symbols[0, 1]]
            for i in range(len(self.symbols) - 1):
                t1, v1 = self.symbols[i]
                t2, v2 = self.symbols[i + 1]

                th1, th2 = thresh[(v1, v2)]
                delta = t2 - t1
                if delta <= th1:
                    s += str_sym[v2]
                elif th1 < delta <= th2:
                    s += 'c' + str_sym[v2]
                else:
                    s += 'w' + str_sym[v2]
        return s

    def str_to_alpha(self, s):
        text = ''
        w = ''
        c = ''
        for sym in s:
            if sym in ['_', '.']:
                c += sym
            elif sym == 'c':
                if c in TO_ALPHA.keys():
                    w += TO_ALPHA[c]
                else:
                    w += c
                c = ''
            elif sym == 'w':
                if c in TO_ALPHA.keys():
                    w += TO_ALPHA[c]
                else:
                    w += c
                text += ' ' + w
                w = ''
                c = ''
        if c in TO_ALPHA.keys():
            w += TO_ALPHA[c]
        else:
            w += c
        text += ' ' + w


        return text

    def to_json(self):
        d = self.__dict__.copy()
        d['symbols'] = self.symbols.tolist()
        return json.dumps(d)

    @classmethod
    def fr_pks(cls, dot, dash, space, ch_space, w_space, t_dots, t_dashes):
        """
        Alternate constructor. Creates time sequence of symbols.
        :param dot:
        :param dash:
        :param space:
        :param ch_space:
        :param w_space:
        :param t_dots:
        :param t_dashes:
        :return: MessageSymbols Object with symbols member being numpy array of shape (n, 2) where a[:, 0] is time
         values and a[:, 1] values represent dots and dashes (0 for dot and 1 for dash)
        """
        dots = np.stack((t_dots, np.zeros(len(t_dots))), axis=-1)
        dashes = np.stack((t_dashes, np.ones(len(t_dashes))), axis=-1)
        symbols = np.concatenate((dots, dashes), axis=0)

        # Sort "table" by time "column
        symbols = symbols[symbols[:, 0].argsort()]

        return cls(dot, dash, space, ch_space, w_space, symbols)

    @classmethod
    def fr_json(cls, s):
        obj = json.loads(s)
        obj['symbols'] = np.array(obj['symbols'])
        sym_obj = cls()
        sym_obj.__dict__ = obj
        return sym_obj
