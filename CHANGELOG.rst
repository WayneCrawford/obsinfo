v0.107
-----
Huge amount of changes to implement full configuration.
Significant changes to and objectization of Python code.

- ``delay_correction`` moved from ``response:decimation_info``
  to ``instrument_components:configurations:{config}``

v0.106
------

- Moved ``sample_rate`` from ``network:`` to
  ``instrument_components:datalogger:{MODEL}:{CONFIG}``

- In ``network`` files:

  * Moved ``station_location`` to station level 
  * Changed ``instrument`` to ``instruments``: [list of 'instrument']
    (for OBSs, there will be only one element)
  * Added ``Comment`` in format station XML
  * Added ``start_time`` and ``end_time`` to ``channel``, if not given they
    take station dates
  * Added iris_unit list to ``input_unit`` and ``output_unit`` fields
  * 'Z' is no longer required at end of date fields 
  * Made ``processing`` field: list in ``network:stations:{STATION}``, moved
    clock corrections there
  * changed station positions and uncertainties from lists to objects with fields
    ``lat``, ``lon`` and ``elev``
  * changed ``network:facility_reference_name`` to ``network:facility``
    object with two fields: ``reference_name`` and ``full_name``
  
- In ``response`` files:

  * changed ``response:stage:filter:offset`` to 
    ``response:stage:filter:delay.samples``
  * added ``response:decimation_info:`` with following elements

    - ``input_sample_rate`` : ``numeric``
    - ``output_sample_rate`` : ``numeric``
    - ``delay_correction``: ``boolean`` or ``numeric``
    
      * if ``True``, set ``correction=delay`` for each stage
      * if ``False``, set ``correction=0`` for each stage
      * if ``numeric``, set ``correction=0`` for all but the last stage and 
        ``correction=delay_correction`` for the last stage

    - ``notes``: ``string``

- In code

  * delete automatic around_down/up_minutes in start/end_time station
  * added many tests
  * StationXML Inventory source is now ``network:facility:full_name`` (or
    ``revision:author`` if ``full_name`` not provided)

v0.106.1: moved tests to obspy style (inittests inside submodule directory) 

v0.105
------

Change all information file schemas to allow information files to specify either
the current format_version or the last one in which that information file type
was modified.

Changed ``network`` file (station level):

* Renamed ``location_code`` to ``instrument:station_location``
* Renamed ``instrument:channel_locations`` to ``instrument:channel_codes_locations``
* Removed ``supplements`` (use ``notes`` or ``comments``, depending on whether you want the information to appear
  in StationXML comments or not)
* Added ``extras`` (as in other information files/levels) for new/desired fields

Other

* 0.105.1: Added leap-second handling and simplified process-scripts (lc2ms completely, others partially)
* 0.105.2: Further simplified process-scripts
* 0.105.3: Added custom filename and file appending to make_process_scripts_*
* 0.105.4: Add combining SDS_corrected/ and SDS_uncorrected/ into SDS_combined/ to SDPCHAIN.py (pulled w/o complete verification)
* 0.105.5: Allow network.yaml to NOT specify an information file, rename ``obsinfo-make_process_scripts_*`` to ``obsinfo-make_*_scripts``
* 0.105.6: Fix a bug in SDPCHAIN leap_second correction (obsinfo.addons.SDPCHAIN.__leap_second_script, "leap_dir"=>"leap_time")
* 0.105.7: Some more corrections to addons.SDPCHAIN and addons.LCHEAPO (removes some inferred path dependecies)
* 0.105.8: Minor bugfixes
  
v0.104
------

Changed ``instrumentation`` and ``instrument_components`` files:

