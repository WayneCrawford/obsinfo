"""
Instrumentation and Instrument classes

nomenclature:
    An "Instrument" (measurement instrument) records one physical parameter
    A "Channel" is an Instrument + an orientation code and possibly
        starttime, endtime and location code
    An "Instrumentation" combines one or more measurement Channels
"""
# Standard library modules
import pprint

# Non-standard modules

# obsinfo modules
from .instrument_component import (InstrumentComponent, Datalogger, Sensor,
                                   Preamplifier)
from ..info_dict import InfoDict

pp = pprint.PrettyPrinter(indent=4, depth=4, width=80)


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
    def from_info_dict(cls, info_dict, debug=False):
        """
        Create Instrumentation instance from an info_dict
        """
        info_dict = InfoDict(info_dict)
        info_dict = InstrumentComponent._configuration_serialnumber(info_dict)
        info_dict = cls._complete_das_channels(info_dict)
        info_das = info_dict.get('das_channels', {})
        if debug:
            print("Instrumentation.from_info_dict info_dict['das_channels']")
            pp.pprint(info_das)
        obj = cls(info_dict.get('equipment', None),
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
        """
        assert 'das_channels' in info_dict,\
            f"No 'das_channels' key in {info_dict.keys()}"
        assert 'base_channel' in info_dict,\
            f"No 'base_channel' key in {info_dict.keys()}"
        for key, value in info_dict['das_channels'].items():
            # print(f'"{key}"')
            temp = InfoDict(value)
            info_dict['das_channels'][key] = InfoDict(
                info_dict['base_channel'])
            info_dict['das_channels'][key].update(temp)
        del info_dict['base_channel']
        return info_dict


class Channel(object):
    """
    Channnel Class.

    Corresponds to StationXML/obspy Channel, plus das_channel code
    """
    def __init__(self,
                 instrument,
                 das_channel,
                 orientation_code,
                 location_code=None,
                 startdate=None,
                 enddate=None):
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
        # print(instrument)
        assert orientation_code in instrument.seed_orientations,\
            print('orientation code "{}" not in seed_orientations: "{}"'.
                  format(orientation_code,
                         instrument.seed_orientations.keys()))
        self.orientation = instrument.seed_orientations[orientation_code]
        self.location_code = location_code
        self.startdate = startdate
        self.enddate = enddate

    @classmethod
    def from_info_dict(cls, info_dict, das_channel, debug=False):
        """
        Create instance from an info_dict

        :param info_dict: information dictionary at
                          instrument:das_channels level
        :type info_dict: dict
        :param das_channel: DAS channel code corresponding to this Channel
        :type das_channel: str
        """
        # print({'datalogger': info_dict['datalogger'],
        #        'sensor': info_dict['sensor'],
        #        'preamplifier': info_dict.get('preamplifier', None)})
        # print(InfoDict(datalogger=info_dict['datalogger'],
        #                sensor=info_dict['sensor'],
        #                preamplifier=info_dict.get('preamplifier', None))
        if debug:
            print("Channel.from_info_dict info_dict['sensor']")
            pp.pprint(info_dict['sensor'])
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

    @staticmethod
    def band_base_code(self, code):
        """
        Return the 'base' code ('B' or 'S') corresponding to a band code)
        """
        assert len(code) == 1,\
            f'Band code "{code}" is not a single letter'
        if code in "FCHBMLVURPTQ":
            return 'B'
        elif code in "GDES":
            return "S"
        else:
            raise NameError(f'Unknown band code: "{code}"')

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

#     def to_obspy(self, locations):
#         """
#         Convert to obspy Channel object
#     
#         :param chan: seed channel code
#         :param locations: dict with keys as location names
#         """
#         response = oi_obspy.response(self.instrument.response_stages.to_obspy())
#         loc_code = self.location_code
#         try:
#             location = self.locations[loc_code]
#         except KeyError:
#             print(f"location code {loc_code} not found in ")
#             print("self.locations, valid keys are:")
#             for key in self.locations.keys():
#                 print(key)
#             sys.exit(2)
#         obspy_lon, obspy_lat = oi_obspy.lon_lats(location)
#         azi, dip = oi_misc.get_azimuth_dip(
#             chan["sensor"].seed_codes, chan["orientation_code"])
#         start_date = self.start_date
#         end_date = self.end_date
#         if location.localisation_method in not None:
#             channel_comment = obspy_util.Comment(
#                 "Localised using : {}".format(
#                         location["localisation_method"])
#             )
#         else:
#             channel_comment = None
#         channel_code = make_channel_code(
#             chan["sensor"].seed_codes,
#             chan["band_code"],
#             chan["inst_code"],
#             chan["orientation_code"],
#             chan["datalogger"].sample_rate,
#         )
#         start_date = start_date_chan if start_date_chan else start_date
#         channel = obspy_inventory.channel.Channel(
#             code=channel_code,
#             location_code=loc_code,
#             latitude=obspy_lat,
#             longitude=obspy_lon,
#             elevation=obspy_types.FloatWithUncertaintiesAndUnit(
#                 location["position"]["elev"],
#                 lower_uncertainty=location["uncertainties.m"]["elev"],
#                 upper_uncertainty=location["uncertainties.m"]["elev"],
#             ),
#             depth=location["depth.m"],
#             azimuth=obspy_types.FloatWithUncertainties(
#                 azi[0],
#                 lower_uncertainty=azi[1] if len(azi) == 2 else 0,
#                 upper_uncertainty=azi[1] if len(azi) == 2 else 0,
#             ),
#             dip=dip[0],
#             types=["CONTINUOUS", "GEOPHYSICAL"],
#             sample_rate=chan["datalogger"].sample_rate,
#             clock_drift_in_seconds_per_sample=1
#             / (1e8 * float(chan["datalogger"].sample_rate)),
#             sensor=oi_obspy.equipment(chan["sensor"].equipment),
#             pre_amplifier=oi_obspy.equipment(
#                             chan["preamplifier"].equipment)
#             if "preamplifier" in chan
#             else None,
#             data_logger=oi_obspy.equipment(
#                             chan["datalogger"].equipment),
#             equipment=None,
#             response=response,
#             description=None,
#             comments=[channel_comment] if channel_comment else None,
#             start_date=start_date,
#             end_date=end_date_chan if end_date_chan else end_date,
#             restricted_status=None,
#             alternate_code=None,
#             data_availability=None,
#         )
#         return channel

    
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
            self.response_stages.extend(preamplifier.response_stages)
        self.response_stages.extend(datalogger.response_stages)
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
