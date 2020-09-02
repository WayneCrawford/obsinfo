"""
Validate information files

"""
# Standard library modules
import pprint
# import os.path
# import sys

# obsinfo modules
from .info_files import (
    read_json_yaml,
    get_information_file_type,
    VALID_TYPES,
    VALID_FORMATS,
)
from ..network import Network
from ..instrumentation import Instrumentation
from ..instrumentation import Instrument_components


def print_summary(filename, type=None, verbose=False, debug=False):
    """
    Print a summary of an information file (JSON or YAML format)

    if type is not provided, figures it out from the filename, which
    should be "*{TYPE}.{FORMAT}

    :param  type: "network", "instrumentation","response",
        "instrument_components", or "filter".
    :kind type: str, optional
    """

    if not type:
        type = get_information_file_type(filename)

    instance = read_json_yaml(filename)

    print(f"\nFILENAME: {filename}")
    if type == "network":
        if debug:
            print("Loading network")
        instance = Network(filename)
        if debug:
            print("Done")
        _print_summary_network(instance, filename)
    elif type == "instrumentation":
        instance = Instrumentation(filename)
        _print_summary_instrumentation(instance)
    elif type == "instrument_components":
        instance = Instrument_components(filename)
        _print_summary_instrument_components(instance)
    else:
        _print_summary_other(instance[type])


def _print_summary_network(network, network_file):
    """ Print summary information about a network """
    print(network)
    for name, station in network.stations.items():
        print("  " + str(station))
    print("")


def _print_summary_instrumentation(instrumentation):
    """ Print summary information about an instrumentation file """
    print(f"FACILITY: {instrumentation.facility['ref_name']}")
    print(f"REVISION: ")
    pp = pprint.PrettyPrinter(indent=1, depth=4, width=100, compact=True)
    pp.pprint(instrumentation.revision)
    # PRINT INSTRUMENTS
    print(20 * "=")
    print("INSTRUMENTS:")
    instrumentation.print_elements()

    # VERIFY THAT REFERRED-TO FILES EXIST
    print(20 * "=")
    print("Checking dependencies in instrument_components_file: "
          f'"{instrumentation.components_file}"')
    file_exists, n_components, n_found, n_cites =\
        instrumentation.check_dependencies(print_names=True)
    if not file_exists:
        print(
            f"Instrument_Components file not found"
        )
    elif n_components == n_found:
        print(
            "Found all {:d} specied functional components ({:d} total cites)"
            "".format(n_components, n_cites)
        )
    else:
        print(
            "MISSING {:d} of {:d} specied functional components "
            "".format(n_components - n_found, n_components)
        )


def _print_summary_instrument_components(instance):
    """ Print summary information about an instrument_components file """
    print(f"FORMAT_VERSION: {instance.format_version}")
    print(f"REVISION: {instance.revision}")
    # PRINT INSTRUMENTS
    print(10 * "=")
    print("DATALOGGERS:")
    instance.print_elements("datalogger")
    print(10 * "=")
    print("PREAMPLIFIERS:")
    instance.print_elements("preamplifier")
    print(10 * "=")
    print("SENSORS:")
    instance.print_elements("sensor")

    # VERIFY THAT REFERRED TO FILES EXIST
    print(10 * "=")
    n_files, n_found, n_cites = instance.verify_source_files(print_names=True)
    if n_files == n_found:
        print(
            "Found all {:d} specified source files ({:d} total citations)"
            "".format(n_files, n_cites)
        )
    else:
        print(
            "MISSING {:d} of {:d} specified source files"
            "".format(n_files - n_found, n_files)
        )


def _print_summary_other(instance, depth=4):
    """ Print summary information about a generic information file """
    pp = pprint.PrettyPrinter(indent=1, depth=depth, compact=True)
    pp.pprint(instance)


def _print_script(argv=None):
    """
    Prints summary of an information file

    Also confirms existence of referenced file(s)
    """
    from argparse import ArgumentParser

    parser = ArgumentParser(prog="obsinfo-print", description=__doc__)
    parser.add_argument("info_file", help="Information file")
    parser.add_argument(
        "-t",
        "--type",
        choices=VALID_TYPES,
        default=None,
        help="Forces information file type (overrides interpreting "
             "from filename)",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=VALID_FORMATS,
        default=None,
        help="Forces information file format (overrides interpreting "
             "from filename)",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="increase output verbosiy"
    )
    args = parser.parse_args()

    print_summary(args.info_file, format=args.format,
                  type=args.type, verbose=args.verbose)
