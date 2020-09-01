"""
InstrumentComponent class and subclasses.

No StationXML equivalent.
"""
# Standard library modules
# import math as m
import warnings
import pprint

# Non-standard modules

from .response_stages import ResponseStages
from .equipment import Equipment
from .orientation import Orientation

pp = pprint.PrettyPrinter(depth=2)


class InstrumentComponent(object):
    """
    InstrumentComponent superclass.  No obspy equivalent
    """
    def __init__(self,
                 equipment,
                 response_stages=[]):
        """
        Constructor
        """
        self.equipment = equipment
        self.response_stages = response_stages

    @staticmethod
    def from_info_dict(info_dict, debug=False):
        """
        Create instance from an info_dict
        """
        if not info_dict:
            return None
        if debug:
            print('InstrumentComponent info_dict')
            pp.pprint(info_dict)
        if 'datalogger' in info_dict:
            info_dict = info_dict['datalogger']
            cls = Datalogger
        elif 'sensor' in info_dict:
            info_dict = info_dict['sensor']
            cls = Sensor
        elif 'preamplifier' in info_dict:
            info_dict = info_dict['preamplifier']
            cls = Preamplifier
        elif 'sample_rate' in info_dict:
            cls = Datalogger
        elif 'seed_codes' in info_dict:
            cls = Sensor
        elif 'equipment' in info_dict:
            cls = Preamplifier
        else:
            warnings.warn(f'Unknown InstrumentComponent: "{info_dict}"')

        if debug:
            print(cls)
        if info_dict is None:
            return None
        obj = cls.from_info_dict(info_dict)
        return obj

    @staticmethod
    def _configuration_serialnumber(info_dict, debug=False):
        """
        Modify info_dict to account for configuration and serial number
        """
        # Standard stuff for all instrument components
        if not info_dict:
            warnings.warn('received empty info_dict')
            return None
        if debug:
            print('in instrument_component._configuration_serialnumber')
            print('BEFORE BEFORE')
            pp.pprint(info_dict)
            print('InstrumentComponent:_configuration_serialnumber info_dict:')
            pp.pprint(info_dict)
        config = info_dict.get('configuration', None)
        if config:
            if config not in info_dict.get('configuration_definitions',{}):
                warnings.warn(f'configuration "{config}" not in instrument '
                              f'component configuration_definitions '
                              f'"{pp.pprint(info_dict)}"')
            else:
                info_dict.update(info_dict['configuration_definitions']
                                          [config])
                info_dict['equipment']['description'] += ' [{}]'.format(config)
        if 'serial_number' in info_dict:
            serial_number = info_dict['serial_number']
            info_dict['equipment']['serial_number'] = serial_number
            SNM = info_dict.get('serial_number_modifications', {})
            if serial_number in SNM:
                if debug:
                    print('BEFORE')
                    pp.pprint(info_dict)
                info_dict.update(SNM[serial_number])
                if debug:
                    print('AFTER')
                    pp.pprint(info_dict)
            assert 'equipment' in info_dict,\
                f'no equipment in info_dict: {pp.pprint(info_dict)}'
        return info_dict


class Datalogger(InstrumentComponent):
    """
    Datalogger Instrument Component
    """
    def __init__(self,
                 equipment,
                 response_stages,
                 sample_rate, 
                 delay_correction=0):
        """
        Constructor
        
        :param equipment: description of the Datalogger
        :kind equipment: ~class Equipment
        :param response_stages: ordered response stages
        :kind response_stages: ~class ResponseStages
        :param sample_rate: data sample rate (samples per second)
        :kind sample_rate: float
        :param delay_correction: time correction applied to the data time stamp
        :kind delay_correction: float, optional
        """
        self.equipment = equipment
        self.response_stages = response_stages
        self.sample_rate = sample_rate
        self.delay_correction = delay_correction

    def __str__(self):
        return 'Datalogger: {}, {:d} resp stages, {} sps, {} delay corr'.\
            format(self.equipment.model, len(self.response_stages),
                   self.sample_rate, self.delay_correction)

    @classmethod
    def from_info_dict(cls, info_dict):
        """
        Create instance from an info_dict
        """
        info_dict = InstrumentComponent._configuration_serialnumber(info_dict)
        obj = cls(Equipment.from_info_dict(info_dict.get('equipment', None)),
                  ResponseStages.from_info_dict(
                    info_dict.get('response_stages', None)),
                  info_dict.get('sample_rate', None),
                  info_dict.get('delay_correction', 0))
        # print(obj)
        return obj

    def __repr__(self):
        s = f'Datalogger({type(self.equipment)}, {self.sample_rate:g}'
        if self.response_stages:
            s += f', {len(self.response_stages):d} x Stage'
        if self._config_description:
            s += f', config_description="{self._config_description}"'
        if self.delay_correction:
            s += f', delay_correction={self.delay_correction:g}'
        s += ')'
        return s


