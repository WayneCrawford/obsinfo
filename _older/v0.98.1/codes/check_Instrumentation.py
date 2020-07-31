#!/usr/bin/env python3
import yaml
import pprint
from obsinfo import OBS_Instrumentation

instrument_file='../files/FACILITY.instrumentation.yaml'

instrumentation=OBS_Instrumentation(instrument_file)

print('\nFILENAME: {}'.format(instrument_file))
print('FACILITY: {}'.format(instrumentation.facility['reference_name']))
print('REVISION: {}'.format(instrumentation.revision))
# PRINT INSTRUMENTS
print('\n' + 20*'=')
print('INSTRUMENTS:')
instrumentation.print_elements()

# VERIFY THAT INSTRUMENTS & SENSORS LISTED IN "individuals" EXIST in "models"
print(20*'=')
if instrumentation.verify_individuals():
    print('All instruments have a generic counterpart')

# VERIFY THAT REFERRED TO FILES EXIST
print('\n' + 20*'=')
print('Checking dependencies on instrument_components_file')
file_exists,n_components,n_found,n_cites = instrumentation.check_dependencies(print_names=True)
if not file_exists :
    print('Instrument_Components file not found: {}'.format(instrumentation.components_file))
elif n_components==n_found :
    print('Found all {:d} specied functional components ({:d} total cites)'\
            ''.format(n_components,n_cites))
else:
    print('MISSING {:d} of {:d} specied functional components '\
            ''.format(n_components-n_found,n_components))