* Change all ``instrument-component/s`` to ``instrument_component/s`` ('-' to '_') 
  (because Python can't have '-' in a module name)
  
Other changes:

* 104.1: Added automatic check of information files against schema
* 104.2: Added console scripts to generate SDPCHAIN and LC2MS process-scripts
  
v0.103
------

* Added top-level ``response`` field to ``*.response.yaml`` (consistent with other information file types)
* Make ``instrument-components.yaml`` file have internal key instrument-components (not instrument_components)     
* changed top-level ``definitions`` keyword to ``yaml_anchors``
  
v0.102
------

Changes to all information files:

* Added ``extras`` field for all values that don't go into making FDSN-compatible data/metadata

Other changes:

* Start adding JSON validator
* Changed directory structure:

  * ``../data``: schema files and other things necessary for the code
  * ``../scripts``: scripts/codes that should directly callable by others
  * ``../exampes``:  Information files and example scripts
  
* Wrote scripts ``obs-validate`` and ``obs-print``

v0.101
------

* Added boolean variable ``delay_corrected`` to ``response:stages``
* CORRECTED BUG in constructing response stages
* Add module to create SDPCHAIN commands
* Put information and schema files in the distribution directory
* Allow ``linear_drift`` OR ``linear_drifts`` (list of linear_drift-types)
      
v0.100
------

* **Changed Python code to use Python package structure**
* Changed ``GeoJSON`` to ``GeoPos`` and ``GeoJSON_m`` to ``GeoUncert``
* Changed units in field names from name_units to name.units 
  (``uncertainties_m`` => ``uncertainties.m``)
* Standardized leap_second fields.
                            
v0.99
------

* Made all references to other files look like they can just be imported into that key
  (but obsinfo.py does not yet handle that: always treats them just as files)   
  
             
v0.98
------

**Numerous changes to remove repetition and concord more with StationXML and
JSON Pointer formats**

* all information files

  - Provide reference_name (for campaign and facility)
  - Use JSON Pointer format (like in JSON-Schema) for ALL external files 
    (e.g. $ref: "{filename}#{internal_path}" )
  - Many small nomenclature changes
  - Standardized top level: only ``notes``, ``format_version``, ``definitions`` and
    "TYPE" allowed, where TYPE is "network", "instrumentation", "campaign", etc.
    
     - Also move ``format_version`` and ``revision`` to base level
     
  - Much stricter about what is allowed as a key ("additionalProperties" : false)
  
* ``instrument-components`` files

  - Removed facility description (leave only in instrumentation.yaml)
  - Renamed "response_files" to "response_stages" and made a list (no more "sensor","ana_filt"...)
  - In datalogger, added delay_correction_samples (will be added to last response stage correction)
  
* ``campaign`` files

  - Removed "network" information (available from FDSN and in network.yaml)
  
    - now only provide "fdsn_network_code:"
    
* ``network`` files

  - "channel_locations" information are now provided individually (no more "channel_defaults")
  
* ``response`` files

  - renamed using '_' instead of '#' as the separator
  - renamed response.yaml to filter.yaml
  - replaced input_sampling interval by input_sample_rate
  - remove output_sampling_interval (calculate from input_sample_rate and decimation_factor)
  - removed "response:corrected" (belongs at stage:delay_correction level)
  - replaced "scaling_divisor" by "coefficient_divisor"
  
    - this value should be confirmed by summing coefficients
    - values passed on to stationXML should have this divisor applied

v0.97
------

*Changes based on discussion with OCA:*

- Add das connector and component to instrument definition
- Add standard dip and azimuth to sensor definitions
- Add configurations to sensor definitions
- Adding digital_filter_suffix??? (instead of sample_rate and variables)
- Adding manufacturer name at instrumentation_yaml level
- Adding config to sensor definition
- Make response "include" file paths based on calling file
    
v0.96
------

This is the first version that creates OCA JSON files. Also:

- Minor changes in structure of components file
- Change in file paths in response_stages file
- ``network`` file "model" field renamed to "reference_code"

v0.95
------

The first version that created valid StationXML (print_stationXML.py).  Also
had modifications to interface with OCA-GeoAzur.

- split the ``instrumentation`` file into ``instrumentation``, ``components_sensor``
  and ``components_datalogger`` files
- Added ``first_name`` and ``last_name`` to author fields
- Added ``network.description`` to ``campaign`` file 
- remove variables from ``instrument_components`` file (because GeoAzur can't use them)


v0.9
------

- ``instrumentation`` file allows complete specification of instruments and
  sensors (including serial-number specific variations)
- ``network`` file allows one to build an instrument by taking it's base
  configuration and changing the attached sensors.
- Added schemas (using JSON-SCHEMA)

v0.8
------

Allow complete specification of StationXML using network + instrumentation files

- ``network`` file changes: 

  - Add "FDSN_network" at "network:" level
  - Added "obs-specific" dictionary to stations, and collected all obs-specific 
    information:
    
    - ``clock_correction_linear``, ``time_base``, ``localization_method`` and
      ``clock_correction_leapsecond`` (NEW)
      
  - Went back to using official station name as station[key]
  - changed ``FDSN_name`` to ``original_name`` within station[key] dictionary
  
- ``campaign`` file changes: 

  - Renamed "FDSN_network" to "network" and simplified information (if it is
    an FDSN network, the complimentary information should be found through FDSN
    webservices)
    
- all information files:

  - Split up "version" into a "format_version" (for the file format) and
    "information_version" (for the information provided)
  - "format_version" is now a base-level element 
  
v0.7
------

Changes to ``instrumentation`` file

- Removed "datalogger" type, because there are already "digitizer" and 
  "digital filter" types that have no corresponding type in StationXML
  (so the "digitizer" and "digital filter" types should be combined
  in the StationXML "datalogger" type)

v0.6
------

- ``campaign`` file changes:

  - added "version:"
  - changed "name:" to "reference_name:"
  - Added ``description`` to ``FDSN_network``
  - changed information in "OBS_facilities:" (previously "OBS_providers:")
  
    - changed "email:" to "contact:"
    - eliminated "representative:", "chief_engineer:" (in NETWORK file)
    - added ``stations``
    
  - in ``data_sample``:
  
    - eliminated "ordering:" (automatically by distance if source_latitude
      and source_longitude provided, by station name otherwise)
      
- ``network`` file changes: 

  - Changed filename to ``{CAMPAIGN}.{FACILITY}.network.yaml``
    (Allows each facility to provide it's own stations' information)
  - Added ``instrumentation-file``
  - Removed ``network_info``
  - in ``stations``
  
    - changed key to be facility's station name
    - within each station:
    
          - added "FDSN_name:"
          - added "geology:", "vault:" and "site:"
            
- ``instrumentation`` file changes: 

  - Add "response_directory:" (absolute or relative pathname)
  - Serial numbers: changed default string from "Default" to "generic"
                
v0.5
------

``instrumentation`` file changes: 

- Add parameters allowing full specification of StationXML
  ``<Equipment>``, ``<Datalogger>``, ``<Preamplifier>`` and ``<Sensor>`` fields.
- Add "dip" and "azimuth" for each channel.
  - Made instances self-contained (at the expense of some streamlining).
