""" 
station object in network information file

"""
# Standard library modules
#import math as m
#import json
#import pprint
#import os.path
import sys

# Non-standard modules
import yaml
import obspy.core.util.obspy_types as obspy_types
import obspy.core.inventory        as obspy_inventory
import obspy.core.inventory.util   as obspy_util
from   obspy.core.utcdatetime  import UTCDateTime

from ..misc            import misc       as oi_misc
from ..misc            import obspy      as oi_obspy
from ..misc.misc       import round_down_minute, round_up_minute, make_channel_code
from ..instrumentation import instrument as oi_instrument

################################################################################       
class station:
    """a station from the network information file"""           
    def __init__(self,station_dict,station_code,network_code,debug=False):
        """ station_dict is straight out of the network information file"""
        self.comments=station_dict.get('comments',[])
        self.site=station_dict['site']
        self.start_date=station_dict['start_date']
        self.end_date=station_dict['end_date']
        # self.location_code=station_dict['location_code']
        self.instruments=station_dict['instrument'] if type(station_dict['instrument']) is list else [station_dict['instrument']]
        self.station_location=station_dict['station_location']
        self.locations=station_dict['locations']
        self.clock_corrections=station_dict.get('clock_corrections',[])
        self.supplements=station_dict.get('supplements',[])
        self.code=station_code
        self.network_code=network_code
        if 'sensors' in station_dict:
            self.sensors=station_dict['sensors']
        else:
            self.sensors=None
    def __repr__(self) :
        txt =       "< {}: code={}, ".format(__name__,self.code)
        if hasattr(self.instrument,'das_components'):
            txt = txt+ 'instrument={} >'.format(self.instrument)
        else:
            #print(self.instrument)
            txt = txt + "instrument= ['{}','{}']".format(
                        self.instrument['reference_code'],
                        self.instrument['serial_number'])
        return txt
    def fill_instrument(self,instrument_file,referring_file=None,debug=False):
        """ Fills in instrument information """
        self.partial_fill_instrument(instrument_file,referring_file)
        if debug:
            print(yaml.dump(self.instrument.das_components))
        
        if self.sensors:
            print("Adding custom sensors")
            self.instrument.modify_sensors(self.sensors,referring_file)
            if debug:
                print(self.sensors)
        for key in self.instruments.keys():
            self.instruments[key].fill_responses()
        if debug:
            print(self.instrument.das_components)
        
    def partial_fill_instrument(self,instrument_file,referring_file=None,debug=False):
        """ Fills in instrument information, but without specific component information """
        instruments = {}
        for instrument in self.instruments:
            reference_code = instrument['reference_code']
            instruments[reference_code] = oi_instrument(instrument_file['$ref'],
                                instrument,
                                referring_file=referring_file)
            #self.__verify_revision_date(instrument_file['revision_date'])
            if debug:
                print("INSTRUMENT DAS COMPONENTS: PRE-LOAD")
                print(yaml.dump(self.instrument.das_components))
            instruments[reference_code].load_components(instruments[reference_code].components_file,instruments[reference_code].basepath)
            if debug:
                print("INSTRUMENT DAS COMPONENTS: POST-LOAD")
                print(yaml.dump(self.instrument.das_components))
            self.operator=instruments[reference_code].facility # à verifier??
            if debug:
                print("INSTRUMENT : POST-LOAD")
                print(yaml.dump(self))
        self.instruments = instruments
