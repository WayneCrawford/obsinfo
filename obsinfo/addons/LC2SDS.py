"""
Write extraction script for LCHEAPO instruments (from proprietary to SDS
format, with basic drift correction)
"""
# import obsinfo
import obsinfo.network.network as oi_network
from pathlib import Path

BIG_SEPARATOR = f"# {'='*70}\n"
SMALL_SEPARATOR = f'echo "{"-"*65}"\n'


def process_script(station, input_dir, output_dir):
    """Writes script to transform raw OBS data to SDS

    :param station:  ~obsinfo.station object
    :param input_dir: directory containing LCHEAPO station directories
    :param output_dir: directory in which to put the SDS directory
    """
    station_dir = str(Path(input_dir) / station.code)
    s = ""
    s += __header(station.code)
    s += __setup_variables(station_dir, output_dir, station.code)
    s += __lcfix_commands()
    s += __lc2sds_commands(station)
    s += '\nmv {}/process-steps.json {}/process-steps_{}.json\n'.format(
        output_dir, output_dir, station.code)
    return s


def __header(station_name):
    s = "#!/bin/bash\n\n"
    s += BIG_SEPARATOR
    s += f'echo "Working on station {station_name}"\n'
    s += BIG_SEPARATOR + '\n'
    return s


def __setup_variables(station_dir, output_dir, station_name):
    """
    :param station_dir: directory containing *.raw.lch files
    :param output_dir: base directory to write to
    """
    s = "#  - Set up paths\n"
    s += f"STATION_DIR={station_dir}\n"
    s += f"OUTPUT_DIR={output_dir}\n"
    s += f"station={station_name}\n"
    s += "\n"
    return s


def __lcfix_commands(in_fnames="*.raw.lch"):
    """
    Write an lc2ms command line

   :param in_fnames: search string for input files within in_path ['*.raw.lch']
   :returns: string of bash script lines
    """
    s = SMALL_SEPARATOR
    s += 'echo "Running LCFIX: Fix common LCHEAPO data bugs"\n'
    s += SMALL_SEPARATOR
    s += 'in_dir="$STATION_DIR"\n'
    s += 'out_dir="$OUTPUT_DIR/$station"\n'
    s += f"lcfix '{in_fnames}' -i $in_dir -o $out_dir\n"
    s += "\n"
    return s


def __lc2sds_commands(station, in_fnames="*.fix.lch"):
    """
    Write an lc2ms command line

    Inputs:
    :param station: ~class obsinfo station
    :param in_fnames: search string for input files within in_path
    :returns: string of bash script lines
    """

    net = station.network_code
    sta = station.code
    obs_type = station.instruments[0].reference_code.split("_")[0]
    if len(station.instruments) > 0:
        NameError("Can't handle more than 1 instrument/station")
    s = SMALL_SEPARATOR
    s += 'echo "Running LC2SDS_weak: LCHEAPO data to SDS with drift correct"\n'
    s += SMALL_SEPARATOR
    s += 'in_dir=$out_dir\n'
    s += 'out_dir=$OUTPUT_DIR\n'
    start_sync_ref, start_sync_inst, end_sync_ref, end_sync_inst =\
        _get_lin_corr(station)
    s += f'START_REFR="{start_sync_ref}"\n'
    s += f'START_INST="{start_sync_inst}"\n'
    s += f'END_REFR="{end_sync_ref}"\n'
    s += f'END_INST="{end_sync_inst}"\n'

    s += f"lc2SDS_weak '*.fix.lch' -i $in_dir -o $out_dir --network '{net}' "
    s += f"--station '{sta}' -t '{obs_type}' "
    s += "-s $START_REFR $START_INST -e $END_REFR $END_INST\n"

    return s


def _get_lin_corr(station):
    """
    Return linear correction parameters as strs
    """
    clock_corrected = False
    for proc in station.processing:
        if "clock_corrections" in proc:
            if clock_corrected:
                NameError("CAN'T HANDLE MORE THAN ONE CLOCK CORRECTION")
            if "leapseconds" in proc["clock_corrections"]:
                NameError("No leap-second correction yet")
            lin_corr = proc['clock_corrections']['linear_drift']
            clock_corrected = True
    start_sync_ref = str(lin_corr["start_sync_reference"]).rstrip("Z")
    start_sync_inst = str(lin_corr["start_sync_instrument"]).rstrip("Z")
    end_sync_ref = str(lin_corr["end_sync_reference"]).rstrip("Z")
    end_sync_inst = str(lin_corr["end_sync_instrument"]).rstrip("Z")
    if start_sync_inst == "0":
        start_sync_inst = ""
    return start_sync_ref, start_sync_inst, end_sync_ref, end_sync_inst


def _console_script(argv=None):
    """
    Console script to convert LCHEAPO data to basic SDS with drift correction
    Data should be in station_data_path/{STATION_NAME}/*.raw.lch
    """
    from argparse import ArgumentParser

    parser = ArgumentParser(
        prog="obsinfo-make_LCHEAPO-park_scripts", description=__doc__)
    parser.add_argument("network_file", help="Network information file")
    parser.add_argument("input_dir",
                        help="Base path containing station directories")
    parser.add_argument("output_dir", default="2_miniseed_basic",
                        help="directory in which to put fixed data and "
                             "SDS directory")
    parser.add_argument("--suffix", default="",
                        help="suffix for script filename")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="increase verbosity")
    parser.add_argument("-q", "--quiet", action="store_true",
                        help="run silently")
    args = parser.parse_args()

    if not args.quiet:
        print("Creating LC2SDS process scripts, ", end="", flush=True)
    # READ IN NETWORK INFORMATION
    network = oi_network(args.network_file)
    sta_list = [name for name in network.stations.keys()]
    if not args.quiet:
        print("network {}, stations {}"
              .format(network.network_info.code, ', '.join(sta_list)))

    for name, station in network.stations.items():
        # station_dir = os.path.join(args.station_data_path, name)
        script = process_script(station, args.input_dir, args.output_dir)
        fname = f"process_{name}{args.suffix}.sh"
        if args.verbose:
            print(f" ... writing file {fname}", flush=True)
        with open(fname, "w") as f:
            f.write(script)
            f.close()
    if not args.verbose and not args.quiet:
        print("")
