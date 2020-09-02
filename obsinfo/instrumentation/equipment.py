"""
Equipment class and subclasses.

Stored directly as an obspy Equipment object
"""
# Standard library modules

# Non-standard modules
from obspy.core.inventory.util import Equipment as obspyEquipment


class Equipment(obspyEquipment):
    """
    Equipment class (subclass of obspy.core.inventory.util.Equipment)
    """

    @classmethod
    def from_info_dict(cls, info_dict):
        """
        Create Equipment instance from an info_dict

        param info_dict: equipment-level information dictionary
        :kind info_dict: ~class InfoDict
        """
        obj = cls(type=info_dict.get('type', None),
                  description=info_dict.get('description', None),
                  manufacturer=info_dict.get('manufacturer', None),
                  model=info_dict.get('model', None),
                  vendor=info_dict.get('vendor', None),
                  serial_number=info_dict.get('serial_number', None),
                  calibration_dates=info_dict.get('calibration_dates', None))
        return obj

    def to_obspy(self):
        """
        Return equivalent obspy object
        """
        return self
