"""
Station class
"""
# Standard library modules
import math

# Non-standard modules
from obspy.core.util.obspy_types import FloatWithUncertaintiesAndUnit
import obspy.core.inventory.util as obspy_util
#
# obsinfo modules
# from ..instrumentation import InstrumentationConfiguration
# from ..misc import obspy_routines as oi_obspy


class Location(object):
    """
    Location Class.
    """
    def __init__(self, latitude, longitude, elevation,
                 lat_uncertainty_m, lon_uncertainty_m, elev_uncertainty_m,
                 geology='unknown', vault='', depth_m=None,
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
        self.latitude = float(latitude)
        self.longitude = float(longitude)
        self.elevation = float(elevation)
        self.lat_uncertainty_m = float(lat_uncertainty_m)
        self.lon_uncertainty_m = float(lon_uncertainty_m)
        self.elev_uncertainty_m = float(elev_uncertainty_m)
        self.geology = geology
        self.vault = vault
        self.depth_m = float(depth_m)
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

    def to_obspy_latitude(self, debug=False):
        """ Calculate obspy util.Latitude"""
        meters_per_degree_lat = 1852.0 * 60.0
        value = float(self.latitude)
        uncert = self.lat_uncertainty_m / meters_per_degree_lat
        # REDUCE UNCERTAINTIES TO 3 SIGNIFICANT FIGURES
        uncert = float("{:.3g}".format(uncert))
        if debug:
            print(f"{value:.3f}+-{uncert:.5f}")
        obspy_obj = obspy_util.Latitude(value,
                                        lower_uncertainty=uncert,
                                        upper_uncertainty=uncert)
        return obspy_obj

    def to_obspy_longitude(self, debug=False):
        """ Return obspy util.Longitude"""
        latitude = float(self.latitude)
        meters_per_degree_lon =\
            1852.*60. * math.cos(latitude * math.pi/180.)
        value = float(self.longitude)
        uncert = self.lon_uncertainty_m / meters_per_degree_lon
        # REDUCE UNCERTAINTIES TO 3 SIGNIFICANT FIGURES
        uncert = float("{:.3g}".format(uncert))
        if debug:
            print(f"{value:.3f}+-{uncert:.5f}")
        obspy_obj = obspy_util.Longitude(value,
                                         lower_uncertainty=uncert,
                                         upper_uncertainty=uncert)
        return obspy_obj

    def to_obspy_elevation(self):
        """ Make obspy util.Elevation"""
        return FloatWithUncertaintiesAndUnit(
            self.elevation,
            lower_uncertainty=self.elev_uncertainty_m,
            upper_uncertainty=self.elev_uncertainty_m)

    def __repr__(self):
        discontinuous = False
        s = f'Location({self.latitude:g}, {self.longitude:g}, '
        s += f'{self.elevation:g}, {self.lat_uncertainty_m:g}, '
        s += f'{self.lon_uncertainty_m:g}, {self.elev_uncertainty_m}, '
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
