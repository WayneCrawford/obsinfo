"""
Response Stage class
"""
# Standard library modules
import warnings

# Non-standard modules
from obspy.core.inventory.response import (PolesZerosResponseStage,
                                           FIRResponseStage,
                                           CoefficientsTypeResponseStage,
                                           ResponseListResponseStage)
from obspy.core.inventory.response import Response as obspy_Response
from obspy.core.inventory.response import InstrumentSensitivity\
                                   as obspy_Sensitivity
import obspy.core.util.obspy_types as obspy_types

# Local modules
from .filter import (Filter, PolesZeros, FIR, Coefficients, ResponseList,
                     Analog, Digital, AD_Conversion)
from .stage import Stage


class ResponseStages():
    """
    ReponseStages class

    An ordered list of Stages
    """
    def __init__(self, stages):
        self.stages = stages
        self._assure_continuity()

    def __repr__(self):
        s = f'Response_Stages([{len(self.stages):d}x{type(self.stages[0])}])'
        return s

    def __len__(self):
        return len(self.stages)

    def __add__(self, other):
        """
        Add two Response_Stages objects together

        The first object will have its stages before before the second's
        """
        stages = self.stages.copy()
        stages.extend(other.stages)
        return(ResponseStages(stages))

    def _assure_continuity(self):
        """
        Number stages sequentially and verify/set units and sample rates
        """
        # Order the stage_sequence_numbers
        for i in range(len(self.stages)):
            self.stages[i].stage_sequence_number = i+1

        stage = self.stages[0]
        for next_stage in self.stages[1:]:
            # Verify continuity of units
            assert stage.output_units == next_stage.input_units,\
                "Stage {:d} and {:d} units don't match".format(
                    stage.stage_sequence_number,
                    next_stage.stage_sequence_number)
            # Verify continuity of sample rate
            if stage.output_sample_rate:
                assert next_stage.decimation_factor,\
                    'No decimation_rate for stage {:d}'.format(
                        next_stage.stage_sequence_number)
                next_rate = (stage.output_sample_rate
                             / next_stage.decimation_factor)
                if next_stage.output_sample_rate:
                    assert next_stage.output_sample_rate == next_rate,\
                        'stage {:d} sample rate ({:g}) != expected ({:g})'.\
                        format(next_stage.stage_sequence_number,
                               next_stage.output_sample_rate,
                               next_rate)
                else:
                    next_stage.output_sample_rate = next_rate
            stage = next_stage

    def extend(self, other):
        """
        Extend one ResponseStages with another

        Same as __add__
        """
        return self + other

    @classmethod
    def from_info_dict(cls, info_dict):
        """
        Create instance from an info_dict

        info_dict is just a list of Stage()s in this case
        """
        if info_dict is None:
            return []
        obj = cls([Stage.from_info_dict(s) for s in info_dict])
        return obj

    def to_obspy(self, delay_correction):
        """
        Return equivalent obspy response class
        
        :param delay_correction: delay correction :
            if it's a number, zero is applied to all stages and the value is
                applied to the last stage
            if it's True, each stage's correction is set equal to its delay
            otherwise, correction is untouched
        :kind delay_correction: bool or number
        """
        # Apply delay correction
        if delay_correction is True:
            for s in self.stages:
                s.correction = s.delay
        else:
            try:
                val = float(delay_correction)
                for s in self.stages[:-1]:
                    s.correction = 0
                self.stages[-1].correction = val
            except ValueError:
                pass
            
        obj = obspy_Response(
            response_stages=[s.to_obspy() for s in self.stages])
        obj = self._add_sensitivity(obj)
        return obj

    def _add_sensitivity(self, obspy_resp, debug=False):
        """
        Adds sensitivity to an obspy Response object

        Based on ..misc.obspy_routines.response_with_sensitivity
        """

        input_units = self.stages[0].input_units
        true_input_units = self.stages[0].input_units
        if "PA" in true_input_units.upper():
            # MAKE OBSPY THINK ITS M/S TO CORRECTLY CALCULATE SENSITIVITY
            input_units = "M/S"
        gain_prod = 1.
        for stage in self.stages:
            gain_prod *= stage.gain
        sensitivity = obspy_Sensitivity(
            gain_prod,
            self.stages[0].gain_frequency,
            input_units=input_units,
            output_units=self.stages[-1].output_units,
            input_units_description=self.stages[0].input_units_description,
            output_units_description=self.stages[-1].output_units_description
            )
        if debug:
            print(sensitivity, obspy_resp)
            for stage in obspy_resp.response_stages:
                print(stage)
        obspy_resp.instrument_sensitivity = sensitivity
        obspy_resp.recalculate_overall_sensitivity(sensitivity.frequency)
        obspy_resp.instrument_sensitivity.input_units = true_input_units

        return obspy_resp
