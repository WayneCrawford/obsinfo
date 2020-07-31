""" 
ObsPy-specific routines
"""
# Standard library modules
import math as m
import json
import pprint
import os.path
import sys

# Non-standard modules
import yaml
import obspy.core.util.obspy_types as obspy_types
import obspy.core.inventory as inventory
import obspy.core.inventory.util as obspy_util
from obspy.core.utcdatetime import UTCDateTime

from .misc import calc_norm_factor
from ..network.util import create_comments


last_output = None
def response_with_sensitivity(resp_stages, sensitivity, debug=False):
    """
    Returns obspy Response object with sensitivity
    
    :param resp_stages: list of obspy ResponseStages
    :param sensitivity: a guess of sensitivity based on individual stage gains
    """

    true_sensitivity_input_units = None

    # HAVE TO MAKE OBSPY THINK ITS M/S FOR IT TO CALCULATE SENSITIVITY CORRECTLY FOR PRESSURE
    if "PA" in sensitivity["input_units"].upper():
        true_sensitivity_input_units = sensitivity["input_units"]
        sensitivity["input_units"] = "M/S"
    response = inventory.response.Response(
        instrument_sensitivity=inventory.response.InstrumentSensitivity(
            sensitivity["guess"],
            sensitivity["freq"],
            input_units=sensitivity["input_units"],
            output_units=sensitivity["output_units"],
            input_units_description=sensitivity["input_units_description"],
            output_units_description=sensitivity["output_units_description"],
        ),
        response_stages=resp_stages,
    )
    # response.plot(min_freq=0.001)
    guesstimate = response.instrument_sensitivity.value
    response.recalculate_overall_sensitivity(sensitivity["freq"])
    if debug:
        calculated = response.instrument_sensitivity.value
        print(
            "Guesstimated vs calculated sensitivity at {:g} Hz : {:.3g} vs {:.3g} ({:.1g}% difference)".format(
                response.instrument_sensitivity.frequency,
                guesstimate,
                calculated,
                100.0 * abs(guesstimate - calculated) / calculated,
            )
        )
    if true_sensitivity_input_units:
        response.instrument_sensitivity.input_units = true_sensitivity_input_units

    return response


def response(my_responses, debug=False):
    """
    Create an obspy response object from a response_yaml-based list of stages
    """
    global last_output
    resp_stages = []
    i_stage = 0
    sensitivity = dict()
    if debug:
        print(len(my_responses), "stages") #??
    #delay_correction = my_response.get("delay_correction",False)
    nbrS = get_nb_stages(my_responses)
    for my_response in my_responses:
        # temporary
        if my_response['decimation_info'] :
            key_with_p = [k for k in my_response['decimation_info'].keys() if '.' in k ]
            if len(key_with_p) !=0:
                delay_correction = my_response['decimation_info'][key_with_p[0]]
            else:
                delay_correction = my_response['decimation_info']['delay_correction'] if my_response['decimation_info'] else False
            if 'input_sample_rate' in my_response['decimation_info']:
                last_output = my_response['decimation_info']['input_sample_rate'] 
        decimation_info = my_response['decimation_info'] if 'decimation_info' in my_response else None

        for stage in my_response['stages']:
            # DEFINE COMMON VALUES
            i_stage = i_stage + 1
            #         if debug:
            #             print("stage=",end='')
            #             print(yaml.dump(stage))

            units, sensitivity = __get_units_sensitivity(stage, sensitivity, i_stage)

            resp_type = stage["filter"]["type"]
            if debug:
                print("i_stage=", i_stage, ", resp_type=", resp_type)
            # Create and append the appropriate response
            if resp_type == "PolesZeros":
                resp_stages.append(__make_poles_zeros(stage, i_stage, units))
            elif resp_type == "COEFFICIENTS":
                resp_stages.append(__make_coefficients(stage, i_stage, units, delay_correction, decimation_info, nbrS))
            elif resp_type == "FIR":
                resp_stages.append(__make_FIR(stage, i_stage, units, delay_correction, decimation_info, nbrS))
            elif resp_type == "AD_CONVERSION":
                resp_stages.append(__make_DIGITAL(stage, i_stage, units, decimation_info))
            elif resp_type == "ANALOG":
                resp_stages.append(__make_ANALOG(stage, i_stage, units))
            else:
                raise TypeError("UNKNOWN STAGE RESPONSE TYPE: {}".format(resp_type))
    response = response_with_sensitivity(resp_stages, sensitivity)
    if debug:
        print(response)
    return response


