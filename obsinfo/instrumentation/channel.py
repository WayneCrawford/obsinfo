"""
Channel class

nomenclature:
    An "Instrument" (measurement instrument) records one physical parameter
    A "Channel" is an Instrument + an orientation code and possibly
        starttime, endtime and location code
    An "Instrumentation" combines one or more measurement Channels
"""
# Standard library modules
import pprint
import sys

# Non-standard modules
import obspy.core.util.obspy_types as obspy_types
# import obspy.core.inventory as obspy_inventory
from obspy.core.inventory.channel import Channel as obspy_channel

# obsinfo modules
from .instrument import Instrument
from .equipment import Equipment
# from ..info_dict import InfoDict
from ..misc import obspy_routines

pp = pprint.PrettyPrinter(indent=4, depth=4, width=80)


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
                 start_date=None,
                 end_date=None):
        """
        :param instrument: instrument description
        :type instrument: ~class `Instrument`
        :param das_channel: the DAS channel the instrument is on
        :type das_channel: str
        :param orientation_code: orientation code of this channel/instrument
        :type orientation_code: str
        :param location_code: channel location code (if different from station)
        :type location_code: str, opt
        :param start_date: channel start date (if different from station)
        :type start_date: str, opt
        :param end_date: channel end date (if different from station)
        :type end_date: str, opt
        """
        # print(instrument)
        assert orientation_code in instrument.seed_orientations,\
            print('orientation code "{}" not in seed_orientations: "{}"'.
                  format(orientation_code,
                         instrument.seed_orientations.keys()))

        self.instrument = instrument
        self.das_channel = das_channel
        self.orientation_code = orientation_code
        self.band_base_code = instrument.seed_band_base_code
        self.instrument_code = instrument.seed_instrument_code
        self.orientation_code = orientation_code
        self.orientation = instrument.seed_orientations[orientation_code]
        self.location_code = location_code
        self.start_date = start_date
        self.end_date = end_date

    def channel_code(self, sample_rate):
        """
        Return channel code for a given sample rate

        :param sample_rate: instrumentation sampling rate (sps)
        :kind sample_rate: float
        """
        return self.make_channel_code(sample_rate,
                                      self.band_base_code,
                                      self.instrument_code,
                                      self.orientation_code)

    def __repr__(self):
        s = f'Channel({type(self.instrument)}, "{self.das_channel}", '
        s += f'"{self.orientation_code}"'
        if self.location_code:
            s += f', {self.location_code}'
            write_keys = False
        else:
            write_keys = True
        if self.start_date:
            if write_keys:
                s += f', start_date={self.start_date}'
            else:
                s += f', {self.start_date}'
        else:
            write_keys = True
        if self.end_date:
            if write_keys:
                s += f', end_date={self.end_date}'
            else:
                s += f', {self.end_date}'
        else:
            write_keys = True
        s += ')'
        return s

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
        if debug:
            print("Channel.from_info_dict info_dict['sensor']")
            pp.pprint(info_dict['sensor'])

        # Transfer configurations to instrument components.
        if 'datalogger_config' in info_dict:
            info_dict['datalogger']['configuration'] =\
                info_dict['datalogger_config']
        if 'sensor_config' in info_dict:
            info_dict['sensor']['configuration'] =\
                info_dict['sensor_config']
        if 'preamplifier_config' in info_dict:
            info_dict['preamplifier']['configuration'] =\
                info_dict['preamplifier_config']
                
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

    def to_obspy(self, station):
        """
        Convert to obspy Channel object

        :param station: Station object, used for location names and possibly
            the station's location code and start/endtimes, if they are not
            specified for the channel.
        """
        # Values specfied at station level if not at channel level
        start_date = self.start_date if self.start_date else station.start_date
        end_date = self.end_date if self.end_date else station.end_date
        location_code = self.location_code if self.location_code\
            else station.location_code

        # Location-based values
        try:
            location = station.locations[location_code]
        except KeyError:
            print(f"location code {location_code} not found in ")
            print("locations, valid keys are: {}".format(
                list(station.locations.keys()).join(",")))
            sys.exit(2)
        azi, dip = self.get_azimuth_dip()
        if location.localisation_method is not None:
            channel_comments = [obspy_routines.make_comment_from_str(
                "Located using: {}".format(location.localisation_method))]
        else:
            channel_comments = None

        # Instrument values
        inst = self.instrument
        response = inst.response_stages.to_obspy(inst.delay_correction)
        pre_amplifier = None
        if isinstance(inst.equipment_preamplifier, Equipment):
            pre_amplifier = inst.equipment_preamplifier.to_obspy()
        clock_drift_sps = 1 / (1e8*float(inst.sample_rate))

        # Make obspy Channel object
        channel = obspy_channel(
            code=self.channel_code(self.instrument.sample_rate),
            location_code=location_code,
            latitude=location.to_obspy_latitude(),
            longitude=location.to_obspy_longitude(),
            elevation=location.to_obspy_elevation(),
            depth=location.depth_m,
            azimuth=azi,
            dip=dip,
            types=["CONTINUOUS", "GEOPHYSICAL"],
            sample_rate=inst.sample_rate,
            clock_drift_in_seconds_per_sample=clock_drift_sps,
            sensor=inst.equipment_sensor.to_obspy(),
            pre_amplifier=pre_amplifier,
            data_logger=inst.equipment_datalogger.to_obspy(),
            equipments=None,
            response=response,
            description=None,
            comments=channel_comments,
            start_date=start_date,
            end_date=end_date,
            restricted_status=None,
            alternate_code=None,
            data_availability=None
        )
        return channel

    def _get_band_code(self, sample_rate):
        """
        Return the Channel's band code

        :param sample_rate: sample rate (sps)
        """
        return self.get_band_code(self.band_base_code, sample_rate)

    def get_azimuth_dip(self):
        """
        Returns azimuth and dip [value, error] pairs
        """
