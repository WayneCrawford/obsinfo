"""
Station class
"""
# Standard library modules

# Non-standard modules
import obspy.core.inventory.util as obspy_util

# obsinfo modules
from ..instrumentation import (Instrumentation, Instrument,
                               InstrumentationConfiguration)
# from ..misc import obspy_routines as oi_obspy


class Station(object):
    """
    Station. Equivalent to obspy/StationXML Station
    """
    def __init__(self,
                 site,
                 start_date,
                 end_date,
                 location_code,
                 locations,
                 instrumentations,
                 processing=None,
                 restricted_status='unknown',
                 comments=[]):
        """
        Constructor

        :param site: site description
        :kind site: str
        :param start_date: station start date
        :kind start_date: str
        :param end_date: station start date
        :kind end_date: str
        :param location_code: station location code (2 digits)
        :kind location_code: str
        :param locations: locations (names and positions)
        :kind locations: ~class `obsinfo.network.Locations`
        :param instrumentations: list of Instrumentation
        :kind instrumentations_configs: list
        :param processing: processing steps
        :kind processing: dict (maybe should have class?)
        :param restricted_status: "open", "closed", "partial", or "unknown"
        :kind restricted_status: str
        :param comments: text comments
        :type comments: list
        """
        self.site = site
        self.start_date = start_date
        self.end_date = end_date
        self.location_code = location_code
        self.locations = locations
        self.instrumentations = instrumentations
        self.processing = processing
        self.restricted_status = restricted_status
        self.comments = comments

    @classmethod
    def from_info_dict(cls, info_dict):
        """
        Create Station instance from an info_dict
        """
        obj = cls(info_dict['site'],
                  info_dict['start_date'],
                  info_dict['end_date'],
                  info_dict['location_code'],
                  {c: Location.from_info_dict(v)
                      for c, v in info_dict['locations'].items()},
                  [InstrumentationConfiguration.from_info_dict(x).to_Instrumentation()
                      for x in info_dict['instrumentations_configs']],
                  Processing.from_info_dict(info_dict.get('processing',
                                                          None)),
                  info_dict.get('restricted_status', None),
                  info_dict.get('commments', [])
                 )
        return obj

    def __repr__(self):
        s = f'Station({self.site}, {self.start_date}, {self.end_date}, '
        s += f'{self.location_code}, '
        s += f'{len(self.locations)} {type(Location)}s, '
        s += f'{len(self.instrumentations)} {type(Instrumentation)}s'
        if self.processing:
            s += f', {len(self.processing)} processing-steps'
        if not self.restricted_stations == "unknown":
            s += f', {self.restricted_status}'
        s += ')'
        return s

#     def to_obspy(self):
#         """
#         Create an obspy station object
#         """
#         # CREATE CHANNELS
#         # print(self)
#         channels = []
#         for instrumentation in self.instrumentations:
#             # resource_id = instrument.resource_id
#             for chan in instrumentation.das_channels:
#                 channels.append(chan.to_obspy())
#         # CREATE STATION
#         station_loc_code = self.location_code
#         if station_loc_code in self.locations:
#             sta_loc = self.locations[station_loc_code]
#             obspy_lon, obspy_lat = oi_obspy.lon_lats(sta_loc)
#         else:
#             print("No valid location code for station, either ", end='')
#             print("set station location_code or provide a location '00'")
#             sys.exit()
# 
#         obspy_comments = oi_obspy.comments(self.comments, self.processing,
#                                            station_loc_code, sta_loc)
# 
#         # DEFINE Operator
#         agency = self.operator["full_name"]
#         contacts = None
#         if "email" in self.operator:
#             contacts = [obspy_util.Person(emails=[self.operator["email"]])]
#         website = self.operator.get("website", None)
#         operator = obspy_util.Operator([agency], contacts, website)
# 
#         # print(obspy_comments)
#         sta = obspy_inventory.station.Station(
#             code=self.code,
#             latitude=obspy_lat,
#             longitude=obspy_lon,
#             elevation=obspy_types.FloatWithUncertaintiesAndUnit(
#                 sta_loc.elevation,
#                 lower_uncertainty=sta_loc.uncertainties_m["elev"],
#                 upper_uncertainty=sta_loc.uncertainties_m["elev"],
#             ),
#             channels=channels,
#             site=obspy_util.Site(getattr(self, "site", "")),
#             vault=sta_loc.vault,
#             geology=sta_loc.geology,
#             equipments=[x.equipment.to_obspy() for x in self.instrumentations],
#             operators=[operator],
#             creation_date=self.start_date,  # Needed to write StationXML
#             termination_date=self.end_date,
#             description=None,
#             comments=obspy_comments,
#             start_date=self.start_date if self.start_date else None,
#             end_date=self.end_date if self.end_date else None,
#             restricted_status=self.restricted_status,
#             alternate_code=None,
#             data_availability=None,
#         )
#         # print(sta)
#         return sta


