"""
Instrumentation and Instrument classes

nomenclature:
    An "Instrument" (measurement instrument) records one physical parameter
    A "Channel" is an Instrument + an orientation code and possibly starttime,
        endtime and location code
    An "Instrumentation" combines one or more measurement Channels
"""
# Standard library modules
import pprint

# Non-standard modules

# obsinfo modules
from .channel import Channel
from .instrument_component import InstrumentComponent
from .equipment import Equipment
from ..info_dict import InfoDict

pp = pprint.PrettyPrinter(depth=4, width=170)


class Instrumentation(object):
    """
    One or more Instrument Channels. Part of an obspy/StationXML Station
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
    def from_info_dict(cls, info_dict, debug=False):
        """
        Create Instrumentation instance from an info_dict
        """
        info_dict = InfoDict(info_dict)

        # Transform the InfoDict according to configuration, serial number
        # and base/das_channel specifications
        info_dict = InstrumentComponent._configuration_serialnumber(info_dict)
        info_dict = cls._complete_das_channels(info_dict)
        info_dict_das = info_dict.get('das_channels', {})

        if debug:
            print("Instrumentation.from_info_dict info_dict['das_channels']")
            pp.pprint(info_dict_das)
        obj = cls(Equipment.from_info_dict(info_dict.get('equipment', None)),
                  [Channel.from_info_dict(v, k)
                   for k, v in info_dict_das.items()])
        return obj

    def __repr__(self):
        s = f'Instrumentation(equipment={type(self.equipment)}, '
        s += f'channels=[{len(self.channels)} {type(self.channels[0])}]'
        return s

    @staticmethod
    def _complete_das_channels(info_dict):
        """
        Complete 'das_channels' using 'base_channel'.

        Fields must be at the top level.
        'base_channel' is deleted
        if 'das_channel' contains a complete sensor, preamplifier or
            datalogger (signified by 'equipment', 'configuration' and
            'configuration_definition' fields) then base_channel 'equipment',
            'configuration', 'serial_number_modifications', 'configuration_definitions' 
            and '{component}_config' are not copied over
        """
        assert 'das_channels' in info_dict,\
            f"No 'das_channels' key in {info_dict.keys()}"
        assert 'base_channel' in info_dict,\
            f"No 'base_channel' key in {info_dict.keys()}"
        for key, das in info_dict['das_channels'].items():
            # print(f'"{key}"')
            # das = InfoDict(value)
            base = Instrumentation._clean_base_attributes(
                info_dict['base_channel'], das)
            info_dict['das_channels'][key] = base
            info_dict['das_channels'][key].update(das)
        del info_dict['base_channel']
        return info_dict

    @staticmethod
    def _clean_base_attributes(base_channel, das_channel):
        """
        Removes base_channel keys that conflict with das_channel
        
        If a das_channel component has "equipment", "configuration" and
        "configuration_definitions" keys, removes those keys plus
        "serial_number_modification" and "{component}_config" from the equivalent
        base_channel component

        :param base_channel: base channel definition
        :type base_channel: InfoDict
        :param das_channel: das channel definition/modifier
        :type das_channel: InfoDict
        :returns: modified base_channel
        :rtype: InfoDict
        """
        base = InfoDict(base_channel)
        for comp in ['sensor', 'datalogger', 'preamplifier']:
            if comp in das_channel and comp in base:
                if ('equipment' in das_channel[comp]
                        and 'configuration' in das_channel[comp]
                        and 'configuration_definitions' in das_channel[comp]):
                    del base[comp]['equipment']
                    del base[comp]['configuration']
                    del base[comp]['configuration_definitions']
                    if 'serial_number_modifications' in base[comp]:
                        del base[comp]['serial_number_modifications']
                    if comp + '_config' in base:
                        del base[comp + '_config']
        return base
