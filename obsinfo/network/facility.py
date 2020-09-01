"""
Facility class
"""
# Standard library modules

# Non-standard modules
from obspy.core.inventory.util import (Person, Operator)

# obsinfo modules


class Facility(object):
    """
    Store variables for facility in network class
    """
    def __init__(self, reference_name, full_name, email=None, website=None):
        """
        Constructor

        :param reference_name: Abbreviated filename-compatible name
        :param full_name: full facility name
        :param email: facility email address
        :param email: facility website
        """
        self.reference_name = reference_name
        self.full_name = full_name
        self.email = email
        self.website = website

    @classmethod
    def from_info_dict(cls, info_dict):
        """
        Create Instrumentation instance from an info_dict
        """
        obj = cls(info_dict['reference_name'],
                  info_dict.get('full_name', info_dict['reference_name']),
                  info_dict.get('email', None),
                  info_dict.get('website', None))
        return obj

    def __repr__(self):
        s = 'Facility("{}", "{}"'.format(self.reference_name, self.full_name)
        if self.email:
            s += ', email="{}"'.format(self.email)
        if self.website:
            s += ', website="{}"'.format(self.website)
        s += ')'
        return s

    def to_obspy(self):
        """
        create an obspy Operator object
        """
        agency = self.full_name
        contacts = None
        if self.email is not None:
            contacts = [Person(emails=[self.email])]
        website = self.website
        # return Operator([agency], contacts, website)
        return Operator(agency, contacts, website)
