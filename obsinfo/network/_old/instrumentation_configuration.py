"""
Station class
"""
# Standard library modules

# Non-standard modules

# obsinfo modules
from ..instrumentation import (Instrumentation, Instrument)


class Station(object):
    """
    Station. Equivalent to obspy/StationXML Station
    """
    def __init__(self, site, start_date, end_date, location_code,
                 locations, instruments, processing=None,
                 restricted_status='unknown'):
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
        :param instruments: list of Instrumentation
        :kind instruments: list
        :param processing: processing steps
        :kind processing: dict (maybe should have class?)
        :param restricted_status: "open", "closed", "partial", or "unknown"
        :kind restricted_status: str
        """
        self.site = site
        self.start_date = start_date
        self.end_date = end_date
        self.location_code = location_code
        self.locations = locations
        self.instruments = instruments
        self.processing = processing
        self.restricted_status = restricted_status

    @classmethod
    def from_info_dict(cls, info_dict):
        """
        Create Station instance from an info_dict
        """
        insts = info_dict['instruments']
        obj = cls(info_dict['site'],
                  info_dict['start_date'],
                  info_dict['end_date'],
                  info_dict['location_code'],
                  {c: Location.from_info_dict(v)
                   for c, v in info_dict['locations'].items()},
                  [Instrumentation.from_info_dict(x) for x in insts],
                   
                   
                  Processing.from_info_dict(info_dict.get('processing',
                                                          None)),
                  info_dict.get('restricted_status', None)
                  )
        return obj

    def __repr__(self):
        s = f'Station({self.site}, {self.start_date}, {self.end_date}, '
        s += f'{self.location_code}, '
        s += f'{len(self.locations)} {type(Location)}s, '
        s += f'{len(self.instruments)} {type(Instrumentation)}s'
        if self.processing:
            s += f', {len(self.processing)} processing-steps'
        if not self.restricted_stations == "unknown":
            s += f', {self.restricted_status}'
        s += ')'
        return s

    # def to_obspy(self):


class Location(object):
    """
    Location Class.
    """
    def __init__(self, latitude, longitude, elevation, uncertainties_m,
                 depth_m=None, geology='unknown', vault='',
                 localisation_method=''):
        """
        :param latitude: station latitude (degrees N)
        :type latitude: float
        :param longitude: station longitude (degrees E)
        :type longitude: float
        :param elevation: station elevation (meters above sea level)
        :type elevation: float
        :param uncertainties_m: uncertainties of [lat, lon, elev] in METERS
        :type uncertainties_m: list
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
        self.uncertainties_m = uncertainties_m
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
                  base['uncertainties.m'],
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
