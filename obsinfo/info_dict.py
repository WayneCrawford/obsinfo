"""
obsinfo information dictionary routines
"""
# Standard library modules
from collections import UserDict
import warnings

# Non-standard modules

# Local modules


class UpDict(dict):
    """
    dict with improved update() function
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.propagate()    # Make all contained dicts and UserDicts UpDicts
    
    def update(self, update_dict, allow_overwrite=True):
        """
        Update that only changes explicitly specfied fields

        Drills recursively through dicts inside the dict, only changing fields
        which are specified in update_dict

        :param update_dict: dictionary containing fields to update
        :param allow_overwrite: allow a field that was originally a dict to be
                         overwritten by a field that is not a dict
        :type allow_overwrite: bool

        >>> a = UpDict(a='j', b=UpDict(c=5, d=6))
        >>> a.update({'b': {'d': 2, 'e': 3}})
        >>> a
        {'a': 'j', 'b': {'c': 5, 'd': 2, 'e': 3}}
        >>> a=UpDict(a='j', b=dict(c=5, d=6))
        >>> a._purity_check()
        True
        >>> a.update({'b': {'d': 2, 'e': 3}})
        >>> a
        {'a': 'j', 'b': {'c': 5, 'd': 2, 'e': 3}}
        >>> a._purity_check()
        True
        >>> a=UpDict(a='j', b={'c': 5, 'd': 6})
        >>> a.update({'b': {'d': 2, 'e': 3}})
        >>> a
        {'a': 'j', 'b': {'c': 5, 'd': 2, 'e': 3}}
        >>> a=UpDict(a='j', b=UpDict(c=5, d=6))
        >>> a.update({'a': 5, 'c': [1, 3]})
        >>> a
        {'a': 5, 'b': {'c': 5, 'd': 6}, 'c': [1, 3]}

        For some reason, the following gives None
        UpDict(a='j', b=UpDict(c=5, d=6)).update({'a': 5, 'c': [1, 3]})
        But it's the same for dict as well
        """
        for key, value in update_dict.items():
            # print(f'{key}')
            if key not in self:  # Add new key and its value
                if isinstance(value, (dict, UserDict)):
                    value = self.__class__(value)
                self[key] = value
            else:  # Key exists in self:
                if isinstance(self[key], (dict, UserDict)):
                    # if value is also a dictionary, update it
                    if isinstance(value,  (dict, UserDict)):
                        # if replacement value is a dictionary, recurse
                        self[key].update(self.__class__(value))
                    else:
                        # print(f'{key} : replace not dict')
                        # if replacement value is not a dictionary
                        if allow_overwrite:  # replace & warn
                            if isinstance(value,  (dict, UserDict)):
                                value = self.__class__(value)
                            self[key] = value
                            warnings.warn(
                                f'field "{key}" was a dict, '
                                'replaced by a non-dict')
                        else:  # reject & warn
                            warnings.warn(
                                f'replacement field "{key}" not inserted into '
                                'original because original was a dict and '
                                'replacement was not')
                elif isinstance(self[key], list) and isinstance(value,  list):
                    # if replacement value is a list, recurse on contents
                    # Does not handle directly nested lists
                    for i in range(len(value)):
                        newitem = value[i]
                        if newitem:
                            if isinstance(newitem, (dict, UserDict)):
                                self[key][i].update(__class__(newitem))
                            else:
                                self[key][i] = newitem
                else:
                    # Replace existing others
                    if isinstance(value, (dict, UserDict)):
                        value = self.__class__(value)
                    self[key] = value


    def propagate(self):
        """
        Make all contained dictionaries UpDicts
        """
        for key, value in self.items():
            if isinstance(value,  (dict, UserDict)):
                self[key] = self.__class__(value)
                self[key].propagate()
                
    def _purity_check(self):
        """
        Return true if all internal dicts are also UpDicts
        """
        for key, value in self.items():
            if (isinstance(value,  (dict, UserDict))):
                if isinstance(value, self.__class__):
                    if not value._purity_check():
                        return False
                else:
                    return False
        return True                


class InfoDict(UpDict):
    """
    UpDict subclass with specific obsinfo-savvy routines
    """                
#    def complete_das_channels(self):
#        """
#        Complete 'das_channels' using 'base_channel'.
#
#        Fields must be at the top level.
#        'base_channel' is deleted
#
#        >>> A = InfoDict(base_channel={'a': 5, 'b':6},
#                         das_channels={'1': {'a': 7}, '2': {'b':0}})
#        >>> A.complete_das_channels()
#        >>> A
#        {'das_channels': {'1': {'a': 7, 'b': 6}, '2': {'a': 5, 'b': 0}}}
#        """
#        assert 'das_channels'  in self, f"No 'das_channels' key in {self.keys()}"
#        assert 'base_channel' in self, f"No 'base_channel' key in {self.keys()}"
#        for key, value in self['das_channels'].items():
#            # print(f'"{key}"')
#            temp = InfoDict(value)
#            self['das_channels'][key] = InfoDict(self['base_channel'])
#            self['das_channels'][key].update(temp)
#        del self['base_channel']

    def update_by_config_SN(self, config=None, serial_number=None):
        """
        Update by configuration and/or serial number

        Assumes that the input dict has one (or both) of the fields
        "configurations" and/or "serial_numbers" ("configurations" can
        also have "serial_numbers" inside.

        Removes the "configurations" and "serial_numbers" fields from the dict
        and updates its remaining fields with values provided, in the
        following order:
            1) serial_numbers/{serial_number}
            2) configurations/{config}
            3) configurations/{config}/serial_numbers/{serial_number}

        :param config: the desired configuration
        :param serial_number: the desired serial number
        :type config, serial_number: str
        """
        if "serial_numbers" in self:
            if serial_number:
                if serial_number in self["serial_numbers"]:
                    self.update(self["serial_numbers"][serial_number])
            del self["serial_numbers"]
        if "configurations" in self:
            if config:
                if config in self["configurations"]:
                    dict_config = self["configurations"][config]
                    self.update(dict_config)
                    if "serial_numbers" in dict_config:
                        if serial_number:
                            if serial_number in dict_config["serial_numbers"]:
                                self.update(
                                    dict_config["serial_numbers"][
                                        serial_number])
                else:
                    raise NameError('Configu "{}" absent from {}'.format(
                                    config, self["configurations"].keys()))
            del self["configurations"]
        elif config:
            print(f'Configuration "{config}" requested, '
                  'but no configurations!')
            # pprint.pprint(in_dict)


if __name__ == "__main__":
    import doctest
    doctest.testmod()
