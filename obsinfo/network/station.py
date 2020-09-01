"""
Station class
"""
# Standard library modules
import pprint
import json

# Non-standard modules
from obspy.core.inventory.util import Site
from obspy.core.inventory import Station as obspy_Station

# obsinfo modules
from ..instrumentation import InstrumentationConfiguration
from ..misc import obspy_routines
from .location import Location
from .processing import Processing

pp = pprint.PrettyPrinter()


class Station(object):
    """
    Station. Equivalent to obspy/StationXML Station
    """
    def __init__(self,
                 code,
                 site,
                 start_date,
                 end_date,
                 location_code,
                 locations,
                 instrumentations,
                 processing=None,
                 restricted_status='unknown',
                 comments=[],
                 extras=None):
        """
        Constructor

        :param code: station code
        :kind site: str
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
        :param extras: parameters not defined/handled by obsinfo
        :type extras: InfoDict
        """
        self.code = code
        self.site = site
        self.start_date = start_date
        self.end_date = end_date
        self.location_code = location_code
        self.locations = locations
        self.instrumentations = instrumentations
        self.processing = processing
        self.restricted_status = restricted_status
        self.comments = comments
        self.extras = extras

    @property
    def location(self):
        assert self.location_code in self.locations,\
            "station location code '{}' not a locations key '{}'".format(
                self.location_code, list(self.locations.keys()).join(','))
        return self.locations[self.location_code]

    @classmethod
    def from_info_dict(cls, code, info_dict):
        """
        Create Station instance from an info_dict

        :param code: station code (from info_dict key)
        :param info_dict: everything beneath the station code
        """
        obj = cls(
            code,
            info_dict['site'],
            info_dict['start_date'],
            info_dict['end_date'],
            info_dict['location_code'],
            {c: Location.from_info_dict(v)
                for c, v in info_dict['locations'].items()},
            [InstrumentationConfiguration.from_info_dict(x).
             to_Instrumentation() for x in
             info_dict['instrumentations_configs']],
            Processing.from_info_dict(info_dict.get('processing', None)),
            info_dict.get('restricted_status', None),
            info_dict.get('commments', []),
            info_dict.get('extras', None)
        )
        return obj

    def __repr__(self):
        s = f'Station({self.site}, {self.start_date}, {self.end_date}, '
        s += f'{self.location_code}, '
        s += f'{len(self.locations)} {type(Location)}s, '
        s += f'{len(self.instrumentations)} {type(self.instrumentations)}s'
        if self.processing:
            s += f', {len(self.processing)} processing-steps'
        if not self.restricted_stations == "unknown":
            s += f', {self.restricted_status}'
        s += ')'
        return s

    def to_obspy(self, facility):
        """
        Create an obspy station object

        :param facility: Facility information (usually in network.facility)
        """
        # CREATE CHANNELS
        channels = []
        for instrumentation in self.instrumentations:
            # resource_id = instrument.resource_id
            for chan in instrumentation.channels:
                channels.append(chan.to_obspy(self))
        # CREATE STATION
        obspy_comments = self.make_comments()

        # DEFINE Operator
        # agency = facility.full_name
        # contacts = None
        # if facility.email is not None:
        #     contacts = [Person(emails=[facility.email])]
        # website = facility.website
        # operator = Operator([agency], contacts, website)

        sta = obspy_Station(
            code=self.code,
            latitude=self.location.to_obspy_latitude(),
            longitude=self.location.to_obspy_longitude(),
            elevation=self.location.to_obspy_elevation(),
            channels=channels,
            site=Site(getattr(self, "site", "")),
            vault=self.location.vault,
            geology=self.location.geology,
            equipments=[x.equipment.to_obspy()
                        for x in self.instrumentations],
            operators=[facility.to_obspy()],
            creation_date=self.start_date,  # Needed to write StationXML
            termination_date=self.end_date,
            description=None,
            comments=obspy_comments,
            start_date=self.start_date if self.start_date else None,
            end_date=self.end_date if self.end_date else None,
            restricted_status=self.restricted_status,
            alternate_code=None,
            data_availability=None,
        )
        return sta

    def make_comments(self):
        """
        Create obspy comments from station information

        Includes information about fields not otherwise put in StationXML
            - self.extras elements as JSON strings,
            - self.processing steps as JSON strings,
            - self.location.location_method
        """
        obspy_comments = []
        if self.comments:
            for comment in self.comments:
                obspy_comments.append(self._make_comment(comment))
        if self.extras:  # Make a comment for each "extras" property
            for key, val in self.extras():
                obspy_comments.append(self._make_comment(
                    json.dumps({key: val})))
        if self.processing:  # Make a comment for each processing step
            for item in self.processing.list:
                obspy_comments.append(self._make_comment(json.dumps(item)))
        if self.location.localisation_method:
            obspy_comments.append(self._make_comment(
                f'Located using: {self.location.localisation_method}'))

        return obspy_comments

    @staticmethod
    def _make_comment(str):
        """
        Make an obspy comment from a string
        """
        return obspy_routines.make_comment_from_str(str)