def get_nb_stages(responses):
    s = 0
    for i in responses:
        s = s + len(i['stages'])
    return s



def __get_units_sensitivity(stage, sensitivity, i_stage):
    """
    Return output units and sensitivity of stages up to present
    
    sensitivity is a dictionary with "input_units", "input_units_description"
        and "freq" being set by the first stage.  "guess" being the product of
        the gains of all stages
        
    units are for the current stage
    """
    
    units = dict()
    temp = stage.get("input_units", {})
    units["input"] = temp.get("name", None)
    units["input_description"] = temp.get("description", None)

    temp = stage.get("output_units", {})
    units["output"] = temp.get("name", None)
    units["output_description"] = temp.get("description", None)

    # Set Sensitivity
    gain_value, gain_frequency = __get_gain(stage)
    if i_stage == 1:
        sensitivity = {
            "input_units": units["input"],
            "input_units_description": units["input_description"],
            "freq": gain_frequency,
            "guess": gain_value,
        }

    else:
        sensitivity["guess"] = sensitivity["guess"] * gain_value
    if units["output"]:
        sensitivity["output_units"] = units["output"]
        sensitivity["output_units_description"] = units["output_description"]

    return units, sensitivity


def __make_poles_zeros(stage, i_stage, units, debug=False):
    gain_value, gain_frequency = __get_gain(stage)
    resp = stage["filter"]
    lstr = resp["units"].lower()
    if "hertz" in lstr or "hz" in lstr:
        pz_type = "LAPLACE (HERTZ)"
    elif "z-transform" in lstr or "digital" in lstr:
        pz_type = "DIGITAL (Z-TRANSFORM)"
    elif "rad" in lstr:
        pz_type = "LAPLACE (RADIANS/SECOND)"
    else:
        raise ValueError('Unknown PoleZero response type: "{}"'.format(lstr))
    zeros = [
        obspy_types.ComplexWithUncertainties(
            float(t[0]) + 1j * float(t[1]), lower_uncertainty=0.0, upper_uncertainty=0.0
        )
        for t in resp["zeros"]
    ]
    poles = [
        obspy_types.ComplexWithUncertainties(
            float(t[0]) + 1j * float(t[1]), lower_uncertainty=0.0, upper_uncertainty=0.0
        )
        for t in resp["poles"]
    ]
    if gain_frequency == 0:
        norm_freq = 1.0
    else:
        norm_freq = gain_frequency
    norm_factor = resp.get(
        "normalization_factor", calc_norm_factor(zeros, poles, norm_freq, pz_type)
    )
    if debug:
        print(
            "  Z=",
            zeros,
            " P=",
            poles,
            " A0={:g} at {:g} Hz".format(norm_factor, norm_freq),
        )
    return inventory.response.PolesZerosResponseStage(
        i_stage,
        gain_value,
        gain_frequency,
        units["input"],
        units["output"],
        pz_transfer_function_type=pz_type,
        normalization_frequency=norm_freq,
        normalization_factor=norm_factor,
        zeros=zeros,
        poles=poles,
        input_units_description=units["input_description"],
        output_units_description=units["output_description"],
        description=stage["description"] if "description" in stage else None,
    )


