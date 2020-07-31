import yaml
import pprint

network_file='EMSOMOMAR2016.network.yaml'
instrument_file='INSU-IPGP.instrumentation.yaml'

with open(network_file,'r') as f:
  stations=yaml.load(f)['network']['stations']
with open(instrument_file,'r') as f:
  instruments=yaml.load(f)['instrumentation']['models']
  
pp=pprint.PrettyPrinter(width=131, compact=True)

for name,station in stations.items():
  # Find associated instrument
  inst_model=station['instrument']['model']
  inst_SN  =station['instrument']['serial_number']
  #print(inst_name,inst_SN)
  # Allow Serial Number to match wildcard
  if inst_SN not in instruments[inst_model]:
    if 'Default' in instruments[inst_model]:
        inst_SN='Default'
    else:
        print('No serial # "{}" found for instrument "{}"'.format(
            inst_SN,inst_model))
        continue
  # Put instrument values in station
  station['instrument']['parameters']=instruments[inst_model][inst_SN]
  # Print result
  print('='*80)
  print('Station {}:'.format(name))
  pp.pprint(station)
  print('')