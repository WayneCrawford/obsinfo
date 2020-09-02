"""
Filter class and subclasses
"""
# Standard library modules
import math as m
import warnings

# Non-standard modules
from obspy.core.inventory.response import (PolesZerosResponseStage,
                                           FIRResponseStage,
                                           CoefficientsTypeResponseStage,
                                           ResponseListResponseStage,
                                           ResponseListElement)
import obspy.core.util.obspy_types as obspy_types

# Local modules


class Filter():
    """
    Filter superclass
    """
    def __init__(self, type="PolesZeros"):
        """
        Constructor
        """
        self.type = type

    @staticmethod
    def from_info_dict(info_dict):
        """
        Creates an appropriate Filter subclass from an info_dict
        """
        if "type" not in info_dict:
            warnings.warn('No "type" specified in info_dict')
            return None
        else:
            if info_dict['type'] == 'PolesZeros':
                obj = PolesZeros.from_info_dict(info_dict)
            elif info_dict['type'] == 'FIR':
                obj = FIR.from_info_dict(info_dict)
            elif info_dict['type'] == 'Coefficients':
                obj = Coefficients.from_info_dict(info_dict)
            elif info_dict['type'] == 'ResponseList':
                obj = ResponseList.from_info_dict(info_dict)
            elif info_dict['type'] == 'ADConversion':
                obj = AD_Conversion.from_info_dict(info_dict)
            elif info_dict['type'] == 'Analog':
                obj = Analog.from_info_dict(info_dict)
            elif info_dict['type'] == 'Digital':
                obj = Digital.from_info_dict(info_dict)
            else:
                warnings.warn(f'Unknown Filter type: "{info_dict["type"]}"')
        return obj


class PolesZeros(Filter):
    """
    PolesZeros Filter
    """
    def __init__(self, transfer_function_type='LAPLACE (RADIANS/SECOND)',
                 poles=[], zeros=[],
                 normalization_frequency=None, normalization_factor=None):
        """
        poles and zeros should be lists of complex numbers
        """
        # self.type = 'PolesZeros'
        self.transfer_function_type = transfer_function_type
        self.poles = poles
        self.zeros = zeros
        self.normalization_frequency = normalization_frequency
        self.normalization_factor = self._set_normalization_factor(
            normalization_factor)

    def _set_normalization_factor(self, given_factor):
        """
        Set the normalization factor based on what was input

        :param given_factor: given normalization factor
        """
        warn_pct = 2
        if self.normalization_frequency:
            self.normalization_factor = self.calc_normalization_factor()
            if given_factor:
                if abs((self.normalization_factor - given_factor)
                       / given_factor) > warn_pct/100.:
                    warnings.warn('given normalization factor more than '
                                  '{:g}% off from calculated ({:g} vs {:g})'
                                  .format(warn_pct, given_factor,
                                          self.normalization_factor))
        elif given_factor is None:
            self.normalization_factor = 1
        else:
            self.normalization_factor = given_factor

    @classmethod
    def from_info_dict(cls, info_dict):
        """
        Create PolesZeros instance from an info_dict
        """
        obj = cls(info_dict.get('transfer_function_type',
                                'LAPLACE (RADIANS/SECOND)'),
                  [(float(x[0]) + 1j*float(x[1]))
                   for x in info_dict.get('poles', [])],
                  [(float(x[0]) + 1j*float(x[1]))
                   for x in info_dict.get('zeros', [])],
                  info_dict.get('normalization_frequency', None),
                  info_dict.get('normalization_factor', None))
        return obj

    def __repr__(self):
        """
        String representation of object
        """
        s = f'PolesZeros("{self.units}", {self.poles}, {self.zeros}, '
        s += f'{self.normalization_frequency:g}, '
        s += f'{self.normalization_factor:g})'
        return s

    def calc_normalization_factor(self, debug=False):
        """
        Calculate the normalization factor for give poles-zeros

        The norm factor A0 is calculated such that
                           sequence_product_over_n(s - zero_n)
                A0 * abs(------------------------------------------) === 1
                           sequence_product_over_m(s - pole_m)
        for s_f=i*2pi*f if the transfer function is in radians
                i*f     if the transfer funtion is in Hertz
        """
        if not self.normalization_frequency:
            if len(self.poles) > 0 or len(self.zeros) > 0:
                warnings.warn('No normalization frequency: could not '
                              'calculate normalization factor')
            return 1.

        A0 = 1.0 + (1j * 0.0)
        if self.transfer_function_type == "LAPLACE (HERTZ)":
            s = 1j * self.normalization_frequency
        elif self.transfer_function_type == "LAPLACE (RADIANS/SECOND)":
            s = 1j * 2 * m.pi * self.normalization_frequency
        else:
            print("Don't know how to calculate normalization factor "
                  "for z-transform poles and zeros!")
            return False
        for p in self.poles:
            A0 *= (s - p)
        for z in self.zeros:
            A0 /= (s - z)

        if debug:
            print("poles={}, zeros={}, s={:g}, A0={:g}".format(
                self.poles, self.zeros, s, A0))

        A0 = abs(A0)
        return A0

    def to_obspy(self, **stage_kwargs):
        """
        create an obspy PolesZerosResponseStage

        :param **stage_kwargs: stage-specfic keyword arguments: stage_gain,
            stage_gain_frequency, input_units, output_units, name,
            input_units_description, output_units_description, description,
            decimation_input_sample_rate, decimation_factor,
            decimation_offset, decimation_delay, decimation_correction
        :kind **stage_kwargs: dict
        """
        return PolesZerosResponseStage(
            **stage_kwargs,
            pz_transfer_function_type=self.transfer_function_type,
            normalization_frequency=self.normalization_frequency,
            zeros=[obspy_types.ComplexWithUncertainties(
                   t, lower_uncertainty=0.0, upper_uncertainty=0.0)
                   for t in self.zeros],
            poles=[obspy_types.ComplexWithUncertainties(
                   t, lower_uncertainty=0.0, upper_uncertainty=0.0)
                   for t in self.poles],
            normalization_factor=self.calc_normalization_factor())


