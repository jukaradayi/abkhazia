# coding: utf-8
# Copyright 2016 Thomas Schatz, Xuan Nga Cao, Mathieu Bernard
#
# This file is part of abkhazia: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Abkhazia is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with abkahzia. If not, see <http://www.gnu.org/licenses/>.

"""Data preparation for the revised Articulation Index Corpus

Distribution of the revised AIC corpus is freely available at LDC:
https://catalog.ldc.upenn.edu/LDC2015S12. However, you need to be
signed in as an organization to add the corpus to the cart. If you are
an individual, sign up for an account but you need to click on "create
your organization" on the registration page to add your organization
and have administration privileges.
"""

import os
import re

from abkhazia.utils import list_files_with_extension
from abkhazia.prepare import AbstractPreparatorWithCMU


class AICPreparator(AbstractPreparatorWithCMU):
    """Convert the AIC corpus to the abkhazia format"""
    name = 'AIC'
    description = 'Articulation Index Corpus LSCP'
    url = 'https://catalog.ldc.upenn.edu/LDC2015S12'
    audio_format = 'flac'

    phones = {
        'a': u'ɑː',
        'xq': u'æ',
        'xa': u'ʌ',
        'c': u'ɔː',
        'xw': u'aʊ',
        'xy': u'aɪ',
        'xr': u'ɝ',
        'xe': u'ɛ',
        'e': u'eɪ',
        'xi': u'ɪ',
        'i': u'iː',
        'o': u'oʊ',
        'xo': u'ɔɪ',
        'xu': u'ʊ',
        'u': u'uː',
        'b': u'b',
        'xc': u'ʧ',
        'd': u'd',
        'xd': u'ð',
        'f': u'f',
        'g': u'g',
        'h': u'h',
        'xj': u'ʤ',
        'k': u'k',
        'l': u'l',
        'm': u'm',
        'n': u'n',
        'xg': u'ŋ',
        'p': u'p',
        'r': u'r',
        's': u's',
        'xs': u'ʃ',
        't': u't',
        'xt': u'θ',
        'v': u'v',
        'w': u'w',
        'y': u'j',
        'z': u'z',
        'xz': u'ʒ',
    }

    silences = [u"NSN"]  # SPN and SIL will be added automatically

    variants = []  # could use lexical stress variants...

    def __init__(self, input_dir, cmu_dict=None,
                 output_dir=None, verbose=False, njobs=1):
        # call the AbstractPreparator __init__
        super(AICPreparator, self).__init__(
            input_dir, cmu_dict, output_dir, verbose, njobs)

    def list_audio_files(self):
        flacs = list_files_with_extension(self.input_dir, '.flac', abspath=True)
        wavs = [os.path.basename(flac).replace('.flac', '.wav')
                for flac in flacs]
        return flacs, wavs

    def make_segment(self):
        with open(self.segments_file, 'w') as out:
            for wav in list_files_with_extension(self.wavs_dir, '.wav'):
                bname = os.path.basename(wav)
                utt_id = bname.replace('.wav', '')
                out.write(utt_id + ' ' + bname + '\n')

        self.log.debug('finished creating segments file')

    def make_speaker(self):
        with open(self.speaker_file, 'w') as out:
            for wav in list_files_with_extension(self.wavs_dir, '.wav'):
                bname = os.path.basename(wav)
                utt_id = bname.replace('.wav', '')
                speaker_id = bname.split('_')[0]
                out.write(utt_id + ' ' + speaker_id + '\n')

        self.log.debug('finished creating utt2spk file')

    def make_transcription(self):
        input_file1 = os.path.join(self.input_dir, 'data/text/normal.txt')
        input_file2 = os.path.join(self.input_dir, 'data/text/weird.txt')

        with open(self.transcription_file, 'w') as out:
            for line in open(input_file1, 'r'):
                out.write(line)

            for line in open(input_file2, 'r'):
                out.write(line)

        self.log.debug('finished creating text file')

    def make_lexicon(self):
        temp_lex = os.path.join(self.logs_dir, 'temp_lexicon_cmu.txt')
        oov = os.path.join(self.logs_dir, 'temp_OOV.txt')
        self.temp_cmu_lexicon(temp_lex, oov)
        self.make_lexicon_aux(temp_lex, oov)

        #remove the temp files
        os.remove(temp_lex)
        os.remove(oov)

    # Create temp lexicon file and temp OOVs. No transcription for the
    # words, we will use the CMU but will need to convert to the
    # symbols used in the AIC
    def temp_cmu_lexicon(self, out_temp_lex, out_oov):
        dict_word = {}
        cmu_dict = {}
        #open CMU dict
        for line in open(self.cmu_dict, "r"):
            dictionary = re.match(r"(.*)\s\s(.*)", line)
            if dictionary:
                entry = dictionary.group(1)
                phn = dictionary.group(2)
                # remove pronunciation variants
                phn = phn.replace("0", "")
                phn = phn.replace("1", "")
                phn = phn.replace("2", "")
                # create the combined dictionary
                cmu_dict[entry] = phn

        for line in open(self.transcription_file, "r"):
            matched = re.match(r"([fm0-9]+)_([ps])_(.*?)\s(.*)", line)
            if matched:
                for word in matched.group(4).upper().split():
                    dict_word[word] = (1 if word not in dict_word
                                       else dict_word[word] + 1)

        # Loop through the words in prompts by descending frequency and
        # create the lexicon by looking up in the CMU dictionary. OOVs
        # should be the sounds and will be written in temp OOV.txt
        outfile = open(out_temp_lex, "w")
        outfile2 = open(out_oov, "w")
        for word, freq in sorted(
                dict_word.items(), key=lambda kv: kv[1], reverse=True):
            if word in cmu_dict.viewkeys():
                outfile.write(word + ' ' + cmu_dict[word] + '\n')
            else:
                outfile2.write(word + '\t' + str(freq) + '\n')

        self.log.debug('finished creating temp lexicon file')

    def make_lexicon_aux(self, temp_lex, oov):
        outfile = open(self.lexicon_file, "w")

        array_phn = []
        for line in open(temp_lex, 'r'):
            # non greedy match to extract phonetic transcription
            matched = re.match(r'(.*?)\s(.*)', line)
            if matched:
                word = matched.group(1)
                word = word.lower()

                phn_trs = matched.group(2)
                # convert the CMU symbols to AIC symbols
                phn_trs = phn_trs.replace('AA', 'a')
                phn_trs = phn_trs.replace('AE', 'xq')
                phn_trs = phn_trs.replace('AH', 'xa')
                phn_trs = phn_trs.replace('AO', 'c')
                phn_trs = phn_trs.replace('AW', 'xw')
                phn_trs = phn_trs.replace('AY', 'xy')
                phn_trs = phn_trs.replace('DH', 'xd')
                phn_trs = phn_trs.replace('EH', 'xe')
                phn_trs = phn_trs.replace('ER', 'xr')
                phn_trs = phn_trs.replace('EY', 'e')
                phn_trs = phn_trs.replace('CH', 'xc')
                phn_trs = phn_trs.replace('HH', 'h')
                phn_trs = phn_trs.replace('IH', 'xi')
                phn_trs = phn_trs.replace('IY', 'i')
                phn_trs = phn_trs.replace('JH', 'xj')
                phn_trs = phn_trs.replace('NG', 'xg')
                phn_trs = phn_trs.replace('OW', 'o')
                phn_trs = phn_trs.replace('OY', 'xo')
                phn_trs = phn_trs.replace('SH', 'xs')
                phn_trs = phn_trs.replace('TH', 'xt')
                phn_trs = phn_trs.replace('UH', 'xu')
                phn_trs = phn_trs.replace('UW', 'u')
                phn_trs = phn_trs.replace('ZH', 'xz')
                phn_trs = phn_trs.replace('D', 'd')
                phn_trs = phn_trs.replace('B', 'b')
                phn_trs = phn_trs.replace('F', 'f')
                phn_trs = phn_trs.replace('G', 'g')
                phn_trs = phn_trs.replace('K', 'k')
                phn_trs = phn_trs.replace('L', 'l')
                phn_trs = phn_trs.replace('M', 'm')
                phn_trs = phn_trs.replace('N', 'n')
                phn_trs = phn_trs.replace('P', 'p')
                phn_trs = phn_trs.replace('R', 'r')
                phn_trs = phn_trs.replace('S', 's')
                phn_trs = phn_trs.replace('T', 't')
                phn_trs = phn_trs.replace('V', 'v')
                phn_trs = phn_trs.replace('W', 'w')
                phn_trs = phn_trs.replace('Y', 'y')
                phn_trs = phn_trs.replace('Z', 'z')
                outfile.write(word + ' ' + phn_trs + '\n')

        # for the sounds
        for line in open(oov, 'r'):
            matched = re.match("(.*)\t(.*)", line)
            if matched:
                sound = matched.group(1)
                sound = sound.lower()
                freq = matched.group(2)
                freq = int(freq)
                # discard the OOV with freq 1 because they are the
                # typos. They will remain OOVs
                if freq > 1:
                    phn_trs = sound
                    # need to split the sound into phones to have the
                    # phonetic transcription
                    array_phn = phn_trs.split(":")
                    outfile.write(sound)
                    for phn in array_phn:
                        outfile.write(' ' + phn)
                    outfile.write('\n')
                else:
                    self.log.debug(sound)

        outfile.close()
        self.log.debug('finished creating lexicon file')