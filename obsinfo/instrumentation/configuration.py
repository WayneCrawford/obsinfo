"""
InstrumentationConfig class

Used to configure an Instrumentation
"""
# Standard library modules
import pprint

# Non-standard modules

# obsinfo modules
# from .instrument_component import (Datalogger, Sensor, Preamplifier,
#                                    Equipment, InstrumentComponent)
from .instrumentation import Instrumentation

pp = pprint.PrettyPrinter(indent=4, depth=2)


class InstrumentationConfiguration(object):
    """
    Instrumentation Configuration class
    """
    def __init__(self,
                 base_inst_dict,
                 config=None,
                 serial_number=None,
                 datalogger_config=None,
                 datalogger_serial_number=None,
                 channel_mods=None,
                 debug=False):
        """
        Constructor

        :param base_inst_dict: base Instrumentation dict
        :kind base_inst_dict: ~class `obsinfo.InfoDict`
        :param serial_number: instrumentation serial number
        :kind serial_number: str, optional
        :param datalogger_config: datalogger configuration
        :kind datalogger_config: str
        :param channel_mods: Modifications to each channel
        :kind channel_mods: ~class
            `obsinfo.instrumentation.ChannelConfigurationSelection`
        NON-IMPLEMENTED FIELDS
        :param config: instrumentation configuration
        :kind config: str, optional
        :param datalogger_serial_number: datalogger serial number
        :kind datalogger_serial_number: str, optional
        """
        self.inst_dict = base_inst_dict
        if debug:
            print('InstrumentConfiguration.__init__.inst_dict')
            pp.pprint(self.inst_dict)
        self.config = config
        self.serial_number = serial_number
        self.datalogger_config = datalogger_config
        self.datalogger_serial_number = datalogger_serial_number
        self.channel_mods = channel_mods

        # Assert non-implemented attributes are not called
        assert config is None, '"config" not implemented'
        assert datalogger_serial_number is None,\
            '"datalogger_serial_number" not implemented'

    def __repr__(self):
        s = f'InstrumentationConfiguration({type(self.inst_dict)}, '
        s += f'"{self.datalogger_config}"'
        if self.channel_mods:
            ", channel_mods={type(self.channel_mods)}"
        if self.serial_number:
            ', serial_number="{serial_number}"'
        return s

    @classmethod
    def from_info_dict(cls, info_dict):
        """
        Create object from an info_dict
        """
        obj = cls(info_dict.get('base', None),
                  info_dict.get('config', None),
                  info_dict.get('serial_number', None),
                  info_dict.get('datalogger_config', None),
                  info_dict.get('datalogger_serial_number', None),
                  ChannelConfigurationSelection.from_info_dict(
                    info_dict.get('channel_mods', None)))
        return obj

    def to_Instrumentation(self, debug=False):
        """
        Output instrumentation based on configurations and modifications
        """
        # Need to add in global config and serial number
        if self.config:
            self.inst_dict['configuration'] = self.config
        if self.serial_number:
            self.inst_dict['serial_number'] = self.serial_number

        # First, apply global configurations
        if debug:
            print('InstrumentConfiguration.to_Instrumentation.inst_dict')
            pp.pprint(self.inst_dict)
        # Next, apply channel-specific modifications
        if self.channel_mods:
            self.inst_dict = self.channel_mods.apply_base_channel_mods(
                self.inst_dict)

        if self.datalogger_config:
            if debug:
                print("self.inst_dict['base_channel']['datalogger']")
                pp.pprint(self.inst_dict['base_channel']['datalogger'])
                print("datalogger_config")
                print(self.datalogger_config)
                pp.pprint(self.datalogger_config)
            self.inst_dict['base_channel']['datalogger']['configuration'] =\
                self.datalogger_config
        if self.datalogger_serial_number:
            self.inst_dict['base_channel']['datalogger']['serial_number'] =\
                self.datalogger_serial_number

        # Next, apply channel-specific modifications
        if self.channel_mods:
            self.inst_dict = self.channel_mods.apply_das_channel_mods(
                self.inst_dict)

        return Instrumentation.from_info_dict(self.inst_dict)


class ChannelConfigurationSelection(object):
    """
    Select instrument channels for configuration
    """
    def __init__(self, base_channel=None, das_channels=None):
        """
        :param base_channel: modifications applied to all channels
        :kind base_channel:
            ~class `obsinfo.configuration.ChannelConfigurations`
        :param das_channels: modifications applied to specific channels
        :kind das_channels: dict of ~class
            `obsinfo.configuration.ChannelConfigurations`
        """
        self.base_channel = base_channel
        self.das_channels = das_channels

    @classmethod
    def from_info_dict(cls, info_dict, debug=False):
        """
        Create instance from an info_dict
        """
        if info_dict is None:
            return None
        if debug:
            print("ChannelConfigurationSelection: info_dict")
            print(info_dict)
        obj = cls(ChannelConfiguration.from_info_dict(
            info_dict.get('base_channel', None)),
                  {k: ChannelConfiguration.from_info_dict(v) for (k, v)
                   in info_dict.get('das_channels', None).items()})
        return obj

    def apply_base_channel_mods(self, info_dict):
        """
        apply channel modifications to an Instrumentation-level info_dict

        :param inst: info_dict at Instrumentation level
        :kind inst: ~class `obsinfo.info_dict.UpDict`
        """
        if self.base_channel:
            # modify the base_channel info_dict
            info_dict['base_channel'] = self.base_channel.apply_mods(
                info_dict['base_channel'])
        return info_dict

    def apply_das_channel_mods(self, info_dict):
        """
        apply channel modifications to an Instrumentation-level info_dict

        :param inst: info_dict at Instrumentation level
        :kind inst: ~class `obsinfo.info_dict.UpDict`
        """
        if self.das_channels:
            # modify the das_channels info_dict
            for das_key, value in self.das_channels.items():
                info_dict['das_channels'][das_key] =\
                    self.das_channels[das_key].apply_mods(
                        info_dict['das_channels'][das_key])
        return info_dict


