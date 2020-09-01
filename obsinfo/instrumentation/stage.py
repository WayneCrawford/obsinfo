"""
Response Stage class
"""
# Standard library modules
import warnings

# Non-standard modules
from obspy.core.inventory.response import (PolesZerosResponseStage,
                                           FIRResponseStage,
                                           CoefficientsTypeResponseStage,
                                           ResponseListResponseStage,
                                           ResponseListElement)
from obspy.core.inventory.response import Response as obspy_Response
from obspy.core.inventory.response import InstrumentSensitivity\
                                   as obspy_Sensitivity
import obspy.core.util.obspy_types as obspy_types

# Local modules
from .filter import (Filter, PolesZeros, FIR, Coefficients, ResponseList,
                     Analog, Digital, AD_Conversion)


class Stage():
    """
    Stage class
    """
    def __init__(self, name, description, input_units, output_units, gain,
                 gain_frequency, filter, stage_sequence_number=-1,
                 input_units_description=None, output_units_description=None,
                 output_sample_rate=None, decimation_factor=1.,
                 delay=0., correction=0., calibration_date=None):
        self.name = name
        self.description = description
        self.input_units = input_units
        self.output_units = output_units
        self.gain = gain
        self.gain_frequency = gain_frequency
        self.filter = filter
        self.stage_sequence_number = stage_sequence_number
        self.input_units_description = input_units_description
        self.output_units_description = output_units_description
        self.output_sample_rate = output_sample_rate
        self.decimation_factor = decimation_factor
        self.delay = delay
        self.correction = correction
        self.calibration_date = calibration_date

    @classmethod
    def from_info_dict(cls, info_dict):
        """
        Create instance from an info_dict
        """
        gain_dict = info_dict.get('gain', {})
        obj = cls(name=info_dict.get('name', None),
                  description=info_dict.get('description', ''),
                  input_units=info_dict.get('input_units', None).get('name', None),
                  output_units=info_dict.get('output_units', None).get('name', None),
                  gain=gain_dict.get('value', 1.0),
                  gain_frequency=gain_dict.get('frequency', 0.0),
                  filter=Filter.from_info_dict(info_dict.get('filter', None)),
                  input_units_description=info_dict.get(
                    'input_units', None).get('description', None),
                  output_units_description=info_dict.get(
                    'output_units', None).get('description', None),
                  output_sample_rate=info_dict.get('output_sample_rate', None),
                  decimation_factor=info_dict.get('decimation_factor', 1),
                  delay=info_dict.get('delay', 0),
                  calibration_date=info_dict.get('calibration_date', None)
                  )
        return obj

    @property
    def input_sample_rate(self):
        if self.output_sample_rate and self.decimation_factor:
            return self.output_sample_rate * self.decimation_factor
        else:
            return None

    @property
    def offset(self):
        """
        offset in samples corresponding to the delay
        
        must be an integer
        """
        if hasattr(self.filter, 'delay_samples'):
            return self.filter.delay_samples
        else:
            if self.input_sample_rate is None:
                return 0
            else:
                return int(self.delay * self.input_sample_rate)

    # @input_sample_rate.setter
    # def input_sample_rate(self, x):
    #     assert self.decimation_factor,\
    #         'cannot set input_sample_rate without decimation_factor'
    #     self.output_sample_rate = x/self.decimation_factor

    def __repr__(self):
        s = f'Stage("{self.name}", "{self.description}", '
        s += f'"{self.input_units}", "{self.output_units}", '
        s += f'{self.gain:g}, {self.gain_frequency:g}, '
        s += f'{type(self.filter)}'
        if not self.stage_sequence_number == -1:
            s += f', stage_sequence_number="{self.stage_sequence_number}"'
        if self.input_units_description:
            s += f', input_units_description="{self.input_units_description}"'
        if self.output_units_description:
            s += f', output_units_description='
            s += f'"{self.output_units_description}"'
        if self.output_sample_rate:
            s += f', output_sample_rate={self.output_sample_rate:g}'
        if not self.decimation_factor == 1.:
            s += f', decimation_factor={self.decimation_factor:g}'
        if not self.delay == 0.:
            s += f', {self.delay:g}'
        if self.calibration_date:
            s += f', delay={self.calibration_date}'
        s += ')'
        return s

    def to_obspy(self):
        """
        Return equivalent obspy response stage
        
        The actual conversion to obspy filter types should be handled in filter.py
        """

        filt = self.filter
        if hasattr(filt, 'delay_samples') and self.input_sample_rate is not None:
            if self.delay == 0:
                self.delay = filt.delay_samples/self.input_sample_rate
            elif self.delay != filt.delay_samples/self.input_sample_rate:
                warnings.warn("stage delay does not equal filter delay samples")
        args = (self.stage_sequence_number,
                self.gain,
                self.gain_frequency,
                self.input_units,
                self.output_units)
        kwargs = dict(name=self.name,
                      input_units_description=self.input_units_description,
                      output_units_description=self.output_units_description,
                      description=self.description,
                      decimation_input_sample_rate=self.input_sample_rate,
                      decimation_factor=self.decimation_factor,
                      decimation_offset=self.offset,
                      decimation_delay=self.delay,
                      decimation_correction=self.correction)
        if isinstance(filt, PolesZeros) or isinstance(filt, Analog):
            if not filt.normalization_frequency:
                filt.normalization_frequency = self.gain_frequency
            obj = PolesZerosResponseStage(
                *args,
                **kwargs,
                pz_transfer_function_type=filt.transfer_function_type,
                normalization_frequency=filt.normalization_frequency,
                zeros=[obspy_types.ComplexWithUncertainties(
                    t, lower_uncertainty=0.0, upper_uncertainty=0.0)\
                    for t in filt.zeros],
                poles=[obspy_types.ComplexWithUncertainties(
                    t, lower_uncertainty=0.0, upper_uncertainty=0.0)\
                    for t in filt.poles],
                normalization_factor=filt.calc_normalization_factor())
        elif isinstance(filt, FIR):
            obj = FIRResponseStage(
                *args,
                **kwargs,
                symmetry=filt.symmetry,
                coefficients=[obspy_types.FloatWithUncertaintiesAndUnit(
                    c / filt.coefficient_divisor)
                              for c in filt.coefficients])
        elif (isinstance(filt, Coefficients)
                or isinstance(filt, Digital)
                or isinstance(filt, AD_Conversion)):
            obj = CoefficientsTypeResponseStage(
                *args,
                **kwargs,
                cf_transfer_function_type=filt.transfer_function_type,
                numerator=[obspy_types.FloatWithUncertaintiesAndUnit(
                    n, lower_uncertainty=0.0, upper_uncertainty=0.0)\
                    for n in filt.numerator_coefficients],
                denominator=[obspy_types.FloatWithUncertaintiesAndUnit(
                    n, lower_uncertainty=0.0, upper_uncertainty=0.0)\
                    for n in filt.denominator_coefficients])
        elif isinstance(filt, ResponseList):
            response_list_elements = [ResponseListElement(x[0],x[1],x[2])
                                      for x in filt.response_list]
            obj = ResponseListResponseStage(
                *args,
                **kwargs,
                response_list_elements=response_list_elements)
        else:
            warnings.warn(f'Unhandled response stage type: "{filt.type}"')
        return obj
