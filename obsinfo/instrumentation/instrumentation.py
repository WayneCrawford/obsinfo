"""
Instrumentation and Instrument classes

nomenclature:
    An "Instrument" (measurement instrument) records one physical parameter
    A "Channel" is an Instrument + an orientation code and possibly
        starttime, endtime and location code
    An "Instrumentation" combines one or more measurement Channels
"""
# Standard library modules

# Non-standard modules

# obsinfo modules
from .instrument_component import (Datalogger, Sensor, Preamplifier,
                                   Equipment)
from ..info_dict import InfoDict


class Instrumentation(object):
    """
    One or more Instruments. Part of an obspy/StationXML Station
    """
    def __init__(self, equipment, channels):
        """
        Constructor

        :param equipment: equipment description
        :type equipment: ~class `Equipment`
        :param channels: list of channels
        :type channels: list of ~class `Channel`
        """
        self.equipment = equipment
        self.channels = channels

    @classmethod
    def from_info_dict(cls, info_dict):
        """
        Create Instrumentation instance from an info_dict
        """
        info_dict = InfoDict(info_dict)
        info_dict = cls._complete_das_channels(info_dict)
        info_das = info_dict.get('das_channels', {})
        obj = cls(Equipment.from_info_dict(info_dict.get('equipment', None)),
                  [Channel.from_info_dict(v, k)
                   for k, v in info_das.items()])
        return obj

    def __repr__(self):
        s = f'Instrumentation({type(self.equipment)}, '
        s += f'{len(self.channels)} {type(self.channels[0])}'
        return s

    @staticmethod
    def _complete_das_channels(info_dict):
        """
        Complete 'das_channels' using 'base_channel'.

        Fields must be at the top level.
        'base_channel' is deleted

        >>> A = InfoDict(base_channel={'a': 5, 'b':6},
                         das_channels={'1': {'a': 7}, '2': {'b':0}})
        >>> self.complete_das_channels(A)
        >>> A
        {'das_channels': {'1': {'a': 7, 'b': 6}, '2': {'a': 5, 'b': 0}}}
        """
        assert 'das_channels'  in info_dict,\
            f"No 'das_channels' key in {info_dict.keys()}"
        assert 'base_channel' in info_dict,\
            f"No 'base_channel' key in {info_dict.keys()}"
        for key, value in info_dict['das_channels'].items():
            # print(f'"{key}"')
            temp = InfoDict(value)
            info_dict['das_channels'][key] = InfoDict(info_dict['base_channel'])
            info_dict['das_channels'][key].update(temp)
        del info_dict['base_channel']
        return info_dict