class FIR(Filter):
    """
    FIR Filter
    """
    def __init__(self, symmetry, delay_samples, coefficients,
                 coefficient_divisor):
        # self.type = 'FIR'
        self.symmetry = symmetry
        if symmetry not in ['ODD', 'EVEN', 'NONE']:
            warnings.warn(f'Illegal FIR symmetry: "{symmetry}"')
        self.delay_samples = delay_samples
        self.coefficients = coefficients
        self.coefficient_divisor = coefficient_divisor

    @classmethod
    def from_info_dict(cls, info_dict):
        """
        Create PolesZeros instance from an info_dict
        """
        obj = cls(symmetry=info_dict.get('symmetry', 'NONE'),
                  delay_samples=info_dict.get('delay.samples', None),
                  coefficients=info_dict.get('coefficients', []),
                  coefficient_divisor=info_dict.get('coefficient_divisor', 1.))
        return obj

    def __repr__(self):
        """
        String representation of object
        """
        s = f'FIR("{self.symmetry}", {self.delay_samples:g}, '
        s += f'{self.coefficients}, {self.coefficient_divisor})'
        return s

    def to_obspy(self, **stage_kwargs):
        """
        create an obspy FIRResponseStage

        :param **stage_kwargs: stage-specfic keyword arguments: stage_gain,
            stage_gain_frequency, input_units, output_units, name,
            input_units_description, output_units_description, description,
            decimation_input_sample_rate, decimation_factor,
            decimation_offset, decimation_delay, decimation_correction
        :kind **stage_kwargs: dict
        """
        return FIRResponseStage(
            **stage_kwargs,
            symmetry=self.symmetry,
            coefficients=[obspy_types.FloatWithUncertaintiesAndUnit(
                c / self.coefficient_divisor)
                          for c in self.coefficients])


