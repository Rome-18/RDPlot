##################################################################################################
#    This file is part of RDPlot - A gui for creating rd plots based on pyqt and matplotlib
#    <https://git.rwth-aachen.de/IENT-Software/rd-plot-gui>
#    Copyright (C) 2017  Institut fuer Nachrichtentechnik, RWTH Aachen University, GERMANY
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##################################################################################################
import re, os

from os.path import abspath, join, isdir, isfile, normpath, basename, sep, dirname, splitext
from abc import ABCMeta

from rdplot.SimulationDataItem import (AbstractSimulationDataItem,
                                SimulationDataItemError)
from collections import defaultdict

class AbstractEncLog(AbstractSimulationDataItem):
    def __init__(self, path):
        super().__init__(path)

        # Parse file path and set additional identifiers
        # self.logType = self._get_Type(path)
        self.sequence, self.config = self._parse_path(self.path)


        # Dictionaries holding the parsed values
        self.summary_data = self._parse_summary_data()
        self.temporal_data = self._parse_temporal_data()
        self.additional_params = []

    def _parse_path(self, path):
        """ parses the identifiers for an encoder log out of the
        path of the logfile and the sequence name and qp given in
         the logfile"""
        # set config to path of sim data item
        config = dirname(normpath(path))
        # open log file and parse for sequence name and qp
        with open(self.path, 'r') as log_file:
            log_text = log_file.read()  # reads the whole text file
            sequence = re.findall(r""" ^Input \s+ File \s+ : \s+ (\S+) $
                                    """, log_text, re.M + re.X)

        # set sequence to the sequence name without path and suffix
        # not for
        sequence = splitext(basename(sequence[-1]))[0]

        return sequence, config

    def _get_label(self, keys):
        """
        :param keys: Variable/Path for which to get the labels
        :return: tuple of labels: (x-axis label, y-axis label)
        """
        # create all the labels with dictionaries. The leaves are tupels of x, y-labels
        labels = {}
        labels['Summary'] = {}
        labels['Summary']['B'] = labels['Summary']['B']['layer 0'] = labels['Summary']['B']['layer 1'] = labels['Summary']['B']['layer 1 + 2'] = defaultdict(lambda: ('kbps', 'dB'))
        labels['Summary']['I'] = labels['Summary']['I']['layer 0'] = labels['Summary']['I']['layer 1'] = labels['Summary']['I']['layer 1 + 2'] = defaultdict(lambda: ('kbps', 'dB'))
        labels['Summary']['P'] = labels['Summary']['P']['layer 0'] = labels['Summary']['P']['layer 1'] = labels['Summary']['P']['layer 1 + 2'] = defaultdict(lambda: ('kbps', 'dB'))
        labels['Summary']['SUMMARY'] = labels['Summary']['SUMMARY']['layer 0'] = labels['Summary']['SUMMARY']['layer 1'] = labels['Summary']['SUMMARY']['layer 1 + 2'] = defaultdict(lambda: ('kbps', 'dB'))

        labels['Summary']['B']['Bitrate'] = labels['Summary']['I']['Bitrate'] = labels['Summary']['P']['Bitrate'] = labels['Summary']['SUMMARY']['Bitrate'] = ('kbps', 'bits')
        labels['Summary']['B']['Frames'] = labels['Summary']['B']['Total Frames'] = ('kbps', 'Frames')
        labels['Summary']['I']['Frames'] = labels['Summary']['I']['Total Frames'] = ('kbps', 'Frames')
        labels['Summary']['P']['Frames'] = labels['Summary']['P']['Total Frames'] = ('kbps', 'Frames')
        labels['Summary']['SUMMARY']['Frames'] = labels['Summary']['SUMMARY']['Total Frames'] = ('kbps', 'Frames')
        labels['Summary']['SUMMARY']['Total Time'] = ('kbps', 'sec')
        labels['Summary']['SUMMARY']['HM Major Version'] = labels['Summary']['SUMMARY']['HM Minor Version'] = ('', 'sec')

        labels['Temporal'] = labels['Temporal']['layer 0'] = labels['Temporal']['layer 1'] = defaultdict(lambda: ('Frame', 'dB'))
        labels['Temporal']['Bits'] = ('Frame', 'bits')
        labels['Temporal']['Frames'] = ('Frame', 'POC')
        labels['Temporal']['ET'] = ('Frame', 'sec')
        label = labels
        # return needed label with keys

        for idx in keys[1:]:
            if isinstance(label[idx], dict):
                label = label[idx]
            else:
                label = label[idx]
                return label

    # Properties

    @property
    def tree_identifier_list(self):
        """Builds up the tree in case of more than one (QP) parameter varied in one simulation directory """
        # This is for conformance with rd data written out by older versions of rdplot
        if not hasattr(self, 'additional_params'):
            self.additional_params = []
        try:
            l1 = list(zip(self.additional_params, [self.encoder_config[i] for i in self.additional_params]))
            l1 = list(map(lambda x: '='.join(x), l1))
            return [self.__class__.__name__, self.sequence, self.config] + l1
        except:
            # MESSAGEBOX
            self.additional_params = ['QP']
            return [self.__class__.__name__, self.sequence, self.config]

    @property
    def data(self):
        # This is for conformance with rd data written out by older versions of rdplot
        if not hasattr(self, 'additional_params'):
            self.additional_params = []
        l1 = list(zip(self.additional_params, [self.encoder_config[i] for i in self.additional_params]))
        l1 = list(map(lambda x: '='.join(x), l1))
        return [
            (
                [self.sequence, self.config] + l1[0:len(l1)],
                {self.__class__.__name__: {'Temporal': self.temporal_data}}
            ),
            (
                [self.sequence, self.config] + l1[0:len(l1)-1],
                {self.__class__.__name__: {'Summary': self.summary_data}}
            ),
        ]

    # Non-abstract Helper Functions
    @classmethod
    def _enc_log_file_matches_re_pattern(cls, path, pattern):
        """"""
        if path.endswith("enc.log"):
            return cls._is_file_text_matching_re_pattern(path, pattern)
        return False

    def _parse_summary_data(self):
        with open(self.path, 'r') as log_file:
            log_text = log_file.read()  # reads the whole text file