class Location(object):
    """
    Location Class.
    """
    def __init__(self, latitude, longitude, elevation,
                 lat_uncertainty_m, lon_uncertainty_m, elev_uncertainty_m,
                 depth_m=None, geology='unknown', vault='',
                 localisation_method=''):
        """
        :param latitude: station latitude (degrees N)
        :type latitude: float
        :param longitude: station longitude (degrees E)
        :type longitude: float
        :param elevation: station elevation (meters above sea level)
        :type elevation: float
        :param lat_uncertainty_m: latitude uncertainty in METERS
        :param lon_uncertainty_m: longitude uncertainty in METERS
        :param elev_uncertainty_m: elevation uncertainty in METERS
        :param geology: site geology
        :type geology: str
        :param vault: vault type
        :type vault: str
        :param depth_m: depth of station beneath surface (meters)
        :type depth_m: float
        :param localisation_method: method used to determine position
        :type localisation_method: str
        """
        self.latitude = latitude
        self.longitude = longitude
        self.elevation = elevation
        self.lat_uncertainty_m = lat_uncertainty_m
        self.lon_uncertainty_m = lon_uncertainty_m
        self.elev_uncertainty_m = elev_uncertainty_m
        self.geology = geology
        self.vault = vault
        self.depth_m = depth_m
        self.localisation_method = localisation_method

    @classmethod
    def from_info_dict(cls, info_dict):
        """
        Create instance from an info_dict

        :param info_dict: info_dict at station:locations:{code} level
        :type info_dict: dict
        """
        assert 'base' in info_dict, 'No base in location'
        assert 'position' in info_dict, 'No position in location'
        position = info_dict['position']
        base = info_dict['base']
        obj = cls(position['lat'],
                  position['lon'],
                  position['elev'],
                  base['uncertainties.m']['lat'],
                  base['uncertainties.m']['lon'],
                  base['uncertainties.m']['elev'],
                  base.get('geology', ''),
                  base.get('vault', ''),
                  base.get('depth.m', None),
                  base.get('localisation_method', '')
                  )
        return obj

    def __repr__(self):
        discontinuous = False
        s = f'Location({self.latitude:g}, {self.longitude:g}, '
        s += f'{self.elevation:g}, {self.uncertainties_m}'
        if not self.geology == 'unknown':
            s += f', "{self.geology}"'
        else:
            discontinuous = True
        if self.vault:
            if discontinuous:
                s += f', vault="{self.vault}"'
            else:
                s += f', "{self.vault}"'
        else:
            discontinuous = True
        if self.depth_m:
            if discontinuous:
                s += f', depth_m={self.depth_m:g}'
            else:
                s += f', {self.depth_m}'
        else:
            discontinuous = True
        if self.localisation_method:
            if discontinuous:
                s += f', localisation_method="{self.localisation_method}"'
            else:
                s += f', "{self.localisation_method}"'
        else:
            discontinuous = True
        s += ')'
        return s


class Processing(object):
    """
    Processing Class.

    Saves a list of Processing steps
    For now, just stores the list
    """
    def __init__(self, the_list):
        """
        :param the_list: list of processing steps
        :type list: list
        """
        self.list = the_list

    @classmethod
    def from_info_dict(cls, info_dict):
        """
        Create instance from an info_dict

        Currently just passes the list that should be at this level
        :param info_dict: info_dict at station:processing level
        :type info_dict: dict
        """
        if not isinstance(info_dict, list):
            return None
        obj = cls(info_dict)
        return obj

    def __repr__(self):
        s = f'Processing({self.list})'
        return s
