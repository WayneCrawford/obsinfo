#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Functions to test the lcheapo functions
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from future.builtins import *  # NOQA @UnusedWildImport

import os
# import glob
import unittest
import inspect
# import xml.etree.ElementTree as ET
# from CompareXMLTree import XmlTree
# from obsinfo.network.network import _make_stationXML_script
# from obsinfo.misc.info_files import validate
from obsinfo.addons.LC2SDS import _get_leapsecond_string


class TestADDONSMethods(unittest.TestCase):
    """
    Test suite for obsinfo "addons".
    """
    def setUp(self):
        self.path = os.path.dirname(os.path.abspath(inspect.getfile(
            inspect.currentframe())))
        self.testing_path = os.path.join(self.path, "data")
        self.infofiles_path = os.path.join(os.path.split(self.path)[0],
                                           '_examples',
                                           'Information_Files')

    def test_LC2SDS_leapseconds_str(self):
        """
        Test leapseconds str creation.
        """
        leapsec_list = [dict(time='2020-12-31T23:59:60', type='+'),
                        dict(time='2021-06-30T23:59:58', type='-')]
        drift_dict = dict(start_sync_reference='2020-11-01T00:00:00',
                          start_sync_instrument='0',
                          end_sync_reference='2021-11-01T12:00:01.23456',
                          end_sync_instrument='2021-11-01T12:00:01')
        cc_dict = dict(clock_corrections=dict(leapseconds=leapsec_list,
                                              linear_drift=drift_dict))
        self.assertEqual(_get_leapsecond_string([cc_dict]),
                         '--leapsecond_times "2020-12-31T23:59:60" '
                         '"2021-06-30T23:59:58" --leapsecond_types "+-"')


def suite():
    return unittest.makeSuite(TestADDONSMethods, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
