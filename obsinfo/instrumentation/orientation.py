"""
InstrumentComponent class and subclasses.

No StationXML equivalent.
"""
# Standard library modules

# Non-standard modules
from obspy.core.util.obspy_types import FloatWithUncertaintiesAndUnit as\
    obspy_FloatWithUncertaintiesAndUnit


class Orientation(object):
    """
    Class for sensor orientations
    """
    def __init__(self, azimuth, azimuth_uncertainty, dip, dip_uncertainty):
        """
        Constructor

        :param azimuth: azimuth (clockwise from north, degrees)
        :param azimuth_uncertainty: degrees
        :param dip: dip (degrees, -90 to 90: positive=down, negative=up)
        :param dip_uncertainty: degrees
        """
        self.azimuth = obspy_FloatWithUncertaintiesAndUnit(
            azimuth, lower_uncertainty=azimuth_uncertainty,
            upper_uncertainty=azimuth_uncertainty, unit='degrees')
        self.dip = obspy_FloatWithUncertaintiesAndUnit(
            dip, lower_uncertainty=dip_uncertainty,
            upper_uncertainty=dip_uncertainty, unit='degrees')

    @classmethod
    def from_info_dict(cls, info_dict):
        """
        Create Orientation instance from an info_dict
        """
        azimuth, azi_uncert = info_dict.get('azimuth.deg', [None, None])
        dip, dip_uncert = info_dict.get('dip.deg', [None, None])
        obj = cls(azimuth, azi_uncert, dip, dip_uncert)
        return obj