def __make_coefficients(stage, i_stage, units, delay_correction, decimation_info,  nbr_stages, debug=False):
    resp = stage["filter"]
    gain_value, gain_frequency = __get_gain(stage)
    decim = {"delay": None, "factor": 1, "offset": None, "input_sr": None}
    correction = None
    if resp["type"].lower() == "hertz":
        cf_type = "ANALOG (HERTZ)"
    elif resp["type"].lower() == "digital":
        cf_type = "DIGITAL"
        decim = __get_decim_parms(stage)
        if delay_correction is True:
            correction = decim["delay"]
        elif type(delay_correction) is float and i_stage == nbr_stages:
            correction = delay_correction
        else:
            correction = 0.0
    else:
        cf_type = "ANALOG (RADIANS/S)"
    return inventory.response.CoefficientsTypeResponseStage(
        i_stage,
        gain_value,
        gain_frequency,
        units["input"],
        units["output"],
        cf_type,
        numerator=float(resp["numerator"]),
        denominator=float(resp["denominator"]),
        input_units_description=units["input_description"],
        output_units_description=units["output_description"],
        description=stage["description"],
        decimation_input_sample_rate=decim["input_sr"],
        decimation_factor=decim["factor"],
        decimation_offset=decim["offset"],
        decimation_delay=decim["delay"],
        decimation_correction=correction,
    )


def __make_FIR(stage, i_stage, units, delay_correction, decimation_info, nbr_stages, debug=False):
    resp = stage["filter"]
    if debug:
        print(resp)
    gain_value, gain_frequency = __get_gain(stage)
    decim = __get_decim_parms(stage, decimation_info)
    if delay_correction is True:
        correction = decim["delay"]
    elif type(delay_correction) is float and i_stage == nbr_stages:
        correction = delay_correction
    else:
        correction = 0.0
    return inventory.response.FIRResponseStage(
        i_stage,
        gain_value,
        gain_frequency,
        "counts",
        "counts",
        symmetry=resp["symmetry"].upper(),
        coefficients=[
            obspy_types.FloatWithUncertaintiesAndUnit(x) for x in resp["coefficients"]
        ],
        input_units_description="Digital Counts",
        output_units_description="Digital Counts",
        description=stage["description"] if "description" in stage else None,
        decimation_input_sample_rate=decim["input_sr"],
        decimation_factor=decim["factor"],
        decimation_offset=decim["offset"],
        decimation_delay=decim["delay"],
        decimation_correction=correction,
    )


def __make_DIGITAL(stage, i_stage, units, decimation_info, debug=False):
    gain_value, gain_frequency = __get_gain(stage)
    decim = __get_decim_parms(stage, decimation_info)
    return inventory.response.CoefficientsTypeResponseStage(
        i_stage,
        gain_value,
        gain_frequency,
        units["input"],
        units["output"],
        "DIGITAL",
        numerator=[
            obspy_types.FloatWithUncertaintiesAndUnit(
                1.0, lower_uncertainty=0.0, upper_uncertainty=0.0
            )
        ],
        denominator=[],
        input_units_description=units["input_description"],
        output_units_description=units["output_description"],
        description=stage["description"] if "description" in stage else None,
        decimation_input_sample_rate=decim["input_sr"],
        decimation_factor=decim["factor"],
        decimation_offset=decim["offset"],
        decimation_delay=decim["delay"],
        decimation_correction=float(stage.get("decimation_correction", 0.0)),
    )


def __make_ANALOG(stage, i_stage, units, debug=False):
    gain_value, gain_frequency = __get_gain(stage)
    # Force to PolesZeros without Poles or Zeros
    return inventory.response.PolesZerosResponseStage(
        i_stage,
        gain_value,
        gain_frequency,
        units["input"],
        units["output"],
        input_units_description=units["input_description"],
        output_units_description=units["output_description"],
        description=stage["description"] if "description" in stage else None,
        pz_transfer_function_type="LAPLACE (HERTZ)",
        normalization_frequency=0.0,
        normalization_factor=1.0,
        zeros=[],
        poles=[],
    )


#     return inventory.response.ResponseStage(\
#             i_stage,
#             gain_value, gain_frequency,
#             input_units, output_units,
#             input_units_description=input_units_description,
#             output_units_description=output_units_description,
#             description=stage['description']
#         )


def __get_gain(stage):
    gain = stage.get("gain", {})
    return float(gain.get("value", 1.0)), float(gain.get("frequency", 0.0))


