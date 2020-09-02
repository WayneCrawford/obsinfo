"""
Response Stage class
"""
# Standard library modules
import warnings

# Non-standard modules
# from obspy.core.inventory.response import Response as obspy_Response
# from obspy.core.inventory.response import InstrumentSensitivity\
#                                    as obspy_Sensitivity

# Local modules
from .filter import (Filter, PolesZeros, Analog)


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
                  input_units=info_dict.get('input_units', None)
                                       .get('name', None),
                  output_units=info_dict.get('output_units', None)
                                        .get('name', None),
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
        Offset in samples corresponding to the stage delay

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
        """

        filt = self.filter
        if (hasattr(filt, 'delay_samples')
                and self.input_sample_rate is not None):
            if self.delay == 0:
                self.delay = filt.delay_samples/self.input_sample_rate
            elif self.delay != filt.delay_samples/self.input_sample_rate:
                warnings.warn("stage delay != filter delay samples")
        kwargs = dict(stage_sequence_number=self.stage_sequence_number,
                      stage_gain=self.gain,
                      stage_gain_frequency=self.gain_frequency,
                      input_units=self.input_units,
                      output_units=self.output_units,
                      name=self.name,
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
        obj = filt.to_obspy(**kwargs)
        return obj
