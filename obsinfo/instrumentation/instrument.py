"""
Instrument class

nomenclature:
    An "Instrument" (measurement instrument) records one physical parameter
    A "Channel" is an Instrument + an orientation code and possibly
        starttime, endtime and location code
    An "Instrumentation" combines one or more measurement Channels
"""
# Standard library modules
import pprint
# import sys

# Non-standard modules

# obsinfo modules
from .instrument_component import (Datalogger, Sensor, Preamplifier)
# from ..info_dict import InfoDict
# from ..misc import misc as oi_misc
# from ..misc import obspy_routines

pp = pprint.PrettyPrinter(indent=4, depth=4, width=80)


class Instrument(object):
    """
    Instrument Class.

    An instrument is a combination of sensor, optional preamplifier, and
    datalogger
    """
    def __init__(self,
                 datalogger,
                 sensor,
                 preamplifier=None,
                 debug=False):
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
            self.response_stages += preamplifier.response_stages
        self.response_stages += datalogger.response_stages
        # Assemble component-specific values
        self.sample_rate = datalogger.sample_rate
        self.delay_correction = datalogger.delay_correction
        self.seed_band_base_code = sensor.seed_band_base_code
        self.seed_instrument_code = sensor.seed_instrument_code
        self.seed_orientations = sensor.seed_orientations
        if debug:
            print('Instrument __init__')
            print(datalogger)
            print(sensor)
            print(preamplifier)
            print('instrument seed_orientations: {}'.format(
                self.seed_orientations))

#     def __repr__(self):
#         s = f'Instrument({self.datalogger}, {self.sensor}'
#         if self.preamplifier:
#             s += f', {self.preamplifier}'
#         s += ')'
#         return s

    @classmethod
    def from_info_dict(cls, info_dict, debug=False):
        """
        Create instance from an info_dict

        :param info_dict: information dictionary containing datalogger,
                          sensor, and optionally preamplifier keys
        :type info_dict: InfoDict
        """
        assert 'datalogger' in info_dict, 'No datalogger specified'
        assert 'sensor' in info_dict, 'No sensor specified'
        if debug:
            print("Instrument.from_info_dict")
            pp.pprint(info_dict)
        obj = cls(Datalogger.from_info_dict(info_dict['datalogger']),
                  Sensor.from_info_dict(info_dict['sensor']),
                  Preamplifier.from_info_dict(info_dict.get('preamplifier',
                                                            None)))
        return obj
