"""
InstrumentComponent class and subclasses.

No StationXML equivalent.
"""
# Standard library modules
# import math as m
import pprint

# Non-standard modules
from obspy.core.inventory.util import Equipment as obspyEquipment


pp = pprint.PrettyPrinter(depth=2)


class Equipment(obspyEquipment):
    """
    Equipment class (subclass of obspy.core.inventory.util.Equipment)
    """
    #def __init__(self, type, description, manufacturer, model,
    #             vendor=None, serial_number=None, installation_date=None,
    #             removal_date=None, calibration_dates=None, resource_id=None):
    #    """
    #    Constructor
    #    
    #    :param type: Equipment type (seismometer, geophone, datalogger...)
    #    :kind type: str
    #    :param description: short description of the equipment
    #    :kind description: str
    #    :param manufacturer: short description of the equipment
    #    :kind manufacturer: str
    #    :param model: short description of the equipment
    #    :kind model: str
    #    :param vendor: short description of the equipment
    #    :kind description: str, optional
    #    :param serial_number: short description of the equipment
    #    :kind description: str, optional
    #    :param installation_date: short description of the equipment
    #    :kind description: str, optional
    #    :param removal_date: short description of the equipment
    #    :kind description: str, optional
    #    :param calibration_date: short description of the equipment
    #    :kind description: str, optional
    #    :param resource_id: short description of the equipment
    #    :kind description: str, optional
    #    """
    #    self.type = type
    #    self.description = description
    #    self.manufacturer = manufacturer
    #    self.model = model
    #    self.vendor = vendor
    #    self.serial_number = serial_number
    #    self.installation_date = installation_date
    #    self.removal_date = removal_date
    #    self.calibration_dates = calibration_dates or []
    #    self.resource_id = resource_id

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
        # print(obj)
        return obj

    def to_obspy(self):
        """
        Return equivalent obspy object
        """
        return self
        # return obspyEquipment(
        #     type=self.type,
        #     description=self.description,
        #     manufacturer=self.manufacturer,
        #     vendor=self.vendor,
        #     model=self.model,
        #     serial_number=self.serial_number,
        #     installation_date=self.installation_date,
        #     removal_date=self.removal_date,
        #     calibration_dates=self.calibration_dates,
        #     resource_id=self.resource_id)
