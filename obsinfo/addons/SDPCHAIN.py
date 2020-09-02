"""
Generate scripts needed to go from basic miniSEED to data center ready
"""
# import obsinfo
from obsinfo.network import network as oi_network
import os.path
import sys
from obspy.core import UTCDateTime

SEPARATOR_LINE = "\n# " + 60 * "=" + "\n"


def process_script(station,
                   station_dir,
                   distrib_dir="/opt/sdpchain",
                   input_dir="miniseed_basic",
                   corrected_dir="miniseed_corrected",
                   extra_commands=None,
                   include_header=True,
                   SDS_uncorr_dir="SDS_uncorrected",
                   SDS_corr_dir="SDS_corrected",
                   SDS_combined_dir="SDS_combined"):
    """Writes OBS data processing script using SDPCHAIN software

        :param station: station to process
        :kind station: ~class obsinfo.Station
        :param station_dir: base directory for the station data
        :param input_dir: directory beneath station_dir for input (basic)
            miniseed data
        :param corrected_dir: directory beneath station_dir for
            corrected miniseed data
        :param SDS_corr_dir: directory beneath station_dir in which to write
            SDS structure of corrected data (ideally ../SOMETHING if ms2sds
            could write all to the same directory)
        :param SDS_uncorr_dir: directory beneath station_dir in which to write
            SDS structure of uncorrected data (ideally ../SOMETHING if ms2sds
            could write all to the same directory)
        :param include_header: whether or not to include the bash script header
            '#!/bin/bash' at the top of the script
        :param distrib_dir: Base directory of sdpchain distribution

        The sequence of commands is:
            1: optional proprietary format steps (proprietary format -> basic
                miniseed, separate)
            2: optional extra_steps (any cleanup needed for the basic
                miniseed data, should either overwrite the existing data or
                remove the original files so that subsequent steps only see
                the cleaned data)
            3: ms2sds on basic miniseed data
            4: leap-second corrections, if necessary
            5: msdrift (creates drift-corrected miniseed)

    """
    leap_corr_dir = "miniseed_leap_corrected"

    s = ""
    if include_header:
        s += __header(station.code)
    s += __setup_variables(distrib_dir, station_dir)
    if extra_commands:
        s += __extra_command_steps(extra_commands)
    s += __ms2sds_script(station, input_dir, SDS_uncorr_dir)
    t = __leap_second_script(
        station.clock_corrections.get("leapseconds", None),
        input_dir, leap_corr_dir)
    if t:
        s += t
        input_dir = leap_corr_dir
    s += __msdrift_script(input_dir, corrected_dir, station.clock_corrections)
    s += __force_quality_script(corrected_dir, "Q")
    s += __ms2sds_script(station, corrected_dir, SDS_corr_dir)
    s += __combine_sds_script(station, SDS_corr_dir, SDS_uncorr_dir,
                              SDS_combined_dir)

    return s


def __header(station_name):
    s = "#!/bin/bash\n"
    s += SEPARATOR_LINE
    s += f'echo "Working on station {station_name}"'
    s += SEPARATOR_LINE
    return s


def __setup_variables(distrib_dir, station_dir):
    s = SEPARATOR_LINE + "# SDPCHAIN STEPS" + SEPARATOR_LINE
    s += "#  - Set up paths\n"
    s += f"STATION_DIR={station_dir}\n"
    s += f"MSDRIFT_EXEC={os.path.join(distrib_dir, 'bin', 'msdrift')}\n"
    s += "MSDRIFT_CONFIG={}\n".format(
        os.path.join(distrib_dir, 'config', 'msdrift.properties'))
    s += f"MS2SDS_EXEC={os.path.join(distrib_dir, 'bin', 'ms2sds')}\n"
    s += "MS2SDS_CONFIG={}\n".format(
        os.path.join(distrib_dir, 'config', 'ms2sds.properties'))
    s += f"SDPPROCESS_EXEC={os.path.join(distrib_dir,'bin','sdp-process')}\n"
    s += f"MSMOD_EXEC={os.path.join('/opt/iris','bin','msmod')}\n"
    s += "\n"

    return s


def __extra_command_steps(extra_commands):
    """
    Write extra command lines, embedded in sdp-process

    Input:
        extra_commands: list of strings containing extra commands
    """
    s = SEPARATOR_LINE
    s = s + "# - EXTRA COMMANDS\n"
    assert isinstance(extra_commands, "list"), "extra_commands is not a list"
    for cmd_line in extra_commands:
        s = s + '$SDPPROCESS_EXEC --cmd="{cmd_line}"\n'
    return s