class EncLogHM(AbstractEncLog):
    # Order value, used to determine order in which parser are tried.
    parse_order = 10

    def __init__(self, path):
        super().__init__(path)
        self.encoder_config = self._parse_encoder_config()

    @classmethod
    def can_parse_file(cls, path):
        matches_class = cls._enc_log_file_matches_re_pattern(path, r'^HM \s software')
        is_finished = cls._enc_log_file_matches_re_pattern(path, 'Total\ Time')
        if is_finished is False and matches_class is True:
            # In case an enc.log file has not a Total Time mark it is very likely that the file is erroneous.
            # TODO: Inform user with a dialog window
            print("Warning: The file" + path + " might be erroneous.")
        return matches_class and is_finished

    def _parse_summary_data(self):
        with open(self.path, 'r') as log_file:
            log_text = log_file.read()  # reads the whole text file

            hm_match = re.search(r'HM software: Encoder Version \[([a-zA-Z-]+)?([0-9]+)\.([0-9]+)', log_text)
            hm_major_version = hm_match.group(2)
            hm_minor_version = hm_match.group(3)

            if hm_major_version == '14':  # HM 14 does not write out average YUV-PSNR
                # catch summary line
                summaries = re.findall(r""" ^(\w*)-*.*$
                                   \s* # catch newline and space
                                   (.*)\| # catch phrase Total Frames / I / P / B
                                   (\s+\S+)(\s+\S+)(\s+\S+)(\s+\S+)# catch rest of the line
                                   \s* # catch newline and space
                                   (\d+\s+)\w # catch frame number
                                   (\s+\d+\.\d+)(\s+\d+\.\d+)(\s+\d+\.\d+)(\s+\d+\.\d+) # catch the fractional number (rate, PSNRs)
                              """, log_text, re.M + re.X)
                total_time = re.findall(r""" ^\s*Total\s+Time.\s+(\d+.\d+)
                               """, log_text, re.M + re.X)
            else:
                # catch summary line
                summaries = re.findall(r""" ^(\w*)-*.*$
                               \s* # catch newline and space
                               (.*)\| # catch phrase Total Frames / I / P / B
                               (\s+\S+)(\s+\S+)(\s+\S+)(\s+\S+)(\s+\S+)# catch rest of the line
                               \s* # catch newline and space
                               (\d+\s+)\w # catch frame number
                               (\s+\d+\.\d+)(\s+\d+\.\d+)(\s+\d+\.\d+)(\s+\d+\.\d+)(\s+\d+\.\d+)# catch the fractional number (rate, PSNRs)
                          """, log_text, re.M + re.X)
                total_time = re.findall(r""" ^\s*Total\s+Time.\s+(\d+.\d+)
                               """, log_text, re.M + re.X)
        data = {}
        for summary in summaries:
            summary_type = summary[0]
            # Create upon first access
            if summary_type not in data:
                data[summary_type] = {}

            # remove first element, we need an even number of elements. then split into two list, values and names
            # and pack them together
            summary = summary[1:]
            names = summary[:len(summary) // 2]
            vals = summary[len(summary) // 2:]

            names = [name.strip() for name in names]  # remove leading and trailing space
            vals = [float(val) for val in vals]  # convert to numbers

            name_val_dict = dict(zip(names, vals))  # pack both together in a dict
            # print(summary_type)

            name_rate = 'Bitrate'
            if summary_type == 'SUMMARY':
                bitrate = float(vals[names.index(name_rate)])
            names.remove(name_rate)

            # now pack everything together
            for name in names:
                if name not in data[summary_type]:  # create upon first access
                    data[summary_type][name] = []
                # Reference all data to *self.qp*
                data[summary_type][name].append(
                    (name_val_dict[name_rate], name_val_dict[name])
                )
        # data['Total Time'] = total_time[0]
        data['SUMMARY']['Total Time'] = [(bitrate, float(total_time[0]))]
        data['SUMMARY']['HM Major Version'] = [(bitrate, int(hm_major_version))]
        data['SUMMARY']['HM Minor Version'] = [(bitrate, int(hm_minor_version))]
        return data

    def _parse_encoder_config(self):
        with open(self.path, 'r') as log_file:
            log_text = log_file.read()  # reads the whole text file
            lines = log_text.split('\n')
            cleanlist = []
            # some of the configs should not be interpreted as parameters
            # those are removed from the cleanlist
            param_not_considered = ['RealFormat', 'Warning', 'InternalFormat', 'Byteswrittentofile', 'Frameindex',
                                    'TotalTime', 'HMsoftware']
            for one_line in lines:
                if one_line:
                    if 'Non-environment-variable-controlled' in one_line:
                        break
                    if one_line.count(':') == 1:
                        clean_line = one_line.strip(' \n\t\r')
                        clean_line = re.sub('\s+', '', clean_line)
                        if not any(re.search(param,clean_line) for param in param_not_considered):
                            cleanlist.append(clean_line)
                    elif one_line.count(':') > 1:
                        if re.search('\w+ \s+ \w+ \s+ \w+ \s+ :\s+ \( \w+ : \d+ , \s+ \w+ : \d+ \)', one_line, re.X):
                            clean_line = re.findall('\w+ \s+ \w+ \s+ \w+ \s+ :\s+ \( \w+ : \d+ , \s+ \w+ : \d+ \)', one_line, re.X)
                        else:
                            clean_line = re.findall('\w+ : \d+ | \w+ : \s+ \w+ = \d+', one_line, re.X)
                        for clean_item in clean_line:
                            if not any(re.search(param,clean_item) for param in param_not_considered):
                                cleanlist.append(clean_item)

        parsed_config = dict(item.split(':', 1) for item in cleanlist)
        self.qp = parsed_config['QP']
        return parsed_config

    def _parse_temporal_data(self):
        # this function extracts temporal values
        with open(self.path, 'r') as log_file:
            log_text = log_file.read()  # reads the whole text file

        temp_data = re.findall(r"""
            ^POC \s+ (\d+) \s+ .+ \s+ \d+ \s+ . \s+ (.-\D+) ,  #Slice
            \s .+ \) \s+ (\d+) \s+ (.+) \s+ #bits
            \[ (\D+) \s+ (\d+.\d+) \s+ #Y PSNR
            \D+ \s+ (\D+) \s+ (\d+.\d+) \s+ # U PSNR
            \D+ \s+ (\D+) \s+ (\d+.\d+) \s+ \D+ . # V PSNR
            \s+ \[ (\D+) \s+ (\d+) \s+# Encoding time
            """, log_text, re.M + re.X)

        # Association between index of data in temp_data and corresponding
        # output key. Output shape definition is in one place.
        names = {0: 'Frames', 2: 'Bits', 5: 'Y-PSNR', 7: 'U-PSNR',
                 9: 'V-PSNR', 11: 'ET'}

        # Define output data dict and fill it with parsed values
        data = {name: [] for (index, name) in names.items()}
        for i in range(0, len(temp_data)):
            # As referencing to frame produces error, reference to index *i*
            for (index, name) in names.items():
                data[name].append(
                    (i, temp_data[i][index])
                )
        return data


class EncLogHM360Lib(AbstractEncLog):
    # Order value, used to determine order in which parser are tried.
    parse_order = 20

    def __init__(self, path):
        super().__init__(path)
        self.encoder_config = self._parse_encoder_config()

    @classmethod
    def can_parse_file(cls, path):
        matches_class = cls._enc_log_file_matches_re_pattern(path, r'Y-PSNR_(?:DYN_)?VP0')
        is_finished = cls._enc_log_file_matches_re_pattern(path, 'Total\ Time')
        return matches_class and is_finished

    def _parse_encoder_config(self):
        with open(self.path, 'r') as log_file:
            log_text = log_file.read()  # reads the whole text file
            lines = log_text.split('\n')
            cleanlist = []
            for one_line in lines:
                if one_line:
                    if '-----360 video parameters----' in one_line:
                        break
                    if one_line.count(':') == 1:
                        clean_line = one_line.strip(' \n\t\r')
                        clean_line = clean_line.replace(' ', '')
                        cleanlist.append(clean_line)
                        # elif one_line.count(':')>1:
                        # Ignore Multiline stuff for now
                        # TODO: do something smart
                        # else:
                        # Something else happened, do nothing
                        # TODO: do something smart
        parsed_config = dict(item.split(':') for item in cleanlist)

        # parse 360 rotation parameter
        m = re.search('Rotation in 1/100 degrees:\s+\(yaw:(\d+)\s+pitch:(\d+)\s+roll:(\d+)\)', log_text)
        if m:
            yaw = m.group(1)
            pitch = m.group(2)
            roll = m.group(3)
            parsed_config['SVideoRotation'] = 'Y%sP%sR%s' % (yaw, pitch, roll)
        self.qp = parsed_config['QP']

        return parsed_config

    def _parse_summary_data(self):

        with open(self.path, 'r') as log_file:
            log_text = log_file.read()
            total_time = re.findall(r""" ^\s*Total\s+Time.\s+(\d+.\d+)
                            """, log_text, re.M + re.X)

        if self._enc_log_file_matches_re_pattern(self.path, r'Y-PSNR_VP0'):
            # 360Lib version < 3.0
            with open(self.path, 'r') as log_file:
                log_text = log_file.read()  # reads the whole text file
                summaries = re.findall(r""" ^(\S+) .+ $ \s .+ $
                                            \s+ (\d+) \s+ \D \s+ (\S+)  # Total Frames, Bitrate
                                            \s+ (\S+) \s+ (\S+) \s+ (\S+) \s+ (\S+)  # y-, u-, v-, yuv-PSNR
                                            \s+ (\S+) \s+ (\S+) \s+ (\S+)  # SPSNR_NN
                                            \s+ (\S+) \s+ (\S+) \s+ (\S+)  # WSPSNR
                                            \s+ (\S+) \s+ (\S+) \s+ (\S+)  # SPSNR_I
                                            \s+ (\S+) \s+ (\S+) \s+ (\S+)  # CPPPSNR
                                            \s+ (\S+) \s+ (\S+) \s+ (\S+)  # E2EWSPSNR
                                            \s+ (\S+) \s+ (\S+) \s+ (\S+)  # PSNR_VP0
                                            \s+ (\S+) \s+ (\S+) \s+ (\S+) $  # PSNR_VP1
                                            """, log_text, re.M + re.X)
            data = {}
            names = {1: 'Frames', 2: 'Bitrate',
                     3: 'Y-PSNR', 4: 'U-PSNR', 5: 'V-PSNR', 6: 'YUV-PSNR',
                     7: 'Y-SPSNR_NN', 8: 'U-SPSNR_NN', 9: 'V-SPSNR_NN',
                     10: 'Y-WSPSNR', 11: 'U-WSPSNR', 12: 'V-WSPSNR',
                     13: 'Y-SPSNR_I', 14: 'U-SPSNR_I', 15: 'V-SPSNR_I',
                     16: 'Y-CPPSNR', 17: 'U-CPPSNR', 18: 'V-CPPSNR',
                     19: 'Y-E2EWSPSNR', 20: 'U-E2EWSPSNR', 21: 'V-E2EWSPSNR',
                     22: 'Y-PSNR_VP0', 23: 'U-PSNR_VP0', 24: 'V-PSNR_VP0',
                     25: 'Y-PSNR_VP1', 26: 'U-PSNR_VP1', 27: 'V-PSNR_VP1'
                     }

            for i in range(0, len(summaries)):  # iterate through Summary, I, P, B
                data2 = {name: [] for (index, name) in names.items()}
                for (index, name) in names.items():
                    data2[name].append(
                        (float(summaries[i][2]), float(summaries[i][index]))
                    )
                data[summaries[i][0]] = data2

        if self._enc_log_file_matches_re_pattern(self.path, r'-----360Lib\ software\ version\ \[3.0\]-----'):
            with open(self.path, 'r') as log_file:
                log_text = log_file.read()  # reads the whole text file
                # todo: \s can not be used, since it contains newline. can [ \t\r\f\v] be declared somehow?
                summaries = re.findall(r""" ^(\S+) .+ $ \s .+ $
                                            \s+ (\d+) [ \t\r\f\v]+ \D [ \t\r\f\v]+ (\S+)  # Total Frames, Bitrate
                                            [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+)  # y-, u-, v-, yuv-PSNR
                                            [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+)  # WSPSNR
                                            [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+)  # E2ESPSNR_NN
                                            [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+)  # E2ESPSNR_I
                                            [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+)  # E2ECPPPSNR
                                            [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+)  # E2EWSPSNR
                                            [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+)  # PSNR_DYN_VP0
                                            [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+)  # PSNR_DYN_VP1
                                            [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+)  # CFSPSNR_NN
                                            [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+)  # CFSPSNR_I
                                            [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+  $# CFCPPPSNR
                                            """, log_text, re.M + re.X)

            data = {}
            names = {1: 'Frames', 2: 'Bitrate',
                     3: 'Y-PSNR', 4: 'U-PSNR', 5: 'V-PSNR', 6: 'YUV-PSNR',
                     7: 'Y-WSPSNR', 8: 'U-WSPSNR', 9: 'V-WSPSNR',
                     10: 'Y-E2ESPSNR_NN', 11: 'U-E2ESPSNR_NN', 12: 'V-E2ESPSNR_NN',
                     13: 'Y-E2ESPSNR_I', 14: 'U-E2ESPSNR_I', 15: 'V-E2ESPSNR_I',
                     16: 'Y-E2ECPPPSNR', 17: 'U-E2ECPPPSNR', 18: 'V-E2ECPPPSNR',
                     19: 'Y-E2EWSPSNR', 20: 'U-E2EWSPSNR', 21: 'V-E2EWSPSNR',
                     22: 'Y-PSNR_DYN_VP0', 23: 'U-PSNR_DYN_VP0', 24: 'V-PSNR_DYN_VP0',
                     25: 'Y-PSNR_DYN_VP1', 26: 'U-PSNR_DYN_VP1', 27: 'V-PSNR_DYN_VP1',
                     28: 'Y-CFSPSNR_NN', 29: 'U-CFSPSNR_NN', 30: 'V-CFSPSNR_NN',
                     31: 'Y-CFSPSNR_I', 32: 'U-CFSPSNR_I', 33: 'V-CFSPSNR_I',
                     34: 'Y-CFCPPPSNR', 35: 'U-CFCPPPSNR', 36: 'V-CFCPPPSNR'
                     }

            for i in range(0, len(summaries)):  # iterate through Summary, I, P, B
                data2 = {name: [] for (index, name) in names.items()}
                for (index, name) in names.items():
                    data2[name].append(
                        (float(summaries[i][2]), float(summaries[i][index]))
                    )
                data[summaries[i][0]] = data2

        if self._enc_log_file_matches_re_pattern(self.path, r'-----360Lib\ software\ version\ \[4.0\]-----'):
            with open(self.path, 'r') as log_file:
                log_text = log_file.read()  # reads the whole text file
                # todo: \s can not be used, since it contains newline. can [ \t\r\f\v] be declared somehow?
                # summaries = re.findall(r""" ^(\S+) .+ $ \s .+ $
                #                             \s+ (\d+) \s+ \D \s+ (\S+)  # Total Frames, Bitrate
                #                             [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+)  # y-, u-, v-, yuv-PSNR
                #                             [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+)  # WSPSNR
                #                             [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+)  # C_SPSNR_NN
                #                             [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+)  # E2ESPSNR_NN
                #                             [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+)  # E2ESPSNR_I
                #                             [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+)  # E2ECPPPSNR
                #                             [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+)  # E2EWSPSNR
                #                             [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+)  # PSNR_DYN_VP0
                #                             [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+)  # PSNR_DYN_VP1
                #                             [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+)  # CFSPSNR_NN
                #                             [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+)  # CFSPSNR_I
                #                             [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+  $# CFCPPPSNR
                #                             """, log_text, re.M + re.X)
                summaries = re.findall(r""" ^(\S+) .+ $ \s .+ $
                                            \s+ (\d+) \s+ \D \s+ (\S+)  # Total Frames, Bitrate
                                            [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+)  # y-, u-, v-, yuv-PSNR
                                            [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+)  # WSPSNR
                                            [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+)  # C_SPSNR_NN
                                            [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+)  # E2ESPSNR_NN
                                            [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+)  # E2EWSPSNR
                                            [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+)  # PSNR_DYN_VP0
                                            [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+)  # PSNR_DYN_VP1
                                            [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+)  # CFSPSNR_NN
                                            [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+ (\S+) [ \t\r\f\v]+  $# CFCPPPSNR
                                            """, log_text, re.M + re.X)

            data = {}
            # names = {1: 'Frames', 2: 'Bitrate',
            #          3: 'Y-PSNR', 4: 'U-PSNR', 5: 'V-PSNR', 6: 'YUV-PSNR',
            #          7: 'Y-WSPSNR', 8: 'U-WSPSNR', 9: 'V-WSPSNR',
            #          10: 'Y-C_SPSNR_NN', 11: 'U-C_SPSNR_NN', 12: 'V-C_SPSNR_NN',
            #          13: 'Y-E2ESPSNR_NN', 14: 'U-E2ESPSNR_NN', 15: 'V-E2ESPSNR_NN',
            #          16: 'Y-E2ESPSNR_I', 17: 'U-E2ESPSNR_I', 18: 'V-E2ESPSNR_I',
            #          19: 'Y-E2ECPPPSNR', 20: 'U-E2ECPPPSNR', 21: 'V-E2ECPPPSNR',
            #          22: 'Y-E2EWSPSNR', 23: 'U-E2EWSPSNR', 24: 'V-E2EWSPSNR',
            #          25: 'Y-PSNR_DYN_VP0', 26: 'U-PSNR_DYN_VP0', 27: 'V-PSNR_DYN_VP0',
            #          28: 'Y-PSNR_DYN_VP1', 29: 'U-PSNR_DYN_VP1', 30: 'V-PSNR_DYN_VP1',
            #          31: 'Y-CFSPSNR_NN', 32: 'U-CFSPSNR_NN', 33: 'V-CFSPSNR_NN',
            #          34: 'Y-CFSPSNR_I', 35: 'U-CFSPSNR_I', 36: 'V-CFSPSNR_I',
            #          37: 'Y-CFCPPPSNR', 38: 'U-CFCPPPSNR', 39: 'V-CFCPPPSNR'
            #          }

            names = {1: 'Frames', 2: 'Bitrate',
                     3: 'Y-PSNR', 4: 'U-PSNR', 5: 'V-PSNR', 6: 'YUV-PSNR',
                     7: 'Y-WSPSNR', 8: 'U-WSPSNR', 9: 'V-WSPSNR',
                     10: 'Y-C_SPSNR_NN', 11: 'U-C_SPSNR_NN', 12: 'V-C_SPSNR_NN',
                     13: 'Y-E2ESPSNR_NN', 14: 'U-E2ESPSNR_NN', 15: 'V-E2ESPSNR_NN',
                     16: 'Y-E2EWSPSNR', 17: 'U-E2EWSPSNR', 18: 'V-E2EWSPSNR',
                     19: 'Y-PSNR_DYN_VP0', 20: 'U-PSNR_DYN_VP0', 21: 'V-PSNR_DYN_VP0',
                     22: 'Y-PSNR_DYN_VP1', 23: 'U-PSNR_DYN_VP1', 24: 'V-PSNR_DYN_VP1',
                     25: 'Y-CFSPSNR_NN', 26: 'U-CFSPSNR_NN', 27: 'V-CFSPSNR_NN',
                     28: 'Y-CFCPPPSNR', 29: 'U-CFCPPPSNR', 30: 'V-CFCPPPSNR'
                     }

            for i in range(0, len(summaries)):  # iterate through Summary, I, P, B
                data2 = {name: [] for (index, name) in names.items()}
                for (index, name) in names.items():
                    data2[name].append(
                        (float(summaries[i][2]), float(summaries[i][index]))
                    )
                data[summaries[i][0]] = data2

        data['SUMMARY']['Total Time'] = [(float(summaries[0][2]), float(total_time[0]))]
        return data

    def _parse_temporal_data(self):
        # this function extracts temporal values

        if self._enc_log_file_matches_re_pattern(self.path, r'-----360Lib\ software\ version\ \[3.0\]-----'):
            with open(self.path, 'r') as log_file:
                log_text = log_file.read()  # reads the whole text file
                temp_data = re.findall(r"""
                    ^POC \s+ (\d+) \s+ .+ \s+ \d+ \s+ . \s+ (.-\D+) ,  # POC, Slice
                    \s .+ \) \s+ (\d+) \s+ \S+ \s+  # bitrate
                    \[ \S \s (\S+) \s \S+ \s+ \S \s (\S+) \s \S+ \s+ \S \s (\S+) \s \S+ ] \s  # y-, u-, v-PSNR
                    \[ \S+ \s (\S+) \s \S+ \s+ \S+ \s (\S+) \s \S+ \s+ \S+ \s (\S+) \s \S+ ] \s  #y-, u-, v-SPSNR_NN
                    \[ \S+ \s (\S+) \s \S+ \s+ \S+ \s (\S+) \s \S+ \s+ \S+ \s (\S+) \s \S+ ] \s  #y-, u-, v-WSPSNR
                    \[ \S+ \s (\S+) \s \S+ \s+ \S+ \s (\S+) \s \S+ \s+ \S+ \s (\S+) \s \S+ ] \s  #y-, u-, v-SPSNR_I
                    \[ \S+ \s (\S+) \s \S+ \s+ \S+ \s (\S+) \s \S+ \s+ \S+ \s (\S+) \s \S+ ] \s  #y-, u-, v-CPPPSNR
                    \[ \S+ \s (\S+) \s \S+ \s+ \S+ \s (\S+) \s \S+ \s+ \S+ \s (\S+) \s \S+ ] \s  #y-, u-, v-E2EWSPSNR
                    \[ \S+ \s (\S+) \s \S+ \s+ \S+ \s (\S+) \s \S+ \s+ \S+ \s (\S+) \s \S+ ] \s  #y-, u-, v-PSNR_VP0
                    \[ \S+ \s (\S+) \s \S+ \s+ \S+ \s (\S+) \s \S+ \s+ \S+ \s (\S+) \s \S+ ] \s  #y-, u-, v-PSNR_VP1
                    \[ \S+ \s \S+ \s \S+ \s+ \S+ \s \S+ \s \S+ \s+ \S+ \s \S+ \s \S+ ] \s  #y-, u-, v-CFSPSNR_NN
                    \[ \S+ \s \S+ \s \S+ \s+ \S+ \s \S+ \s \S+ \s+ \S+ \s \S+ \s \S+ ] \s  #y-, u-, v-CFSPSNR_I
                    \[ \S+ \s \S+ \s \S+ \s+ \S+ \s \S+ \s \S+ \s+ \S+ \s \S+ \s \S+ ] \s  #y-, u-, v-CFCPPPSNR
                    \[ \D+ \s+ (\d+) \s+ #ET
                    """, log_text, re.M + re.X)

                # Association between index of data in temp_data and corresponding
                # output key. Output shape definition is in one place.
                names = {0: 'Frames', 2: 'Bits',
                         3: 'Y-PSNR', 4: 'U-PSNR', 5: 'V-PSNR',
                         6: 'Y-SPSNR_NN', 7: 'U-SPSNR_NN', 8: 'V-SPSNR_NN',
                         9: 'Y-WSPSNR', 10: 'U-WSPSNR', 11: 'V-WSPSNR',
                         12: 'Y-SPSNR_I', 13: 'U-SPSNR_I', 14: 'V-SPSNR_I',
                         15: 'Y-CPPSNR', 16: 'U-CPPSNR', 17: 'V-CPPSNR',
                         18: 'Y-E2EWSPSNR', 19: 'U-E2EWSPSNR', 20: 'V-E2EWSPSNR',
                         21: 'Y-PSNR_VP0', 22: 'U-PSNR_VP0', 23: 'V-PSNR_VP0',
                         24: 'Y-PSNR_VP1', 25: 'U-PSNR_VP1', 26: 'V-PSNR_VP1', 27: 'ET'
                         }

        if self._enc_log_file_matches_re_pattern(self.path, r'-----360Lib\ software\ version\ \[4.0\]-----'):
            with open(self.path, 'r') as log_file:
                log_text = log_file.read()  # reads the whole text file
                temp_data = re.findall(r"""
                    ^POC \s+ (\d+) \s+ .+ \s+ \d+ \s+ . \s+ (.-\D+) ,  # POC, Slice
                    \s .+ \) \s+ (\d+) \s+ \S+ \s+  # bitrate
                    \[ \S \s (\S+) \s \S+ \s+ \S \s (\S+) \s \S+ \s+ \S \s (\S+) \s \S+ ] \s  # y-, u-, v-PSNR
                    \[ \S+ \s (\S+) \s \S+ \s+ \S+ \s (\S+) \s \S+ \s+ \S+ \s (\S+) \s \S+ ] \s  #y-, u-, v-WSPSNR
                    \[ \S+ \s (\S+) \s \S+ \s+ \S+ \s (\S+) \s \S+ \s+ \S+ \s (\S+) \s \S+ ] \s  #y-, u-, v-C_SPSNR_NN
                    \[ \S+ \s (\S+) \s \S+ \s+ \S+ \s (\S+) \s \S+ \s+ \S+ \s (\S+) \s \S+ ] \s  #y-, u-, v-E2ESPSNR_NN
                    \[ \S+ \s (\S+) \s \S+ \s+ \S+ \s (\S+) \s \S+ \s+ \S+ \s (\S+) \s \S+ ] \s  #y-, u-, v-E2EWSPSNR
                    \[ \S+ \s (\S+) \s \S+ \s+ \S+ \s (\S+) \s \S+ \s+ \S+ \s (\S+) \s \S+ ] \s  #y-, u-, v-PSNR_DYN_VP0
                    \[ \S+ \s (\S+) \s \S+ \s+ \S+ \s (\S+) \s \S+ \s+ \S+ \s (\S+) \s \S+ ] \s  #y-, u-, v-PSNR_DYN_VP1
                    \[ \S+ \s (\S+) \s \S+ \s+ \S+ \s (\S+) \s \S+ \s+ \S+ \s (\S+) \s \S+ ] \s  #y-, u-, v-CFSPSNR_NN
                    \[ \S+ \s (\S+) \s \S+ \s+ \S+ \s (\S+) \s \S+ \s+ \S+ \s (\S+) \s \S+ ] \s  #y-, u-, v-CFCPPPSNR
                    \[ \D+ \s+ (\d+) \s+ #ET
                    """, log_text, re.M + re.X)

                names = {0: 'Frames', 2: 'Bits',
                         3: 'Y-PSNR', 4: 'U-PSNR', 5: 'V-PSNR',
                         6: 'Y-WSPSNR', 7: 'U-WSPSNR', 8: 'V-WSPSNR',
                         9: 'Y-C_SPSNR_NN', 10: 'U-C_SPSNR_NN', 11: 'V-C_SPSNR_NN',
                         12: 'Y-E2ESPSNR_NN', 13: 'U-E2ESPSNR_NN', 14: 'V-E2ESPSNR_NN',
                         15: 'Y-E2EWSPSNR', 16: 'U-E2EWSPSNR', 17: 'V-E2EWSPSNR',
                         18: 'Y-PSNR_DYN_VP0', 19: 'U-PSNR_DYN_VP0', 20: 'V-PSNR_DYN_VP0',
                         21: 'Y-PSNR_DYN_VP1', 22: 'U-PSNR_DYN_VP1', 23: 'V-PSNR_DYN_VP1',
                         24: 'Y-CFSPSNR_NN', 25: 'U-CFSPSNR_NN', 26: 'V-CFSPSNR_NN',
                         27: 'Y-CFCPPPSNR', 28: 'U-CFCPPPSNR', 29: 'V-CFCPPPSNR', 30: 'ET'
                         }

        # Define output data dict and fill it with parsed values
        data = {name: [] for (index, name) in names.items()}
        for i in range(0, len(temp_data)):
            # As referencing to frame produces error, reference to index *i*
            for (index, name) in names.items():
                data[name].append(
                    (i, temp_data[i][index])
                )
        return data


class EncLogSHM(AbstractEncLog):
    # Order value, used to determine order in which parser are tried.
    parse_order = 21

    @classmethod
    def can_parse_file(cls, path):
        matches_class = cls._enc_log_file_matches_re_pattern(path, r'^SHM \s software')
        is_finished = cls._enc_log_file_matches_re_pattern(path, 'Total\ Time')
        return matches_class and is_finished

    def _parse_summary_data(self):
        with open(self.path, 'r') as log_file:
            log_text = log_file.read()  # reads the whole text file
            summaries = re.findall(r"""
                        ^\s+ L (\d+) \s+ (\d+) \s+ \D \s+ # the next is bitrate
                        (\S+) \s+ (\S+) \s+ (\S+) \s+ (\S+) \s+ (\S+)
                        """, log_text, re.M + re.X)
            total_time = re.findall(r""" ^\s*Total\s+Time.\s+(\d+.\d+)
                                        """, log_text, re.M + re.X)
        data = {}
        layer_quantity = int(len(summaries) / 4)
        header_names = ['SUMMARY', 'I', 'P', 'B']
        names = {1: 'Frames', 2: 'Bitrate', 3: 'Y-PSNR', 4: 'U-PSNR',
                 5: 'V-PSNR', 6: 'YUV-PSNR', }

        for it in range(0, 4):  # iterate through Summary, I, P, B
            data2 = {}
            for layer in range(0, layer_quantity):  # iterate through layers
                layerstring = 'layer ' + str(layer)
                data2[layerstring] = {}
                data3 = {}
                bitrate = summaries[layer_quantity * it + layer][2]
                for (index, name) in names.items():
                    # convert string '-nan' to int 0 if necessary
                    data3[name] = []
                    if isinstance(bitrate, str) and (bitrate == '-nan'):
                        data3[name].append(
                            (float(0), float(0))
                        )
                    else:
                        data3[name].append(
                            (float(bitrate), float(summaries[layer_quantity * it + layer][index]))
                        )
                data2[layerstring] = data3

            # add the addition of layers 1 and two in rate. PSNR values are taken from Layer one
            # TODO make this nice one day
            layerstring = 'layer 1 + 2'
            # data2[layerstring] = {}
            data4 = {}
            bitrate = 0
            for layer in range(0, layer_quantity):
                if summaries[layer_quantity * it + layer_quantity - 1][2] != '-nan':
                    bitrate += float(summaries[layer_quantity * it + layer][2])
            for (index, name) in names.items():
                data4[name] = []
                if summaries[layer_quantity * it + layer_quantity - 1][2] == 'nan':
                    data4[name].append((float(0), float(0)))
                else:
                    data4[name].append(
                        (bitrate, float(summaries[layer_quantity * it + layer_quantity - 1][index])))
            data2[layerstring] = data4

            data[header_names[it]] = data2

        data['SUMMARY']['layer 0']['Total Time'] = [(float(summaries[0][2]), float(total_time[0]))]
        data['SUMMARY']['layer 1']['Total Time'] = [(float(summaries[1][2]), float(total_time[0]))]
        data['SUMMARY']['layer 1 + 2']['Total Time'] = [
            (float(data['SUMMARY']['layer 1 + 2']['Bitrate'][0][0]), float(total_time[0]))]
        return data

    def _parse_temporal_data(self):
        # this function extracts temporal values
        with open(self.path, 'r') as log_file:
            log_text = log_file.read()  # reads the whole text file
            temp_data = re.findall(r"""
                                ^POC \s+ (\d+) .+? : \s+ (\d+) .+ (\D-\D+) \s \D+,  #Slice
                                .+ \) \s+ (\d+) \s+ (.+) \s+ \[ (\D+) \s+ (\d+.\d+) \s+ #Y PSNR
                                \D+ \s+ (\D+) \s+ (\d+.\d+) \s+ # U PSNR
                                \D+ \s+ (\D+) \s+ (\d+.\d+) \s+ \D+ . # v PSNR
                                \s+ \[ (\D+) \s+ (\d+) \s+# Encoding time
                                """, log_text, re.M + re.X)

        # Association between index of data in temp_data and corresponding
        # output key. Output shape definition is in one place.
        names = {0: 'Frames', 3: 'Bits', 6: 'Y-PSNR', 8: 'U-PSNR',
                 10: 'V-PSNR', 12: 'ET'}

        layer_quantity = int(max(temp_data[i][1] for i in range(0, len(temp_data)))) + 1
        layer_quantity = int(layer_quantity)
        data = {}
        for layer in range(0, layer_quantity):  # iterate through layers
            data2 = {name: [] for (index, name) in names.items()}
            for j in range(0, int(len(temp_data) / layer_quantity)):  # iterate through frames (POCS)
                for (index, name) in names.items():
                    data2[name].append(
                        (j, temp_data[layer_quantity * j + layer][index])
                    )
            layerstring = 'layer ' + str(layer)
            data[layerstring] = data2
        return data
