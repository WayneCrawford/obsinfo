"""
Processsing class
"""
# Standard library modules
import pprint

# Non-standard modules
# import obspy.core.inventory.util as obspy_util

# obsinfo modules

pp = pprint.PrettyPrinter()


class Processing(object):
    """
    Processing Class.

    Saves a list of Processing steps
    For now, just stores the list
    """
    def __init__(self, the_list):
        """
        :param the_list: list of processing steps
        :type list: list
        """
        self.list = the_list

    @classmethod
    def from_info_dict(cls, info_dict):
        """
        Create instance from an info_dict

        Currently just passes the list that should be at this level
        :param info_dict: info_dict at station:processing level
        :type info_dict: dict
        """
        if not isinstance(info_dict, list):
            return None
        obj = cls(info_dict)
        return obj

    def __repr__(self):
        s = f'Processing({self.list})'
        return s