def __ms2sds_script(station, in_path, out_path):
    """
    Writes the ms2sds lines of the script
    """
    sta = station.code
    net = station.network_code

    s = f'echo "{"-"*60}"\n'
    s += 'echo "Running MS2SDS: MAKE SDS ARCHIVE"\n'
    s += f'echo "{"-"*60}"\n'

    s += f'in_dir="{in_path}"\n'
    s += f'out_dir="{out_path}"\n'

    s += "# - Create output directory\n"
    s += "mkdir $STATION_DIR/$out_dir\n"

    s += "# - Collect input filenames\n"
    s += "command cd $STATION_DIR/$in_dir\n"
    s += "mseedfiles=$(ls *.mseed)\n"
    s += "command cd -\n"
    s += 'echo "mseedfiles=" $mseedfiles\n'

    s += "# - Run executable\n"
    s += "$MS2SDS_EXEC $mseedfiles -d $STATION_DIR -i $in_dir -o $out_dir "
    s += f'--network "{net}" --station "{sta}" -a SDS -p $MS2SDS_CONFIG\n'
    s += "\n"

    return s


def __leap_second_script(leapseconds, in_dir, out_dir):
    """
    Create leap-second correction text

    Inputs:
        leapseconds: list of dictionaries from network information file
    """
    if not leapseconds:
        return ""

    s = f'echo "{"-"*60}"\n'
    s += 'echo "LEAPSECOND CORRECTIONS"\n'
    s += f'echo "{"-"*60}"\n'

    s += f"in_dir={in_dir}\n"
    s += f"out_dir={out_dir}\n"

    s += "# - Create output directory\n"
    s += "mkdir $STATION_DIR/$out_dir\n"

    s += "# - Copy files to output directory\n"
    s += "cp $STATION_DIR/$in_dir/*.mseed $STATION_DIR/$out_dir\n"

    for leapsecond in leapseconds:
        if leapsecond["corrected_in_basic_miniseed"]:
            s += f'# LEAP SECOND AT {leapsecond["time"]} '
            s += 'ALREADY CORRECTED IN BASIC MINISEED, DOING NOTHING\n'
            return s
        temp = leapsecond["time"].split("T")
        d = UTCDateTime(temp[0])
        leap_time = d.strftime("%Y,%j,") + temp[1].rstrip("Z")
        s += 'echo ""\n'
        s += f'echo "{"="*60}"\n'
        s += 'echo "Running LEAPSECOND correction"\n'
        s += f'echo "{"-"*60}"\n'
        if leapsecond["type"] == "+":
            s += '$SDPPROCESS_EXEC -d $STATION_DIR '
            s += '-c="Shifting 1 second BACKWARD after positive leapsecond" '
            s += f' --cmd="$MSMOD_EXEC --timeshift -1 -ts {leap_time} '
            s += '-s -i $STATION_DIR/$out_dir/*.mseed"\n'
            s += '$SDPPROCESS_EXEC -d $STATION_DIR '
            s += '-c="Marking the record containing the positive leapsecond" '
            s += ' --cmd="$MSMOD_EXEC --actflags 4,1 '
            s += f'-tsc {leap_time} -tec {leap_time} '
            s += '-s -i $STATION_DIR/$out_dir/*.mseed"\n'
        elif leapsecond["type"] == "-":
            s += '$SDPPROCESS_EXEC -d $STATION_DIR '
            s += '-c="Shifting 1 second FORWARD after negative leapsecond" '
            s += f' --cmd="$MSMOD_EXEC --timeshift +1 -ts {leap_time} '
            s += '-s -i $STATION_DIR/$out_dir/*.mseed"\n'
            s += '$SDPPROCESS_EXEC -d $STATION_DIR '
            s += '-c="Marking the record containing the negative leapsecond" '
            s += ' --cmd="$MSMOD_EXEC --actflags 5,1 '
            s += f'-tsc {leap_time} -tec {leap_time} -s '
            s += '-i $STATION_DIR/$out_dir/*.mseed"\n'
        else:
            s += 'ERROR: leapsecond type "{}" is neither "+" nor "-"\n'.format(
                 leapsecond["type"])
            sys.exit(2)
    return s