#         if self.orientation_code == None\
#             and len(self.instrument.seed_orientations) == 1:
#                 orientation_code = list(
#                     self.instrument.seed_orientations.keys())[0]
        assert self.orientation_code in self.instrument.seed_orientations,\
            'orientation code "{}" not in instrument.seedorientations'.format(
                self.orientation_code)
        oc = self.instrument.seed_orientations[self.orientation_code]
        azimuth = oc.azimuth
        dip = oc.dip
        return azimuth, dip

    @staticmethod
    def get_band_base_code(code):
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

    @staticmethod
    def get_band_code(band_base_code, sample_rate):
        """
        Return the channel band code

        :param band_base_code: 'B' or 'S'
        :param sample_rate: sample rate (sps)
        """
        assert len(band_base_code) == 1,\
            f'Band base code "{band_base_code}" is not a single letter'
        if band_base_code in "FCHBMLVURPTQ":
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
        elif band_base_code in "GDES":
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
            raise NameError(f'Unknown band base code: "{band_base_code}"')

    @staticmethod
    def make_channel_code(sample_rate, band_base_code, instrument_code,
                          orientation_code):
        """
        Make a channel code

        :param sample_rate: sample rate (sps)
        :param band_base_code: "B" (broadband) or "S" (short period)
        :param instrument code: instrument code
        :param orientation code: orientation code

        >> A = make_channel_code(400, 'S', 'H', 'Z')
        >> A == 'DHZ'
        """
        assert len(band_base_code) == 1,\
            f'Band code "{band_base_code}" is not a single letter'
        assert len(instrument_code) == 1,\
            f'Instrument code "{instrument_code}" is not a single letter'
        assert len(orientation_code) == 1,\
            f'Orientation code "{orientation_code}" is not a single letter'
        band_code = Channel.get_band_code(band_base_code, sample_rate)
        return band_code + instrument_code + orientation_code
