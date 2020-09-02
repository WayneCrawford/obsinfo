"""
ObsPy-specific routines
"""
# Standard library modules
# import math as m
# import json
# import pprint
# import os.path
# import sys

# Non-standard modules
# import yaml
# import obspy.core.util.obspy_types as obspy_types
# import obspy.core.inventory as inventory
import obspy.core.inventory.util as obspy_util
# from obspy.core.utcdatetime import UTCDateTime

# from .misc import calc_norm_factor

last_output = None


def make_comment_from_str(input):
    """
    Make an obspy Commment object from a string

    :param input: str
    """
    assert type(input) is str, "input is not a str"
    return obspy_util.Comment(input)

# def response_with_sensitivity(resp_stages, sensitivity, debug=False):
#     """
#     Returns obspy Response object with sensitivity
#
#     :param resp_stages: list of obspy ResponseStages
#     :param sensitivity: a guess of sensitivity based on individual stage
#         gains
#     """
#     true_sensitivity_input_units = None
#
#     # HAVE TO MAKE OBSPY THINK ITS M/S FOR IT TO CALCULATE SENSITIVITY
#     # CORRECTLY FOR PRESSURE
#     if "PA" in sensitivity["input_units"].upper():
#         true_sensitivity_input_units = sensitivity["input_units"]
#         sensitivity["input_units"] = "M/S"
#     response = inventory.response.Response(
#         instrument_sensitivity=inventory.response.InstrumentSensitivity(
#             sensitivity["guess"],
#             sensitivity["freq"],
#             input_units=sensitivity["input_units"],
#             output_units=sensitivity["output_units"],
#             input_units_description=sensitivity["input_units_description"],
#             output_units_description=sensitivity["output_units_description"],
#         ),
#         response_stages=resp_stages,
#     )
#     # response.plot(min_freq=0.001)
#     guesstimate = response.instrument_sensitivity.value
#     response.recalculate_overall_sensitivity(sensitivity["freq"])
#     if debug:
#         calculated = response.instrument_sensitivity.value
#         print("Guesstimated vs calculated sensitivity at {:g} Hz : "
#               "{:.3g} vs {:.3g} ({:.1g}% difference)".format(
#                 response.instrument_sensitivity.frequency,
#                 guesstimate,
#                 calculated,
#                 100.0 * abs(guesstimate - calculated) / calculated))
#     if true_sensitivity_input_units:
#         response.instrument_sensitivity.input_units =\
#               true_sensitivity_input_units
#     return response
#
#
# def response(my_responses, debug=False):
#     """
#     Create an obspy response object from a response_yaml-based list of stages
#     """
#     global last_output
#     resp_stages = []
#     i_stage = 0
#     sensitivity = dict()
#     if debug:
#         print(len(my_responses), "stages") #??
#     #delay_correction = my_response.get("delay_correction",False)
#     nbrS = get_nb_stages(my_responses)
#     for my_response in my_responses:
#         # temporary
#         if my_response['decimation_info'] :
#             key_with_p = [k for k in my_response['decimation_info'].keys()\
#                     if '.' in k ]
#             if len(key_with_p) !=0:
#                 delay_correction = my_response['decimation_info'][
#                                                key_with_p[0]]
#             else:
#                 delay_correction = my_response['decimation_info'][
#                                    'delay_correction']\
#                           if my_response['decimation_info'] else False
#             if 'input_sample_rate' in my_response['decimation_info']:
#                 last_output = my_response['decimation_info'][
#                                           'input_sample_rate']
#         decimation_info = my_response['decimation_info']\
#                           if 'decimation_info' in my_response else None
#         for stage in my_response['stages']:
#             # DEFINE COMMON VALUES
#             i_stage = i_stage + 1
#             #         if debug:
#             #             print("stage=",end='')
#             #             print(yaml.dump(stage))
#
#             units, sensitivity = __get_units_sensitivity(
#                                      stage, sensitivity, i_stage)
#             resp_type = stage["filter"]["type"]
#             if debug:
#                 print("i_stage=", i_stage, ", resp_type=", resp_type)
#             # Create and append the appropriate response
#             if resp_type == "PolesZeros":
#                 resp_stages.append(__make_poles_zeros(stage, i_stage, units))
#             elif resp_type == "COEFFICIENTS":
#                 resp_stages.append(
#                       __make_coefficients(stage, i_stage, units,
#                                           delay_correction, decimation_info,
#                                           nbrS))
#             elif resp_type == "FIR":
#                 resp_stages.append(__make_FIR(stage, i_stage, units,
#                                               delay_correction,
#                                               decimation_info, nbrS))
#             elif resp_type == "AD_CONVERSION":
#                 resp_stages.append(__make_DIGITAL(stage, i_stage, units,
#                                                   decimation_info))
#             elif resp_type == "ANALOG":
#                 resp_stages.append(__make_ANALOG(stage, i_stage, units))
#             else:
#                 raise TypeError("UNKNOWN STAGE RESPONSE TYPE: {}".format(
#                                 resp_type))
#     response = response_with_sensitivity(resp_stages, sensitivity)
#     if debug:
#         print(response)
#     return response
#
#
# def get_nb_stages(responses):
#     s = 0
#     for i in responses:
#         s = s + len(i['stages'])
#     return s
#
#
# def __get_units_sensitivity(stage, sensitivity, i_stage):
#     """
#     Return output units and sensitivity of stages up to present
#
#     sensitivity is a dictionary with "input_units", "input_units_description"
#         and "freq" being set by the first stage.  "guess" being the product
#         of the gains of all stages
#
#     units are for the current stage
#     """
#     units = dict()
#     temp = stage.get("input_units", {})
#     units["input"] = temp.get("name", None)
#     units["input_description"] = temp.get("description", None)
#     temp = stage.get("output_units", {})
#     units["output"] = temp.get("name", None)
#     units["output_description"] = temp.get("description", None)
#     # Set Sensitivity
#     gain_value, gain_frequency = __get_gain(stage)
#     if i_stage == 1:
#         sensitivity = {
#             "input_units": units["input"],
#             "input_units_description": units["input_description"],
#             "freq": gain_frequency,
#             "guess": gain_value,
#         }
#     else:
#         sensitivity["guess"] = sensitivity["guess"] * gain_value
#     if units["output"]:
#         sensitivity["output_units"] = units["output"]
#         sensitivity["output_units_description"] = units["output_description"]
#     return units, sensitivity
#
#
# def __get_gain(stage):
#     gain = stage.get("gain", {})
#     return float(gain.get("value", 1.0)), float(gain.get("frequency", 0.0))
#
#
# def __get_decim_parms(stage, decimation_info):
#     global last_output
#     decim = dict()
#     decim["factor"] = int(stage.get("decimation_factor", 1))
#     if 'output_sample_rate' in stage:
#         decim["input_sr"] = decim["factor"] * stage["output_sample_rate"]
#     elif  decimation_info and 'input_sample_rate' in decimation_info.keys():
#         decim["input_sr"] = last_output
#         last_output = decim["input_sr"] / decim["factor"]
#     else:
#         raise RuntimeError(f'Your stage {stage} does not have a'
#                            '"output_sample_rate" ')
#     filter = stage["filter"]
#     decim["offset"] = int(filter.get("delay.samples", 0))
#     # cas sismob
#     if "delay" in stage:
#         decim["delay"] = stage["delay"]
#     else:
#         decim["delay"] = float(
#             filter.get("delay",
#                        float(decim["offset"]) / float(decim["input_sr"]))
#         )
#     return decim