class ChannelConfiguration(object):
    """
    Instrumentation channel modifications

    """
    def __init__(self,
                 sensor=None,
                 datalogger=None,
                 preamplifier=None,
                 location_code=None,
                 start_date=None,
                 end_date=None,
                 azimuth_deg=None):
        """
        :param sensor: modifications to channel's Sensor
        :param datalogger: modifications to channel's Datalogger
        :param preamplifier: modifications to channel's Preamplifier
        :kind sensor: ~class
            `obsinfo.configuration.InstrumentComponentConfiguration`
        :kind datalogger: ~class
            `obsinfo.configuration.InstrumentComponentConfiguration`
        :kind preamplifier: ~class
            `obsinfo.configuration.InstrumentComponentConfiguration`
        :param location_code: channel's location code
        :param start_date: channel's start_date
        :param end_date: channel's end_date
        :param azimuth_deg: azimuth and uncertainty
        :kind azimuth_deg: list [azimuth, uncertainty]
        """
        self.sensor = sensor
        self.datalogger = datalogger
        self.preamplifier = preamplifier
        # NOT IMPLEMENTED
        assert location_code is None, '"location_code" not implemented'
        assert start_date is None, '"start_date" not implemented'
        assert end_date is None, '"end_date" not implemented'
        assert azimuth_deg is None, '"end_date" not implemented'

    @classmethod
    def from_info_dict(cls, info_dict):
        """
        Create instance from an info_dict
        """
        if info_dict is None:
            return None
        obj = cls(info_dict.get('sensor', None),
                  info_dict.get('datalogger', None),
                  info_dict.get('preamplifier', None),
                  info_dict.get('location_code', None),
                  info_dict.get('start_date', None),
                  info_dict.get('end_date', None),
                  info_dict.get('azimuth.deg', None),
                  )
        return obj

    def apply_mods(self, info_dict):
        """
        apply modifications to a Channel-level info_dict

        :param info_dict: info_dict at Channel level
        :kind info_dict: ~class `obsinfo.info_dict.UpDict`
        """
        if self.sensor:
            info_dict['sensor'] = self.sensor.apply_mods(info_dict['sensor'])
        if self.datalogger:
            info_dict['datalogger'] =\
                self.sensor.apply_mods(info_dict['datalogger'])
        if self.datalogger:
            info_dict['preamplifier'] =\
                self.sensor.apply_mods(info_dict['preamplifier'])
        if self.location_code:
            info_dict['location_code'] = self.location_code
        if self.start_date:
            info_dict['start_date'] = self.start_date
        if self.end_date:
            info_dict['end_date'] = self.end_date
        if self.azimuth_deg:
            info_dict['sensor']['seed_orientations']['azimuth'] =\
                self.azimuth_deg[0]
            info_dict['sensor']['seed_orientations']['azimuth_uncertainty'] =\
                self.azimuth_deg[1]
        return info_dict


class InstrumentComponentConfiguration(object):
    """
    Instrument Component modifications

    Datalogger, Preamplifier or Sensor
    """
    def __init__(self,
                 base=None,
                 config=None,
                 serial_number=None):
        """
        :param base: specify an InstrumentComponent
        :kind base: ~class `obsinfo.info_dict.UpDict`
        :param config: Activate InstrumentComponent-level
            configuration_definition
        :kind config: str, optional
        :param serial_number: InstrumentComponent-level serial_number
        :kind serial_number: str, optional
        """
        self.base = base
        self.config = config
        self.serial_number = serial_number

    @classmethod
    def from_info_dict(cls, info_dict):
        """
        Create instance from an info_dict
        """
        obj = cls(info_dict.get('base', None),
                  info_dict.get('config', None),
                  info_dict.get('serial_number', None)
                  )
        return obj

    def apply_mods(self, info_dict):
        """
        Apply modifications to an InstrumentComponent-level info_dict

        Just modifies the info_dict "configuration" and "serial_number"
        parameters. These parameters are then read and interpreted by
        InstrumentComponent
        :param info_dict: info_dict at Instrumentation level
        :kind info_dict: ~class `obsinfo.info_dict.UpDict`
        """
        if self.base:   # substitute in a new component
            info_dict = self.base
        if self.config:
            info_dict['configuration'] = self.config
        if self.serial_number:
            info_dict['serial_number'] = self.serial_number
        return info_dict

#    @staticmethod
#    def _find_chan_loc(self, chan_loc, das_chan_dict):
#        """
#        Find a given channel_location in a list of das channels
#
#        :param chan_loc: channel_location (e.g. 'BHZ_00')
#        :kind: str
#        :param das_chan_dict: das_channels level dict
#        :kind inst: ~class `obsinfo.info_dict.UpDict`
#        :returns: matching das_channel key
#        """
#        a = chan_loc.split('_')
#        chan_code, loc = a[0], a[1]
#        base_chan_code = (Instrumentation.band_base_code(chan_code[0])
#                          + chan_code[1:])
#        for key, inst_chan in das_chan_dict.values():
#            scs = inst_chan['sensor']['seed_codes']
#            base_seed_code = (Instrumentation.band_base_code(scs['band_base']
#                              + scs['instrument'] + scs['orientation']))
#            if base_seed_code == base_chan_code:
#                if inst_chan['location_code']:
#                    if not inst_chan['location_code'] == loc:
#                        continue
#                return key
#        print(f'"{chan_loc}" not found!')
#        return None