def __msdrift_script(in_path, out_path, clock_corrs):
    """
    Write msdrift lines of the script

    :param in_path:
    :param out_path:
    :param clock_corrs:
    """
    s = f'echo "{"-"*60}"\n'
    s += 'echo "Running MSDRIFT: CORRECT LINEAR CLOCK DRIFT"\n'
    s += f'echo "{"-"*60}"\n'

    s += f'in_dir="{in_path}"\n'
    s += f'out_dir="{out_path}"\n'

    s += "# - Create output directory\n"
    s += "mkdir $STATION_DIR/$out_dir\n"

    s += "# - Collect input filenames\n"
    s += f"command cd $STATION_DIR/$in_dir\n"
    s += "mseedfiles=$(ls *.mseed)\n"
    s += "command cd -\n"
    s += 'echo "mseedfiles=" $mseedfiles\n'

    if "linear_drift" in clock_corrs:
        lin_corr = clock_corrs["linear_drift"]
        s += "# - Run executable\n"
        s += 'START_REFR="{}"\n'.format(
            str(lin_corr["start_sync_reference"]).rstrip("Z"))
        s += 'START_INST="{}"\n'.format(
            str(lin_corr["start_sync_instrument"]).rstrip("Z"))
        s += 'END_REFR="{}"\n'.format(
            str(lin_corr["end_sync_reference"]).rstrip("Z"))
        s += 'END_INST="{}"\n'.format(
            str(lin_corr["end_sync_instrument"]).rstrip("Z"))
        s += "$MSDRIFT_EXEC $mseedfiles "
        s += "-d $STATION_DIR -i $in_dir -o $out_dir "
        s += '-m "%E.%S.00.%C.%Y.%D.%T.mseed:'
        s += '%E.%S.00.%C.%Y.%D.%T_driftcorr.mseed" '
        s += '-s "$START_REFR;$START_INST" '
        s += '-e "$END_REFR;$END_INST" '
        # s += '-c "comment.txt" '
        s += "-p $MSDRIFT_CONFIG\n\n"
    else:
        while lin_corr in clock_corrs["linear_drifts"]:
            s += SEPARATOR_LINE
            s += "ERROR, CANT APPLY MULTIPLE TIME CORRECTS (CHANGE MSDRIFT\n"
            s += "TO ONLY WRITE TIME RANGE BUT APPEND TO EXISTING FILE?)\n"
            s += +SEPARATOR_LINE
    return s


def __force_quality_script(in_path, quality="Q"):
    """
    Force data quality to Q

    Inputs:
        in_path: directory where mseed files are found
        quality: new quality code
    """
    s = f'echo "{"-"*60}"\n'
    s += 'echo "Forcing data quality to Q"\n'
    s += f'echo "{"-"*60}"\n'
    s += '$SDPPROCESS_EXEC -d $STATION_DIR -c="Forcing data quality to Q" '
    s += f'--cmd="$MSMOD_EXEC --quality Q -i {in_path}/*.mseed"\n'
    s += "\n"

    return s


def __combine_sds_script(station, SDS_corrected_dir, SDS_uncorrected_dir,
                         SDS_combined_dir):
    """
    Combine corrected and uncorrected SDS directories/files

    Corrected must be before uncorrected so that Arclink will extract it by
    default
    Uses the corrected directory as the template: will not process uncorrected
    files that don't have corresponding corrected files

    Creates no process-steps because there are so many individual calls to
    msmod (should we write an sdp-sds_combine script?)

    Inputs:
        station:             station object
        SDS_corrected_dir:   name of SDS directory containing corrected data
        SDS_uncorrected_dir: name of SDS directory containing uncorrected data
        SDS_combined_dir:    name of SDS directory to put combined data into
    """
    s = f'echo "{"-"*60}"\n'
    s += 'echo "Combining corrected and uncorrected SDS datafiles"\n'
    s += f'echo "{"-"*60}"\n'
    s += f"mkdir -p $STATION_DIR/{SDS_combined_dir}\n"
    s += f"command cd $STATION_DIR/{SDS_corrected_dir}\n"
    s += f"years=????\n"
    s += f"command cd -\n"
    s += f"for y in $years ; do\n"
    # I HAD TO ADD "SDSs" to handle the fact that ms2sds makes an
    # "SDS" directory inside the output directory
    s += f"  for d in $STATION_DIR/{SDS_corrected_dir}/SDS/$y/"
    s += f"{station.network_code}/{station.code}/*.D ; do\n"
    s += "    d_sub=${{d#$STATION_DIR/{}/SDS/}}\n".format(
        SDS_corrected_dir)
    s += f"    if [[ ! -d $STATION_DIR/{SDS_combined_dir}/$d_sub ]] ; then\n"
    s += f'      echo "Creating and filling SDS subdirectory $d_sub"\n'
    s += f'      eval "mkdir -p $STATION_DIR/{SDS_combined_dir}/$d_sub"\n'
    s += f"      for f in $d/*; do\n"
    s += f"        f_sub=${{f#$STATION_DIR/{SDS_corrected_dir}/SDS/}}\n"
    s += f"        cat $STATION_DIR/{SDS_corrected_dir}/SDS/$f_sub "
    s += f"$STATION_DIR/{SDS_uncorrected_dir}/SDS/$f_sub > "
    s += f"$STATION_DIR/{SDS_combined_dir}/$f_sub\n"
    s += f"      done\n"
    s += f"    else\n"
    s += f'      echo "SDS subdirectory $d_sub already exists, skipping..."\n'
    s += f"    fi\n"
    s += f"  done\n"
    s += f"done\n"
    s += "\n"

    return s


