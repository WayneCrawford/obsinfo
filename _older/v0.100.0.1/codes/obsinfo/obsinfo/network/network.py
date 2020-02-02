""" 
Print complete stations from information in network.yaml file

nomenclature:
    A "measurement instrument" is a means of recording one physical parameter,
        from sensor through dac
    An "instrument" is composed of one or more measurement instruments
    
    version 0.100.0.1
    
I need to modify the code so that it treats a $ref as a placeholder for the associated object
"""
# Standard library modules
#import math as m
#import json
#import pprint
import os.path
#import sys

# Non-standard modules
#import yaml
#import obspy.core.util.obspy_types as obspy_types
import obspy.core.inventory as obspy_inventory
import obspy.core.inventory.util as obspy_util
from obspy.core.utcdatetime import UTCDateTime

from ..misc.misc import root_symbol, load_yaml
from ..misc import FDSN  as oi_FDSN
from .station import station as oi_station

################################################################################       
    
class network:
    """ Everything contained in a network.yaml file
    
        Has two subclasses:
            stations (.station)
            network_info (..misc.network_info)
    """
    def __init__(self,filename,referring_file=None,debug=False):
        """ Reads from a network.yaml file 
        
        should also be able to specify whether or not it has read its sub_file
        """
        root,path = load_yaml(filename+root_symbol,referring_file) 
        self.basepath =             path
        self.revision =             root['revision'].copy()
        self.format_version =       root['format_version']
        self.facility =             root['network']['facility_reference_name']
        self.campaign =             root['network']['campaign_reference_name']
        self.network_info = oi_FDSN.network_info(root['network']['general_information'])
        self.instrumentation_file = root['network']['instrumentation']
        self.stations=dict()
        for key,station in root['network']['stations'].items():
            self.stations[key]=oi_station(station, key, self.network_info.code)
            if debug:
                print(self.stations[key])
                
    def __repr__(self) :
#        return "<obsinfo.network: code={}, facility={}, campaign={}, {:d} stations>".format(
#                self.network_info.code,self.facility,self.campaign, len(self.stations))
        return "<{}: code={}, facility={}, campaign={}, {:d} stations>".format(
                __name__,
                self.network_info.code,
                self.facility,
                self.campaign, 
                len(self.stations))
                
    def __make_obspy_inventory(self,stations=None,source=None,debug=False):
        """
        Make an obspy inventory object with a subset of stations
        
        stations = list of obs-info.OBS-Station objects
        source  =  value to put in inventory.source
        """
        my_net=self.__make_obspy_network(stations)
        if not source:
            source = self.revision['author']['first_name'] + ' ' + self.revision['author']['last_name']
        my_inv = obspy_inventory.inventory.Inventory([my_net],source)
        return my_inv
        
    def __make_obspy_network(self,stations,debug=False):
        """Make an obspy network object with a subset of stations"""
        obspy_stations=[]    
        for station in stations:
            obspy_stations.append(station.make_obspy_station())
    
        temp=self.network_info.comments
        if temp:
            comments=[]
            for comment in temp:
                comments.append(obspy_util.Comment(comment))
        my_net = obspy_inventory.network.Network(
                            self.network_info.code,
                            obspy_stations,
                            description = self.network_info.description,
                            comments =    comments,
                            start_date =  self.network_info.start_date,
                            end_date   =  self.network_info.end_date
                        )
        return my_net
    
    def write_stationXML(self,station_name,destination_folder=None,debug=False):
        station=self.stations[station_name]    
        if debug:
            print("Loading and filling station")    
        station.fill_instrument(self.instrumentation_file,
                                referring_file=self.basepath)    
        if debug:
            print("Creating obsPy inventory object")    
        my_inv= self.__make_obspy_inventory([station],'INSU-IPGP OBS Park')
        if debug:
            print(yaml.dump(my_inv))
        fname=os.path.join(destination_folder,
                        '{}.{}.STATION.xml'.format(\
                                    self.network_info.code,
                                    station_name))
        print("Writing to", fname)    
        my_inv.write(fname,'STATIONXML')
    
    def write_station_XMLs(self,destination_folder=None):
        for station in self.stations:
            self.write_station(destination_folder)