class Channel(object):
    """
    Channnel Class.

    Corresponds to StationXML/obspy Channel, plus das_channel code
    """
    def __init__(self, instrument, das_channel, orientation_code,
                 location=None, startdate=None, enddate=None):
        """
        :param instrument: instrument description
        :type instrument: ~class `Instrument`
        :param das_channel: the DAS channel the instrument is on
        :type das_channel: str
        :param orientation_code: orientation code of this channel/instrument
        :type orientation_code: str
        :param location_code: channel location code (if different from network)
        :type location_code: str, opt
        :param startdate: channel startdate (if different from network)
        :type startdate: str, opt
        :param enddate: channel enddate (if different from network)
        :type enddate: str, opt
        """
        self.instrument = instrument
        self.das_channel = das_channel
        self.orientation_code = orientation_code
        self.orientation = instrument.seed_orientations[orientation_code]
        self.location_code = location
        self.startdate = startdate
        self.enddate = enddate

    @classmethod
    def from_info_dict(cls, info_dict, das_channel=None):
        """
        Create instance from an info_dict

        :param info_dict: information dictionary at
                          instrument:das_channels level
        :type info_dict: dict
        """
        # print({'datalogger': info_dict['datalogger'],
        #        'sensor': info_dict['sensor'],
        #        'preamplifier': info_dict.get('preamplifier', None)})
        # print(InfoDict(datalogger=info_dict['datalogger'],
        #                      sensor=info_dict['sensor'],
        #                      preamplifier=info_dict.get('preamplifier', None))
        obj = cls(Instrument.from_info_dict(
                    {'datalogger': info_dict['datalogger'],
                     'sensor': info_dict['sensor'],
                     'preamplifier': info_dict.get('preamplifier', None)}),
                  das_channel,
                  info_dict['orientation_code'],
                  info_dict.get('location_code', None),
                  info_dict.get('startdate', None),
                  info_dict.get('enddate', None))
        return obj

    def __repr__(self):
        s = f'Channel({type(self.instrument)}, "{self.das_channel}", '
        s += f'"{self.orientation_code}"'
        if self.location:
            s += f', {self.location}'
            write_keys = False
        else:
            write_keys = True
        if self.startdate:
            if write_keys:
                s += f', startdate={self.startdate}'
            else:
                s += f', {self.startdate}'
        else:
            write_keys = True
        if self.enddate:
            if write_keys:
                s += f', enddate={self.enddate}'
            else:
                s += f', {self.enddate}'
        else:
            write_keys = True
        s += ')'
        return s

    @property
    def channel_code(self, sample_rate):
        """
        Return channel code for a given sample rate

        :param sample_rate: instrumentation sampling rate (sps)
        :kind sample_rate: float
        """
        inst_code = self.instrument.seed_instrument_code
        assert len(inst_code) == 1,\
            f'Instrument code "{inst_code}" is not a single letter'
        assert len(self.orientation_code) == 1,\
            'Orientation code "{}" is not a single letter'.format(
                self.orientation_code)
        return (self._band_code(sample_rate)
                + inst_code
                + self.orientation_code)

    def _band_code(self, sample_rate):
        """
        Return the channel band code

        :param sample_rate: sample rate (sps)
        """
        bbc = self.instrument.seed_band_base_code
        assert len(bbc) == 1,\
            f'Band base code "{bbc}" is not a single letter'
        if bbc in "FCHBMLVURPTQ":
            if sample_rate >= 1000:
                return "F"
            elif sample_rate >= 250:
                return "C"
            elif sample_rate >= 80:
                return "H"
            elif sample_rate >= 10:
                return "B"
            elif sample_rate > 1:
                return "M"
            elif sample_rate > 0.3:
                return "L"
            elif sample_rate > 0.03:
                return "V"
            elif sample_rate > 0.003:
                return "U"
            elif sample_rate >= 0.0001:
                return "R"
            elif sample_rate >= 0.00001:
                return "P"
            elif sample_rate >= 0.000001:
                return "T"
            else:
                return "Q"
        elif bbc in "GDES":
            if sample_rate >= 1000:
                return "G"
            elif sample_rate >= 250:
                return "D"
            elif sample_rate >= 80:
                return "E"
            elif sample_rate >= 10:
                return "S"
            else:
                raise ValueError("Short period sensor sample rate < 10 sps")
        else:
            raise NameError(f'Unknown band base code: "{bbc}"')


class Instrument(object):
    """
    Instrument Class.
    """
    def __init__(self, datalogger, sensor, preamplifier=None):
        """
        :param datalogger: datalogger information
        :type datalogger: ~class `Datalogger`
        :param sensor: sensor information
        :type sensor: ~class `Sensor`
        :param preamplifier: preamplifier information
        :type preamplifier: ~class `Preamplifier`, opt
        """
        # Set equipment parameters
        self.equipment_datalogger = datalogger.equipment
        self.equipment_sensor = sensor.equipment
        self.equipment_preamplifier = None
        if preamplifier:
            self.equipment_preamplifier = preamplifier.equipment
        # Stack response stages
        self.response_stages = sensor.response_stages
        if preamplifier:
            self.response_stages.extend(preamplifier.response_stages)
        self.response_stages.extend(datalogger.response_stages)
        # Assemble component-specific values
        self.sample_rate = datalogger.sample_rate
        self.delay_correction = datalogger.delay_correction
        self.seed_band_base_code = sensor.seed_band_base_code
        self.seed_instrument_code = sensor.seed_instrument_code
        self.seed_orientations = sensor.seed_orientations

    def __repr__(self):
        s = f'Instrument({self.datalogger}, {self.sensor}'
        if self.preamplifier:
            s += f', {self.preamplifier}'
        s += ')'
        return s

    @classmethod
    def from_info_dict(cls, info_dict):
        """
        Create instance from an info_dict

        :param info_dict: information dictionary containing datalogger,
                          sensor, and optionally preamplifier keys
        :type info_dict: InfoDict
        """
        assert 'datalogger' in info_dict, 'No datalogger specified'
        assert 'sensor' in info_dict, 'No sensor specified'
        obj = cls(Datalogger.from_info_dict(info_dict['datalogger']),
                  Sensor.from_info_dict(info_dict['sensor']),
                  Preamplifier.from_info_dict(info_dict.get('preamplifier',
                                                            None)))
        return obj