def _console_script(argv=None):
    """
    Console-level processing script

    requires SDPCHAIN programs msdrift and ms2sds, and IRIS program msmod

    Currently usese 'SDS_corrected' and 'SDS_uncorrected' as default SDS
    directories.
    Would be better to use ../SDS_[un]corrected so that all data are together,
    but ms2sds is not yet capable of putting data in an existing SDS directory

    """
    from argparse import ArgumentParser

    parser = ArgumentParser(prog="obsinfo-make_process_scripts_SDPCHAIN",
                            description=__doc__)
    parser.add_argument("network_file", help="Network information file")
    parser.add_argument("station_data_path",
                        help="Base path containing station data")
    parser.add_argument("distrib_dir", default="/opt/sdpchain",
                        help="Path to SDPCHAIN software")
    parser.add_argument("-i", "--input_dir", default="miniseed_basic",
                        help="subdirectory of station_data_path/{STATION}/ "
                        "containing input *.mseed files")
    parser.add_argument("-o", "--corrected_dir", default="miniseed_corrected",
                        help="subdirectory of station_data_path/{STATION}/ "
                        "to put corrected *.mseed files")
    parser.add_argument("--SDS_corr_dir", default="SDS_corrected",
                        help="subdirectory of station_data_path/{STATION}/ "
                        "for SDS structure of corrected data")
    parser.add_argument("--SDS_uncorr_dir", default="SDS_uncorrected",
                        help="subdirectory of station_data_path/{STATION}/ "
                        "for SDS structure of uncorrected data")
    parser.add_argument("--suffix", default="_SDPCHAIN",
                        help="suffix for script filename")
    parser.add_argument("--append", action="store_true",
                        help="append to existing script file")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="increase output verbosity")
    parser.add_argument("--no_header", action="store_true",
                        help="do not include file header")
    parser.add_argument("-q", "--quiet", action="store_true",
                        help="run silently")
    args = parser.parse_args()

    # READ IN NETWORK INFORMATION
    if not args.quiet:
        print(f"Creating SDPCHAIN process scripts, ", end="")
    network = oi_network(args.network_file)
    if not args.quiet:
        print(f"network {network.network_info.code}, stations ", end="")
        if args.verbose:
            print("")

    first_time = True
    for name, station in network.stations.items():
        if not args.quiet:
            if args.verbose:
                print(f"\t{name}", end="")
            else:
                if first_time:
                    print(f"{name}", end="")
                else:
                    print(f", {name}", end="")
        station_dir = os.path.join(args.station_data_path, name)
        script = process_script(
            station,
            station_dir,
            distrib_dir=args.distrib_dir,
            input_dir=args.input_dir,
            corrected_dir=args.corrected_dir,
            SDS_uncorr_dir=args.SDS_uncorr_dir,
            SDS_corr_dir=args.SDS_corr_dir,
            include_header=not args.no_header,
        )
        fname = "process_" + name + args.suffix + ".sh"
        if args.verbose:
            print(f" ... writing file {fname}", flush=True)
        if args.append:
            write_mode = "a"
        else:
            write_mode = "w"
        with open(fname, write_mode) as f:
            f.write(script)
            f.close()
        first_time = False
    if not args.verbose and not args.quiet:
        print("")
