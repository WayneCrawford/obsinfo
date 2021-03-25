"""
Print complete stations from information in network.yaml file

nomenclature:
    A "measurement instrument" is a means of recording one physical parameter,
        from sensor through dac
    An "instrument" is composed of one or more measurement instruments

I need to modify the code so that it treats a $ref as a placeholder for the
associated object
"""
# Standard library modules
import os.path

# Non-standard modules
import obspy.core.inventory as obspy_inventory
from obspy.core.inventory.util import Operator
import yaml
# import obspy.core.inventory.util as obspy_util
# from obspy.core.utcdatetime import UTCDateTime

from ..misc.info_files import load_information_file
from ..misc import FDSN as oi_FDSN
from .station import station as oi_station
from .util import create_comments

###############################################################################


class network:
    """ Everything contained in a network.yaml file

        Has two subclasses:
            stations (.station)
            network_info (..misc.network_info)
    """

    def __init__(self, filename, referring_file=None, debug=False):
        """ Reads from a network information file

        should also be able to specify whether or not it has read its sub_file
        """
        root, path = load_information_file(filename, referring_file)
        self.basepath = path
        self.revision = root["revision"].copy()
        self.format_version = root["format_version"]
        net = root["network"]
        self.facility_ref_name = net["facility"]["reference_name"]
        self.facility_full_name = net["facility"].get("full_name", None)
        self.campaign = net["campaign_reference_name"]
        self.network_info = oi_FDSN.network_info(net["general_information"])
        self.instrumentation_file = net["instrumentation"]
        if not self.instrumentation_file["$ref"]:
            print(
                "No instrumentation file specfied, cannot create StationXML"
            )
        self.stations = dict()
        if debug:
            print("in network:__init__()")
        for code, station in root["network"]["stations"].items():
            if debug:
                print(f"net={self.network_info.code},station={code}")
            self.stations[code] = oi_station(station, code,
                                             self.network_info.code)
            if self.instrumentation_file["$ref"]:
                # Fill the instrument
                self.stations[code].fill_instrument(
                    self.instrumentation_file, referring_file=self.basepath
                )

            if debug:
                print(self.stations[code])

    def __repr__(self):
        return "<{}: code={}, facility={}, campaign={}, {:d} stations>".format(
            __name__,
            self.network_info.code,
            self.facility_ref_name,
            self.campaign,
            len(self.stations),
        )

    def __make_obspy_inventory(self, stations=None, source=None, debug=False):
        """
        Make an obspy inventory object with a subset of stations

        stations = list of obs-info.OBS-Station objects
        source  =  value to put in inventory.source
        """
        my_net = self.__make_obspy_network(stations)
        if not source:
            if self.facility_full_name:
                source = self.facility_full_name
            else:
                source = (
                    self.revision["author"]["first_name"]
                    + " "
                    + self.revision["author"]["last_name"]
                )
        my_inv = obspy_inventory.inventory.Inventory([my_net], source)
        return my_inv

    def __make_obspy_network(self, stations, debug=False):
        """Make an obspy network object with a subset of stations"""
        obspy_stations = []
        for station in stations:
            obspy_stations.append(station.make_obspy_station())

        temp = self.network_info.comments
        comments = None
        if temp:
            comments = create_comments(temp)
        
        # Create Operator
        my_op = Operator(self.facility_full_name, None,None)
        
        my_net = obspy_inventory.network.Network(
            self.network_info.code,
            obspy_stations,
            description=self.network_info.description,
            comments=comments,
            start_date=self.network_info.start_date,
            end_date=self.network_info.end_date,
            operators=[my_op]
        )
        return my_net

    def write_stationXML(self, station_name, destination_folder=None,
                         quiet=False, debug=False):
        station = self.stations[station_name]
        if debug:
            print("Creating obsPy inventory object")
        my_inv = self.__make_obspy_inventory([station])
        if debug:
            print(yaml.dump(my_inv))
        if not destination_folder:
            destination_folder = "."
        fname = os.path.join(
            destination_folder,
            "{}.{}.STATION.xml".format(self.network_info.code, station_name),
        )
        if not quiet:
            print("Writing to", fname)
        my_inv.write(fname, "STATIONXML")

    def write_station_XMLs(self, destination_folder=None):
        for station_name in self.stations:
            self.write_station(station_name, destination_folder)


def _make_stationXML_script(argv=None):
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
    net = network(args.network_file)
    # print(net)

    for station in net.stations:
        net.write_stationXML(station, args.dest_path, quiet=args.quiet)