class Sensor(InstrumentComponent):
    """
    Sensor Instrument Component
    """
    def __init__(self,
                 equipment,
                 response_stages,
                 seed_band_base_code,
                 seed_instrument_code,
                 seed_orientations,
                 debug=False):
        """
        Constructor

        :param equipment: Equipment information
        :type equipment: ~class `obsinfo.instrumnetation.Equipment`
        :param response stages: sensor response stages
        :type equipment: ~class `obsinfo.instrumentation.ResponseStages`
        :param seed_band_base_code: SEED base code ("B" or "S") indicating
                                    instrument band.  Must be modified by
                                    obsinfo to correspond to output sample
                                    rate
        :type seed_band_base_code: str (len 1)
        :param seed_instrument code: SEED instrument code
        :type seed_instrument_code: str (len 1)
        :param seed_orientations: SEED orientation codes and corresponding
                                      azimuths and dips
        :type seed_orientations: dict

        """
        self.equipment = equipment
        self.response_stages = response_stages
        self.seed_band_base_code = seed_band_base_code
        self.seed_instrument_code = seed_instrument_code
        self.seed_orientations = seed_orientations  # dictionary
        if debug:
            print('sensor seed_orientations: {}'.format(
                self.seed_orientations))

    def __str__(self):
        return 'Sensor: {}, {:d} resp stages, seed code(s) {}{}[{}]'.format(
            self.equipment.model, len(self.response_stages),
            self.seed_band_base_code, self.seed_instrument_code,
            ''.join([k for (k, v) in self.seed_orientations.items()]))

    @classmethod
    def from_info_dict(cls, info_dict, debug=False):
        """
        Create instance from an info_dict
        """
        info_dict = InstrumentComponent._configuration_serialnumber(info_dict)
        if debug:
            print('Sensor info_dict:')
            pp.pprint(info_dict)
        seed_dict = info_dict.get('seed_codes', {})
        orients = {key: Orientation.from_info_dict(value)
                   for (key, value)
                   in seed_dict.get('orientation', {}).items()}
        if debug:
            print("sensor seed_codes['orientation']: {}".format(
                seed_dict.get('orientation', {})))
            print("orients: {}".format(orients))
        obj = cls(Equipment.from_info_dict(info_dict.get('equipment', None)),
                  ResponseStages.from_info_dict(
                    info_dict.get('response_stages', None)),
                  seed_dict.get('band_base', None),
                  seed_dict.get('instrument', None),
                  orients)
        # print(obj)
        return obj

    def __repr__(self):
        s = 'Sensor({}, "{}", "{}", {}x{}'.format(
            type(self.equipment), self.seed_band_base_code,
            self.seed_instrument_code, len(self.seed_orientations),
            type(self.seed_orientations))
        if self.response_stages:
            s += f', {len(self.response_stages):d} x list'
        if self.config_description:
            s += f', config_description={self.config_description}'
        s += ')'
        return s


class Preamplifier(InstrumentComponent):
    """
    Preamplifier Instrument Component
    """
    @classmethod
    def from_info_dict(cls, info_dict):
        """
        Create instance from an info_dict
        """
        if info_dict is None:
            return None
        info_dict = InstrumentComponent._configuration_serialnumber(info_dict)
        obj = cls(Equipment.from_info_dict(info_dict.get('equipment', None)),
                  ResponseStages.from_info_dict(
                    info_dict.get('response_stages', None)))
        # print(obj)
        return obj

    def __str__(self):
        return 'Preamplifier: {}, {:d} response stages'.format(
            self.equipment.model, len(self.response_stages))

    def __repr__(self):
        s = f'Preamplifier({type(self.equipment)}'
        if self.response_stages:
            s += f', {len(self.response_stages):d}xlist'
        if self.config_description:
            s += f', config_description={self.config_description}'
        s += ')'
        return s
