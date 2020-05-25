""" 
Validate information files

"""
# Standard library modules
import pprint
import os.path
import sys

# obsinfo modules
from .info_files import (
    read_json_yaml,
    get_information_file_format,
    get_information_file_type,
    VALID_TYPES,
    VALID_FORMATS,
)
from ..network import network
from ..instrumentation import instrumentation
from ..instrument_components import instrument_components

################################################################################
def print_summary(filename, format=None, type=None, verbose=False, debug=False):
    """
    Print a summary of an information file
    type: "network", "instrumentation","response", "instrument_components","filter"
    format: "JSON" or "YAML"
    
    if type and/or format are not provided, figures them out from the
    filename, which should be "*{TYPE}.{FORMAT}
    """

    if not type:
        type = get_information_file_type(filename)

    instance = read_json_yaml(filename)

    print(f"\nFILENAME: {filename}")
    if type == "network":
        if debug:
            print("Loading network")
        instance = network(filename)
        if debug:
            print("Done")
        _print_summary_network(instance, filename)
    elif type == "instrumentation":
        instance = instrumentation(filename)
        _print_summary_instrumentation(instance)
    elif type == "instrument_components":
        instance = instrument_components(filename)
        _print_summary_instrument_components(instance)
    else:
        _print_summary_other(instance[type])


################################################################################
def _print_summary_network(network, network_file):
    """ Print summary information about a network """
    print(network)
    for name, station in network.stations.items():
        print("  " + str(station))
    print("")


################################################################################
def _print_summary_instrumentation(instrumentation):
    """ Print summary information about an instrumentation file """
    print(f"FACILITY: {instrumentation.facility['reference_name']}")
    print(f"REVISION: {instrumentation.revision}")
    # PRINT INSTRUMENTS
    print(20 * "=")
    print("INSTRUMENTS:")
    instrumentation.print_elements()

    # VERIFY THAT INSTRUMENTS & SENSORS LISTED IN "individuals" EXIST in "models"
    print(20 * "=")
    if instrumentation.verify_individuals():
        print("All instruments have a generic counterpart")

    # VERIFY THAT REFERRED TO FILES EXIST
    print(20 * "=")
    print("Checking dependencies on instrument_components_file")
    file_exists, n_components, n_found, n_cites = instrumentation.check_dependencies(
        print_names=True
    )
    if not file_exists:
        print(
            f"Instrument_Components file not found: {instrumentation.components_file}"
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


################################################################################
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

    # VERIFY THAT COMPONENTS LISTED IN "specific" EXIST in "generic"
    print(10 * "=")
    if instance.verify_individuals():
        print("All specific components have a generic counterpart")

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


################################################################################
def _print_summary_other(instance):
    """ Print summary information about a generic information file """
    pp = pprint.PrettyPrinter(indent=1, depth=2, compact=True)
    pp.pprint(instance)


################################################################################
def _print_script(argv=None):
    """
    Prints summary of an information file

    Also confirms existence of referenced file(s)
    """
    from argparse import ArgumentParser

    parser = ArgumentParser(prog="obsinfo-print", description=__doc__)
    parser.add_argument("info_file", help="Information file")
    parser.add_argument("-t", "--type", choices=VALID_TYPES, default=None,
                        metavar="TYPE",
                        help="Forces information file type.  Allowed values "
                             + "are {" + ", ".join(VALID_TYPES)
                             + "}. (default = interpret from filename)")
    parser.add_argument("-f",  "--format", choices=VALID_FORMATS, default=None,
                        metavar="FMT",
                        help="Forces information file format. Allowed values "
                             + "are {" + ", ".join(VALID_FORMATS)
                             + "}. (default = interpret from filename)")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="increase output verbosity")
    args = parser.parse_args()

    print_summary(
        args.info_file, format=args.format, type=args.type, verbose=args.verbose
    )