class Coefficients(Filter):
    """
    Coefficients Filter
    """
    def __init__(self, transfer_function_type, numerator_coefficients,
                 denominator_coefficients):
        if transfer_function_type not in ["ANALOG (RADIANS/SECOND)",
                                          "ANALOG (HERTZ)",
                                          "DIGITAL"]:
            warnings.warn('Illegal transfer function type: "{}"'.format(
                transfer_function_type))
        self.transfer_function_type = transfer_function_type
        self.numerator_coefficients = numerator_coefficients
        self.denominator_coefficients = denominator_coefficients

    @classmethod
    def from_info_dict(cls, info_dict):
        """
        Create PolesZeros instance from an info_dict
        """
        obj = cls(info_dict.get('transfer_function_type', 'DIGITAL'),
                  info_dict.get('numerator_coefficients', []),
                  info_dict.get('denominator_coefficients', []))
        return obj

    def __repr__(self):
        s = f'Coefficients("{self.transfer_function_type}", '
        s += f'{self.numerator_coefficients}, '
        s += f'{self.denominator_coefficients})'
        return s

    def to_obspy(self, **stage_kwargs):
        """
        create an obspy CoefficientsTypeResponseStage

        :param **stage_kwargs: stage-specfic keyword arguments: stage_gain,
            stage_gain_frequency, input_units, output_units, name,
            input_units_description, output_units_description, description,
            decimation_input_sample_rate, decimation_factor,
            decimation_offset, decimation_delay, decimation_correction
        :kind **stage_kwargs: dict
        """
        return CoefficientsTypeResponseStage(
            **stage_kwargs,
            cf_transfer_function_type=self.transfer_function_type,
            numerator=[obspy_types.FloatWithUncertaintiesAndUnit(
                n, lower_uncertainty=0.0, upper_uncertainty=0.0)
                for n in self.numerator_coefficients],
            denominator=[obspy_types.FloatWithUncertaintiesAndUnit(
                n, lower_uncertainty=0.0, upper_uncertainty=0.0)
                for n in self.denominator_coefficients])


class ResponseList(Filter):
    """
    ResponseList Filter
    """
    def __init__(self, response_list):
        """
        :param response_list: list of [freq, gain, phase]
        :kind response_list: list of 3-lists
        """
        assert len(response_list) > 2,\
            'response_list must have at least two elements'
        for element in response_list:
            assert len(element) == 3,\
                'response_list element does not have 3 items'
        self.response_list = response_list

    @classmethod
    def from_info_dict(cls, info_dict):
        """
        Create PolesZeros instance from an info_dict
        """
        obj = cls(info_dict['elements'])
        return obj

    def __repr__(self):
        return f'ResponseList("{self.response_list}")'

    def to_obspy(self, **stage_kwargs):
        """
        create an obspy ResponseListResponseStage

        :param **stage_kwargs: stage-specfic keyword arguments: stage_gain,
            stage_gain_frequency, input_units, output_units, name,
            input_units_description, output_units_description, description,
            decimation_input_sample_rate, decimation_factor,
            decimation_offset, decimation_delay, decimation_correction
        :kind **stage_kwargs: dict
        """
        response_list_elements = [ResponseListElement(x[0], x[1], x[2])
                                  for x in self.response_list]
        return ResponseListResponseStage(
            **stage_kwargs,
            response_list_elements=response_list_elements)


class Analog(PolesZeros):
    """
    Analog Filter (Flat PolesZeros filter)
    """
    def __init__(self):
        # self.type = 'Analog'
        self.transfer_function_type = 'LAPLACE (RADIANS/SECOND)'
        self.units = 'rad/s'
        self.poles = []
        self.zeros = []
        self.normalization_frequency = None
        self.normalization_factor = 1.

    @classmethod
    def from_info_dict(cls, info_dict):
        """
        Create Analog instance from an info_dict
        """
        obj = cls()
        return obj

    def __repr__(self):
        return 'Analog()'


class Digital(Coefficients):
    """
    Digital Filter (Flat Coefficients filter)
    """
    def __init__(self):
        self.transfer_function_type = 'DIGITAL'
        self.numerator_coefficients = [1.0]
        self.denominator_coefficients = []

    @classmethod
    def from_info_dict(cls, info_dict):
        """
        Create Digital instance from an info_dict
        """
        obj = cls()
        return obj

    def __repr__(self):
        return 'Digital()'


class AD_Conversion(Coefficients):
    """
    AD_Conversion Filter (Flat Coefficients filter)
    """
    def __init__(self, input_full_scale, output_full_scale):
        self.transfer_function_type = 'DIGITAL'
        self.numerator_coefficients = [1.0]
        self.denominator_coefficients = []
        self.input_full_scale = input_full_scale
        self.output_full_scale = output_full_scale

    @classmethod
    def from_info_dict(cls, info_dict):
        """
        Create AD_Conversion instance from an info_dict
        """
        obj = cls(info_dict.get('input_full_scale', None),
                  info_dict.get('output_full_scale', None))
        return obj

    def __repr__(self):
        s = f'AD_Conversion({self.input_full_scale:g}, '
        s += f'{self.output_full_scale})'
        return s