def __get_decim_parms(stage, decimation_info):
    global last_output

    decim = dict()
    decim["factor"] = int(stage.get("decimation_factor", 1))

    if 'output_sample_rate' in stage:
        decim["input_sr"] = decim["factor"] * stage["output_sample_rate"]  
    elif  decimation_info and 'input_sample_rate' in decimation_info.keys():
        decim["input_sr"] = last_output
        last_output = decim["input_sr"] / decim["factor"]

    else:
        raise RuntimeError(f'Your stage {stage} does not have a "output_sample_rate" ')

    filter = stage["filter"]
    decim["offset"] = int(filter.get("delay.samples", 0))
    # cas sismob
    if "delay" in stage:
        decim["delay"] = stage["delay"]
    else:
        decim["delay"] = float(
            filter.get("delay", float(decim["offset"]) / float(decim["input_sr"]))
        )
    return decim


def equipment(equipment, resource_id=None, debug=False):
    """
    Create obspy EquipmentType from obs_info.equipment
    
    """
    if type(equipment) == dict:
        equipment = FDSN_EquipmentType(equipment)
    if not equipment.description:
        raise RuntimeError('Your equipment variable does not have a "description"')
    obspy_equipment = obspy_util.Equipment(
        type=equipment.type,
        description=equipment.description,
        manufacturer=equipment.manufacturer,
        vendor=equipment.vendor,
        model=equipment.model,
        serial_number=equipment.serial_number,
        installation_date=equipment.installation_date,
        removal_date=equipment.removal_date,
        calibration_dates=equipment.calibration_date,
        resource_id=resource_id,
    )
    if debug:
        print(equipment)
        print(obspy_equipment)
    return obspy_equipment


def comments(comments, processing, supplements, loc_code, location, debug=False):
    """
    Create obspy comments from station information
    
    Also stuffs fields that are otherwise not put into StationXML:
         "supplement" elements as JSON strings, 
          "location:location_methods" 
    """
    obspy_comments = []

    # add varible to check if clock_corrections is alredy commented
    clock_cor_commented = False
    if debug:
        print("supplements=", end="")
        print(supplements)

    if comments:
        obspy_comments += create_comments(comments)
    if supplements:  # ??
        for key, val in supplements.items():
            obspy_comments += create_comments(json.dumps({key: val}))
    if processing:
        for element in processing:
            if "clock_corrections" in element:
                clock_cor_commented = True
                for key, val in element["clock_corrections"].items():
                    obspy_comments += create_comments(
                        json.dumps({"clock_correction": {key: val}})
                    )
            else:
                obspy_comments += create_comments(element)

        if not clock_cor_commented:
            obspy_comments += create_comments(json.dumps({"clock_correction": None}))
    loc_comment = 'Using location "{}"'.format(loc_code)
    if "localisation_method" in location:
        loc_comment = loc_comment + ", localised using : {}".format(
            location["localisation_method"]
        )
        obspy_comments += create_comments(loc_comment)
    return obspy_comments


def lon_lats(location, debug=False):
    """ Calculate obspy util.Latitude and util.Longitude"""
    longitude = float(location.longitude)
    latitude = float(location.latitude)
    meters_per_degree_lat = 1852.0 * 60.0
    meters_per_degree_lon = 1852.0 * 60.0 * m.cos(latitude * m.pi / 180.0)
    lat_uncert = location.lat_uncertainty_m / meters_per_degree_lat
    lon_uncert = location.lon_uncertainty_m / meters_per_degree_lon
    # REDUCE UNCERTAINTIES TO 3 SIGNIFICANT FIGURES
    lat_uncert = float("{:.3g}".format(lat_uncert))
    lon_uncert = float("{:.3g}".format(lon_uncert))
    if debug:
        print(
            "{:.3f}+-{:.5f}, {:.3f}+-{:.5f}".format(
                longitude, lon_uncert, latitude, lat_uncert
            )
        )
    obspy_lat = obspy_util.Latitude(
        latitude, lower_uncertainty=lat_uncert, upper_uncertainty=lat_uncert
    )
    obspy_lon = obspy_util.Longitude(
        longitude, lower_uncertainty=lon_uncert, upper_uncertainty=lon_uncert
    )
    return obspy_lon, obspy_lat
