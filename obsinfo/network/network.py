"""
Network class
"""
# Standard library modules
import os.path

# Non-standard modules
from obspy.core.inventory import Network as obspyNetwork
from obspy.core.inventory import Inventory as obspyInventory

# obsinfo modules
from ..misc import obspy_routines
from .facility import Facility
from .station import Station
from ..misc.info_files import read_info_file


class Network(object):
    """
    corresponds to StationXML network
    """
    def __init__(self, code, name, start_date, end_date,
                 description='', stations=[], facility=None,
                 campaign='', comments=[]):
        """
        Constructor

        :param code: FDSN network code
        :param name: FDSN network name
        :param start_date: FDSN network start_date
        :param end_date: FDSN network end_date
        :param description: FDSN network description
        :param stations: list of obsinfo Stations
        :param facility: Facility class
        :param campaign: campaign reference name
        :param comments: list of strings
        """
        self.code = code
        self.name = name
        self.start_date = start_date
        self.end_date = end_date
        self.description = description
        self.stations = stations
        self.facility = facility
        self.campaign = campaign
        self.comments = comments

    @classmethod
    def from_info_dict(cls, info_dict):
        """
        Create Instrumentation instance from an info_dict
        """
        net_info = info_dict['network_info']
        obj = cls(net_info['code'],
                  net_info.get('name', ''),
                  net_info['start_date'],
                  net_info['end_date'],
                  net_info.get('description', ''),
                  [Station.from_info_dict(k, v)
                  for k, v in info_dict['stations'].items()],
                  Facility.from_info_dict(info_dict['facility']),
                  info_dict['campaign_ref_name'],
                  net_info.get('comments', []))
        return obj

    def __repr__(self):
        s = 'Network("{}", "{}", "{}", "{}", "{}"'.format(
            self.code, self.name, self.start_date,
            self.end_date, self.description)
        if self.stations:
            s += ', <list of {}>'.format(type(self.stations[0]))
        if self.facility:
            s += ', {}, "{}", "{}")'.format(type(self.facility))
        if self.comments:
            s += ', "{}"'.format(self.campaign)
        if self.campaign:
            s += ', <{:d}-list of str>'.format(len(self.comments))
        s += ')'
        return s

    def to_obspy(self):
        """
        Create an obspy station object
        """
        # CREATE COMMENTS
        obspy_comments = []
        if self.comments:
            for comment in self.comments:
                obspy_comments.append(obspy_routines.make_comment_from_str(
                    comment))

        return obspyNetwork(
            code=self.code,
            stations=[x.to_obspy(self.facility) for x in self.stations],
            total_number_of_stations=None,
            selected_number_of_stations=None,
            description=self.description,
            comments=obspy_comments,
            start_date=self.start_date,
            end_date=self.end_date,
            restricted_status=None,
            alternate_code=None,
            historical_code=None,
            data_availability=None,
            identifiers=None,
            operators=[self.facility.to_obspy()],
            source_id=None
        )

    def to_stationXML(self, by_station=True, source=None,
                      destination_folder=None):
        """
        Write to StationXML file

        :param by_station: save one file per Station
        :kind by_station: bool, optional
        :param source: value for <Source> field of stationXML
            will use facility.full_name if none provided
        :kind source: str, optional
        :param destination_folder: Name of destination folder
        :type destination_folder: str, optional
        :returns: output filename(s)
        :rtype: list of str
        """
        if destination_folder is None:
            destination_folder = "."
        if source is None:
            source = self.facility.full_name

        inv = obspyInventory(networks=[self.to_obspy()], source=source)
        fnames = []
        if by_station:
            for station_code in [x.code for x in self.stations]:
                fname = os.path.join(
                    destination_folder,
                    "{}.{}.STATION.xml".format(inv[0].code, station_code))
                inv_sta = inv.select(station=station_code)
                inv_sta.write(fname, "STATIONXML")
                fnames.append(fname)
        else:
            fname = os.path.join(
                destination_folder,
                "{}.STATION.xml".format(inv[0].code))
            inv = obspyInventory(
                networks=[self.to_obspy()],
                source='obsinfo')
            inv.write(fname, "STATIONXML")
            fnames.append(fname)
        return fnames


def make_stationXML_script(argv=None):
    """
    Creates StationXML files from a network file and instrumentation file tree
    """
    from argparse import ArgumentParser

    parser = ArgumentParser(prog="obsinfo-makeSTATIONXML", description=__doc__)
    parser.add_argument("network_file", help="Network information file")
    parser.add_argument("-d", "--dest_path",
                        help="Destination folder for StationXML files")
    parser.add_argument("-q", "--quiet", action="store_true",
                        help="Run silently")
    # parser.add_argument( '-v', '--verbose',action="store_true",
    #            help='increase output verbosiy')

    args = parser.parse_args(argv)

    if args.dest_path:
        if not os.path.exists(args.dest_path):
            os.mkdir(args.dest_path)

    # READ IN NETWORK INFORMATION
    A = read_info_file(args.network_file)
    # print(A['network'])
    net = Network.from_info_dict(A['network'])
    # print(net)

    fnames = net.to_stationXML(destination_folder=args.dest_path)
    if not args.quiet:
        print('Wrote to ' + ', '.join(fnames))