#     def __verify_revision_date(self,reference_revision_date):
#         if not self.instrument.revision['date'] == reference_revision_date :
#             print('ERROR!: instrument file revision date is not that specified in network file')
#             sys.exit(1)
            
    def make_obspy_station(self,debug=False):
        """
        Create an obspy station object from a fully informed station
        """
        # CREATE CHANNELS

        #if debug:
        #    print(self)
        channels=[]
        for instrument in self.instruments.values():
            resource_id=instrument.resource_id
            for key,chan in instrument.das_components.items():
                if debug:
                    print(key)
                    print(yaml.dump(chan))
                print(chan)
                response=oi_obspy.response(chan['response'])
                #loc_code=key.split(':')[1]
                loc_code=chan['location_code']
                try:
                    location = self.locations[loc_code]
                except:
                    print(f'location code {loc_code} not found in self.locations, valid keys are:');
                    for key in self.locations.keys():
                        print(key)
                    sys.exit(2)
                obspy_lon,obspy_lat = oi_obspy.lon_lats(location)
                azimuth,dip=oi_misc.get_azimuth_dip(
                                            chan['sensor'].seed_codes,
                                            chan['orientation_code'])
                start_date=None
                end_date=None
                # Give at least 3 seconds margin around start and end dates


                if  'start_date' in chan:
                    start_date = UTCDateTime(chan['start_date'])
                elif hasattr(self,'start_date'):
                    if self.start_date:
                        try:
                            start_date=round_down_minute(UTCDateTime(self.start_date),3)
                        except:
                            print(f"There is a problem with the station start date: {self.start_date}")
                            sys.exit(2)
                if 'end_date' in chan:
                    end_date = UTCDateTime(chan['end_date'])
                elif hasattr(self,'end_date'):
                    if self.end_date:
                        #print(self.end_date)
                        #print(UTCDateTime(self.end_date))
                        try:
                            end_date=round_up_minute(UTCDateTime(self.end_date),3)
                        except:
                            print(f"There is a problem with the station end date: {self.end_date}")
                            sys.exit(2)
                if debug:
                    print(key)
                    print(yaml.dump(chan))
                #print(location)
                if 'localisation_method' in location:
                    channel_comment=obspy_util.Comment('Localised using : {}'.format(
                            location['localisation_method']))
                else:
                    channel_comment = None
                channel_code=make_channel_code(chan['sensor'].seed_codes,
                                                chan['band_code'],
                                                chan['inst_code'],
                                                chan['orientation_code'],
                                                chan['sample_rate'])
                channel = obspy_inventory.channel.Channel(
                        code = channel_code,
                        location_code  = loc_code,
                        latitude  = obspy_lat,
                        longitude = obspy_lon,
                        elevation = obspy_types.FloatWithUncertaintiesAndUnit(
                                            location['position'][2],
                                            lower_uncertainty=location['uncertainties.m'][2],
                                            upper_uncertainty=location['uncertainties.m'][2]),
                        depth     = location['depth.m'],
                        azimuth   = obspy_types.FloatWithUncertainties(
                                            azimuth[0],
                                            lower_uncertainty=azimuth[1] if len(azimuth) is 2 else 0,
                                            upper_uncertainty=azimuth[1] if len(azimuth) is 2 else 0),
                        dip       = dip[0],
                        types      =['CONTINUOUS','GEOPHYSICAL'],
                        sample_rate=chan['sample_rate'], 
                        clock_drift_in_seconds_per_sample=1/(1e8*float(chan['sample_rate'])),
                        sensor     =oi_obspy.equipment(chan['sensor'].equipment),
                        pre_amplifier=oi_obspy.equipment(chan['preamplifier'].equipment) if 'preamplifier' in chan else None ,
                        data_logger=oi_obspy.equipment(chan['datalogger'].equipment),
                        equipment  =None,
                        response   =response,
                        description=None,
                        comments=[channel_comment] if channel_comment else None,
                        start_date = start_date ,
                        end_date   = end_date,
                        restricted_status = None,
                        alternate_code=None,
                        data_availability=None
                    )
                channels.append(channel)
                if debug:
                    print(yaml.dump(channel))
            # CREATE STATION
            station_loc_code=self.station_location # david
            if station_loc_code in self.locations:
                sta_loc=self.locations[station_loc_code]
                obspy_lon,obspy_lat = oi_obspy.lon_lats(sta_loc)
            else:
                print ("No valid location code for station, either set station_location_code or provide a location '00'")
                sys.exit()
            
            obspy_comments = oi_obspy.comments(
                            self.comments,
                            self.clock_corrections,
                            self.supplements,
                            station_loc_code,
                            sta_loc
                        )
            # DEFINE Operator
            agency=self.operator['full_name']
            contacts=None
            if 'email' in self.operator:
                contacts=[obspy_util.Person(emails=[self.operator['email']])]
            website=self.operator.get('website',None)
            operator = obspy_util.Operator([agency],contacts,website)
        
            if debug:
                print(obspy_comments)
            sta=obspy_inventory.station.Station(
                        code      = self.code,
                        latitude  = obspy_lat,
                        longitude = obspy_lon,
                        elevation = obspy_types.FloatWithUncertaintiesAndUnit(
                                            sta_loc['position'][2],
                                            lower_uncertainty=sta_loc['uncertainties.m'][2],
                                            upper_uncertainty=sta_loc['uncertainties.m'][2]),
                        channels = channels,
                        site     = obspy_util.Site(getattr(self,'site','')),
                        vault    = sta_loc['vault'],
                        geology  = sta_loc['geology'],
                        equipments= [oi_obspy.equipment(instrument.equipment) for instrument in self.instruments.values()],
                        operators=[operator],
                        creation_date=start_date,   # Necessary for obspy to write StationXML
                        termination_date=end_date,
                        description=None,
                        comments = obspy_comments,
                        start_date = UTCDateTime(self.start_date),
                        end_date   = UTCDateTime(self.end_date),
                        restricted_status = None,
                        alternate_code=None,
                        data_availability=None,
                    )
        if debug:
            print(sta)
        return sta

    def cast_date(self,date):
        try:
            
            date_date=round_down_minute(UTCDateTime(date),3)
        except:
            print(f"There is a problem with the station start or end date: {date}")
            sys.exit(2)    
        return  date_date  