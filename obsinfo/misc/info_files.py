""" 
Validate information files

"""
# Standard library modules
import json
import pprint
import os.path
import sys
import pkg_resources
import urllib.request

# Non-standard modules
import jsonschema
import jsonref
import yaml

root_symbol = "#"
VALID_FORMATS = ["JSON", "YAML"]
VALID_TYPES = [
    "campaign",
    "network",
    "instrumentation",
    "instrument_components",
    "response",
    "filter",
]
################################################################################


def list_valid_types():
    """
    Returns a list of valid information file types
    """
    return VALID_TYPES


################################################################################


def get_information_file_type(filename):
    """
    Determines the type of a file, assuming that the filename is "*.{TYPE}.{SOMETHING}
    """

    # the_type = filename.split(".")[-2].split("/")[-1].lower()
    the_type = os.path.basename(filename).split(".")[-2].lower()
    if the_type in VALID_TYPES:
        return the_type
    print(f"Unknown type: {the_type}")
    sys.exit(1)


################################################################################
def validate(filename, format=None, type=None, verbose=False, quiet=False):
    """
    Validates a YAML or JSON file against schema
    type: "network", "instrumentation","response", "instrument_components","filter"
    format: "JSON" or "YAML"
    
    if type and/or format are not provided, tries to figure them out from the
    filename, which should be "*{TYPE}.{FORMAT}
    """

    if quiet:
        verbose = False

    if not type:
        type = get_information_file_type(filename)

    instance = read_json_yaml(filename, format=format)

    SCHEMA_FILE = pkg_resources.resource_filename(
        "obsinfo",  os.path.join("data","schemas",f"{type}.schema.json"))
    base_uri = "file://{}/".format(
        urllib.request.pathname2url(os.path.dirname(SCHEMA_FILE)))
    with open(SCHEMA_FILE, "r") as f:
        try:
            schema = jsonref.loads(f.read(), base_uri=base_uri, jsonschema=True)
        except json.decoder.JSONDecodeError as e:
            print(f"JSONDecodeError: Error loading JSON schema file: {SCHEMA_FILE}")
            print(str(e))
            return False
        except:
            print(f"Error loading JSON schema file: {SCHEMA_FILE}")
            print(sys.exc_info()[1])
            return False

    # Lazily report all errors in the instance
    # ASSUMES SCHEMA IS DRAFT-04 (I couldn't get it to work otherwise)
    try:
        if verbose:
            print(f"instance = {filename}")
        elif not quiet:
            print(f"instance = {filename} ... ", end="")

        if verbose:
            print(f"schema =   {os.path.basename(SCHEMA_FILE)}")
            print("\tTesting schema ...", end="")

        v = jsonschema.Draft4Validator(schema)

        if verbose:
            print("OK")
            print("\tTesting instance ...", end="")
        if not v.is_valid(instance):
            if quiet:
                # IF HAVE TO PRINT ERROR MESSAGE, PRINT INTRO TOO
                print(f"instance = {filename}")
            else:
                print("")
            for error in sorted(v.iter_errors(instance), key=str):
                print("\t\t", end="")
                for elem in error.path:
                    print(f"['{elem}']", end="")
                print(f": {error.message}")
            print("\tFAILED")
        else:
            if not quiet:
                print("OK")
    except jsonschema.ValidationError as e:
        if quiet:
            # IF HAVE TO PRINT ERROR MESSAGE, PRINT INTRO TOO
            print(f"instance = {filename}")
        else:
            print("")
        print("\t" + e.message)

    return True


################################################################################


def get_information_file_format(filename):
    """
    Determines if the information file is in JSON or YAML format
    
    Assumes that the filename is "*.{FORMAT}
    """

    format = filename.split(".")[-1].upper()
    if format in VALID_FORMATS:
        return format
    print("Unknown format: {format}")
    sys.exit(1)


##################################################
def read_json_yaml(filename, format=None, debug=False):
    """ Reads a JSON or YAML file """
    if not format:
        format = get_information_file_format(filename)

    with open(filename, "r") as f:
        if format == "YAML":
            try:
                element = yaml.safe_load(f)
            except:
                print(f"Error loading YAML file: {filename}")
                print(sys.exc_info()[1])
                return
        else:
            try:
                element = json.load(filename)
            except JSONDecodeError as e:
                print(f"JSONDecodeError: Error loading JSON file: {filename}")
                print(str(e))
                return
            except:
                print(f"Error loading JSON file: {filename}")
                print(sys.exc_info()[1])
                return

    return element


##################################################
def load_information_file(
    reference, source_file=None, root_symbol=root_symbol, debug=False
):
    """
    Loads all (or part) of an information file
    
    input:
        reference (str): path to the element (filename &/or internal element path)
        source_file (str): full path of referring file (if any)
    output:
        element: the requested element
        base_file: the path of this file
        
    root_symbol is interpreted as the file's root level
     - If it is at the beginning of the reference, the element is searched for
        in source_file.
     - If it is in the middle of the reference, the element is searched for within the
        filename preceding it. 
     - If it is at the end (or absent), then the entire file is loaded 
     
    Based on JSON Pointers
       
    """

    # Figure out filename, absolute path and path inside file
    filename = None
    if root_symbol in reference:
        if reference.count(root_symbol) > 1:
            raise RuntimeError(
                'More than one occurence of "{}" in file reference "{}"'.format(
                    root_symbol, reference
                )
            )
        if reference[0] == root_symbol:
            filename = ""
            internal_path = reference[1:]
        elif reference[-1] == root_symbol:
            filename = reference[0:-1]
            internal_path = ""
        else:
            A = reference.split(root_symbol)
            filename = A[0]
            internal_path = A[1]
    else:
        filename = reference
        internal_path = ""
    if debug:
        print(
            "LOAD_INFORMATION_FILE(): reference={}, source_file={}".format(
                reference, source_file
            )
        )
    if source_file:
        if os.path.isfile(source_file):
            current_path = os.path.dirname(source_file)
        else:
            current_path = source_file
        filename = os.path.join(current_path, filename)
    else:
        current_path = os.getcwd()
    if debug:
        print(
            "LOAD_INFORMATION_FILE(): filename={}, internal_path={}".format(
                filename, internal_path
            )
        )

    # MAKE SURE THAT IT CONFORMS TO SCHEMA
    validate(filename, quiet=True)

    # READ IN FILE
    element = read_json_yaml(filename)

    # BREAK OUT THE REQUESTED PART
    if internal_path:
        for key in internal_path.split("/"):
            if not key in element:
                raise RuntimeError(
                    "Internal path {} not found in file {}".format(
                        internal_path, filename
                    )
                )
            else:
                element = element[key]

    # RETURN RESULT
    if debug:
        print("LOAD_YAML(): ", type(element))
    return element, os.path.abspath(os.path.dirname(filename))


################################################################################
def _validate_script(argv=None):
    """
    Validate an obsinfo information file

    Validates a file named *.{TYPE}.json or *.{TYPE}.yaml against the 
    obsinfo schema.{TYPE}.json file.

    {TYPE} can be campaign, network, instrumentation, instrument_components or
    response
    """
    from argparse import ArgumentParser

    parser = ArgumentParser(prog="obsinfo-validate", description=__doc__)
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

    validate(args.info_file, format=args.format, type=args.type, verbose=args.verbose)
