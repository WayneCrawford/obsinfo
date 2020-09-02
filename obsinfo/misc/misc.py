"""
Miscellaneous routines
"""
# Standard library modules
import math as m
# import os.path
# import sys
# import warnings

# Non-standard modules
# import obspy.core.util.obspy_types as obspy_types
# import obspy.core.inventory as inventory
# import obspy.core.inventory.util as obspy_util
# from obspy.core.utcdatetime import UTCDateTime


def calc_norm_factor(zeros, poles, norm_freq, pz_type, debug=False):
    """
    Calculate the normalization factor for give poles-zeros

    The norm factor A0 is calculated such that
                       sequence_product_over_n(s - zero_n)
            A0 * abs(------------------------------------------) === 1
                       sequence_product_over_m(s - pole_m)

    for s_f=i*2pi*f if the transfer function is in radians
            i*f     if the transfer funtion is in Hertz
    """

    A0 = 1.0 + 1j * 0.0
    if pz_type == "LAPLACE (HERTZ)":
        s = 1j * norm_freq
    elif pz_type == "LAPLACE (RADIANS/SECOND)":
        s = 1j * 2 * m.pi * norm_freq
    else:
        print("Don't know how to calculate normalization factor for "
              "z-transform poles and zeros!")
    for p in poles:
        A0 = A0 * (s - p)
    for z in zeros:
        A0 = A0 / (s - z)

    if debug:
        print("poles={}, zeros={}, s={:g}, A0={:g}".format(
            poles, zeros, s, A0))

    A0 = abs(A0)

    return A0


def round_down_minute(date_time, min_offset):
    """
    Round down to nearest minute

    :param date_time: input date_time
    :kind date_time: class ~datetime.datetime????
    :param min_offset: the minute must be at least this many seconds earlier
    :kind min_offset: number
    :returns: rounded down date_time
    :rtype: same as date_time
    """
    dt = date_time - min_offset
    dt.second = 0
    dt.microsecond = 0
    return dt


def round_up_minute(date_time, min_offset):
    """
    Round up to nearest minute

    :param date_time: input date_time
    :kind date_time: class ~datetime.datetime????
    :param min_offset: the minute must be at least this many seconds later
    :kind min_offset: number
    :returns: rounded up date_time
    :rtype: same as date_time
    """
    dt = date_time + 60 + min_offset
    dt.second = 0
    dt.microsecond = 0
    return dt


def get_azimuth_dip(channel_seed_codes, orientation_code):
    " Return azimuth and dip [value,error] pairs (UNUSED???)"

    if orientation_code in channel_seed_codes["orientation"]:
        azimuth = channel_seed_codes["orientation"][orientation_code][
                                     "azimuth.deg"]
        azimuth = [float(x) for x in azimuth]
        dip = channel_seed_codes["orientation"][orientation_code]["dip.deg"]
        dip = [float(x) for x in dip]
    else:
        raise NameError(
            'orientation code "{}" not found in '
            "component seed_codes.orientation".format(orientation_code)
        )
    return azimuth, dip


if __name__ == "__main__":
    import doctest
    doctest.testmod()
