"""
station object in network information file
"""
# Standard library modules
import sys

# Non-standard modules
import yaml
import obspy.core.util.obspy_types as obspy_types
import obspy.core.inventory as obspy_inventory
import obspy.core.inventory.util as obspy_util
from obspy.core.utcdatetime import UTCDateTime

from ..misc import misc as oi_misc
from ..misc import obspy as oi_obspy
# from .util import create_comments
from ..misc.misc import make_channel_code
from ..instrumentation import instrument as oi_instrument


class station:
    """a station from the network information file"""

    def __init__(self, station_dict, station_code, network_code, debug=False):
        """ Create a station object directly from a network file's
        station: element """
        self.comments = station_dict.get("comments", [])
        self.site = station_dict["site"]
        self.start_date = station_dict["start_date"]
        self.end_date = station_dict["end_date"]
        self.instruments = station_dict["instruments"]
        self.station_location = station_dict["station_location"]
        self.locations = station_dict["locations"]
        self.processing = station_dict.get("processing", [])
        self.supplements = station_dict.get("supplements", [])  # ??
        self.code = station_code
        self.network_code = network_code
        if "sensors" in station_dict:
            self.sensors = station_dict["sensors"]
        else:
            self.sensors = None

    def __repr__(self):
        txt = "< {}: code={}, ".format(__name__, self.code)
        for inst in self.instruments:
            if hasattr(inst, "das_components"):
                txt += "instrument={} >".format(inst)
            else:
                txt += "instrument= ['{}','{}']".format(
                    inst["reference_code"], inst["serial_number"]
                )
        return txt

    def fill_instrument(self, instrument_file, referring_file=None):
        """ Fills in instrument information """
        self.partial_fill_instruments(instrument_file, referring_file)
        if self.sensors:
            print("Adding custom sensors")
            self.instruments.modify_sensors(self.sensors, referring_file)
        for inst in self.instruments:
            inst.fill_responses()

    def partial_fill_instruments(self, instrument_file,
                                 referring_file=None, debug=True):
        """ Converts network file instrument objects to Instrument class.
            ??? Does not fill in component responses ??? """
        instruments = []
        for inst_dict in self.instruments:
            inst = oi_instrument(instrument_file["$ref"], inst_dict,
                                 referring_file=referring_file)
            inst.load_components(inst.components_file, inst.basepath)
            self.operator = inst.facility  # à verifier??
            # instruments[inst_dict["reference_code"]]=inst
            instruments.append(inst)
        self.instruments = instruments

    def make_obspy_station(self, debug=False):
        """
        Create an obspy station object from a fully informed station
        """
        # CREATE CHANNELS

        # if debug:
        #    print(self)
        channels = []
        for instrument in self.instruments:
            # resource_id = instrument.resource_id
            for key, chan in instrument.das_components.items():
                if debug:
                    print(key)
                    print(yaml.dump(chan))
                response = oi_obspy.response(chan["response"])
                # loc_code=key.split(':')[1]
                loc_code = chan["location_code"]
                try:
                    location = self.locations[loc_code]
                except KeyError:
                    print(f"location code {loc_code} not found in ")
                    print("self.locations, valid keys are:")
                    for key in self.locations.keys():
                        print(key)
                    sys.exit(2)
                obspy_lon, obspy_lat = oi_obspy.lon_lats(location)
                azi, dip = oi_misc.get_azimuth_dip(
                    chan["sensor"].seed_codes, chan["orientation_code"]
                )
                start_date = None
                end_date = None
                start_date_chan = None
                end_date_chan = None
                # Give at least 3 seconds margin around start and end dates

                if "start_date" in chan:
                    start_date_chan = UTCDateTime(chan["start_date"])

                if self.start_date:
                    start_date = UTCDateTime(self.start_date)

                if "end_date" in chan:
                    end_date_chan = UTCDateTime(chan["end_date"])

                if self.end_date:

                    end_date = UTCDateTime(self.end_date)

                if debug:
                    print(key)
                    print(yaml.dump(chan))
                # print(location)
                if "localisation_method" in location:
                    channel_comment = obspy_util.Comment(
                        "Localised using : {}".format(
                                location["localisation_method"])
                    )
                else:
                    channel_comment = None
                channel_code = make_channel_code(
                    chan["sensor"].seed_codes,
                    chan["band_code"],
                    chan["inst_code"],
                    chan["orientation_code"],
                    chan["datalogger"].sample_rate,
                )
                start_date = start_date_chan if start_date_chan else start_date
                channel = obspy_inventory.channel.Channel(
                    code=channel_code,
                    location_code=loc_code,
                    latitude=obspy_lat,
                    longitude=obspy_lon,
                    elevation=obspy_types.FloatWithUncertaintiesAndUnit(
                        location["position"]["elev"],
                        lower_uncertainty=location["uncertainties.m"]["elev"],
                        upper_uncertainty=location["uncertainties.m"]["elev"],
                    ),
                    depth=location["depth.m"],
                    azimuth=obspy_types.FloatWithUncertainties(
                        azi[0],
                        lower_uncertainty=azi[1] if len(azi) == 2 else 0,
                        upper_uncertainty=azi[1] if len(azi) == 2 else 0,
                    ),
                    dip=dip[0],
                    types=["CONTINUOUS", "GEOPHYSICAL"],
                    sample_rate=chan["datalogger"].sample_rate,
                    clock_drift_in_seconds_per_sample=1
                    / (1e8 * float(chan["datalogger"].sample_rate)),
                    sensor=oi_obspy.equipment(chan["sensor"].equipment),
                    pre_amplifier=oi_obspy.equipment(
                                    chan["preamplifier"].equipment)
                    if "preamplifier" in chan
                    else None,
                    data_logger=oi_obspy.equipment(
                                    chan["datalogger"].equipment),
                    equipments=None,
                    response=response,
                    description=None,
                    comments=[channel_comment] if channel_comment else None,
                    start_date=start_date,
                    end_date=end_date_chan if end_date_chan else end_date,
                    restricted_status=None,
                    alternate_code=None,
                    data_availability=None,
                )
                channels.append(channel)
                if debug:
                    print(yaml.dump(channel))
            # CREATE STATION
            station_loc_code = self.station_location  # david
            if station_loc_code in self.locations:
                sta_loc = self.locations[station_loc_code]
                obspy_lon, obspy_lat = oi_obspy.lon_lats(sta_loc)
            else:
                print("No valid location code for station, either ", end='')
                print("set station_location_code or provide a location '00'")
                sys.exit()

            obspy_comments = oi_obspy.comments(
                self.comments,
                self.processing,
                self.supplements,
                station_loc_code,
                sta_loc,
            )

            # DEFINE Operator
            agency = self.operator["full_name"]
            contacts = None
            if "email" in self.operator:
                contacts = [obspy_util.Person(emails=[self.operator["email"]])]
            website = self.operator.get("website", None)
            operator = obspy_util.Operator(agency, contacts, website)

            if debug:
                print(obspy_comments)
            sta = obspy_inventory.station.Station(
                code=self.code,
                latitude=obspy_lat,
                longitude=obspy_lon,
                elevation=obspy_types.FloatWithUncertaintiesAndUnit(
                    sta_loc["position"]["elev"],
                    lower_uncertainty=sta_loc["uncertainties.m"]["elev"],
                    upper_uncertainty=sta_loc["uncertainties.m"]["elev"],
                ),
                channels=channels,
                site=obspy_util.Site(getattr(self, "site", "")),
                vault=sta_loc["vault"],
                geology=sta_loc["geology"],
                equipments=[oi_obspy.equipment(instrument.equipment)
                            for instrument in self.instruments],
                operators=[operator],
                creation_date=start_date,  # Needed to write StationXML
                termination_date=end_date,
                description=None,
                comments=obspy_comments,
                start_date=start_date if start_date else None,
                end_date=end_date if end_date else None,
                restricted_status=None,
                alternate_code=None,
                data_availability=None,
            )
        if debug:
            print(sta)
        return sta
