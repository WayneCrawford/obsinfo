TO DO
======================

`Questions/suggestions for information files`_

.. _Questions/suggestions for information files: QUESTIONS_infofiles.rst

Bugs
____________

- Crashes on empty or absent network.general_information.comments field

Major
____________

- Only allow "$ref" as oneOf choice at network (and instrumentation?) level(s)
- ?json-schema more levels? (one per "class") to allow more file validations
- make instrumentaion have "configuration" and "configuration_definition"
  (like instrument_components)
- move filter obspy creation to filter.py
- Put "file_fields" description in descriptions.schema.json
  - each schema file will open with 
'''
    allOf: [
        {$ref: "description.schema.json"},
        {
            "type": "object",
            "required": [ "response","format_version" ],
            "properties": {
                "format_version" : {"$ref" : "#/definitions/format_version"},
                "revision" :       {"$ref" : "definitions.schema.json#/revision"},
                "response" :       {"$ref" : "#/definitions/response" },
                "yaml_anchors" :   {"$ref" : "definitions.schema.json#/yaml_anchors"},
                "notes" :          {"$ref" : "definitions.schema.json#/note_list"},
                "extras" :         {"$ref" : "definitions.schema.json#/extras"}
            },
	        "additionalProperties" : false,
        }
    ]
'''

Allow user to specify complete instruments for a network
------------------------------------------------------------

 - Create  sample network files with gain configs entered
 - Create another with full instrument (but still around a base instrument
   that at least indicates the datalogger)

Make a ``obsinfo-example-dir`` console script
------------------------------------------------------------
Copies the obsinfo/obsinfo/_examples directory to a local directory
specified by the user

Minor
____________

- Network file:

    - Add ``bad_stations`` field at same level (and with same format) as
      ``stations``?  This would allow one correct specification of bad stations
      without the codes trying to make data from them.  But it would force the
      user to specify a start_date and end_date for data recovery statistics.
      
    - Change ``network.general_information.description`` to 
     ``network.general_information.name`` 
     
    - Change ``network:general_information`` to
      ``network:fdsn_network_information`` (or
      ``network:STATIONXML_network_information``, or 
      ``network:experiement_information``).  This field is used to generate
      STATIONXML network information in the absence of informations directly
      from FDSN.  Its current name implies that the information belongs to the
      campaign, but several campaigns could be part of the same
      experiment/FDSN_network.
      
- ?Put location code in instrumentation.yaml?
 
    - (allows proper specification of Hydroctopus, for example)
   
    - Should automatically verify that channel_locations in network.yaml
      correspond        
     
    - Or only require a location code in instrumentation.yaml if there are
      duplicate channel codes?

- Allow network file to specify orientation of each component (write test case
  to confirm)

- Add Response and Filter classes to instrument_components.py?

- Code

   * ``In obsinfo-make_process_scripts_*``, should ``--append`` imply
     ``--noheader`` ?

   * Flatten the directory structure:
     * Put instrumentation.py, instrument.py, instrument_components.py,
       instrument_component.py, network.py and station.py at top level
     * maybe put station in network.py, instrument in instrumentation.py
       and instrument_component in instrument_components.py?
     * will allow me to make a "test/" directory at this level
   
- Define and use a standard naming system for response files

- remove output_sample_rate from ``response:decimation_info`` (datalogger)
  It's already in ``instrument_components:datalogger:configurations`` (but need
  to be sure this value can be used to check the output sample rate.
  Alternatively, verify that output_sample_rate = sample_rate

  
- Make simpler network files in examples:

    - SPOBS_EXPT: one from MOMAR (SPOBS, HOCT and BUC location)
    - BBOBS_EXPT: one from PiLAB (BBOBS, acoustic survey and leap_second)
    - MANY_LOCS: showing many different location methods
    - HOCT_EXPT: showing an instrument with many of the same sensors
    - LEAPSECOND: with leapsecond
    - LANDSTATION: Showing full specification of each channels acquistion chain
    - CUSTOM-CONFIGS1: Show specification of gains
    - CUSTOM-CONFIGS2: Show specification of gains and sensors
    - OBSOLETE:  weird cases and obsolete instruments 
    
- State somewhere that a given instrument should have a fixed number of channels
  - Different configurations can change anything about the responses/components

Major Maybes
____________


Define a "field separation" character?
------------------------------------------------------------

Define a character to separate "fields" in filenames and keys within the information files?
For now, '_' is used both to separate words and fields, so it's not easy to see what is a "key"
and what is a "field".  '#' can't be used in the filenames because it has a specific
meaning in JSON Pointers.  '.' (as in SeisComp3 Data Structure) is not very visual
but might be the simplest and is already used for separating fields from their unit definition
(as with "embargo_period.a", "duration.s" and duration.m" in network files)
Examples (using '.') would include:

- Data logger configurations (in instrument_component files): INDENTIFIER.CONFIG, e.g.:

    - LC2000_LOGGER.62sps
    
    - LC2000_LOGGER.125sps
    
    - OPENSOURCE_LOGGER.100sps_zerophase
    
    - OPENSOURCE_LOGGER.100sps_minphase

    - OPENSOURCE_LOGGER.100sps_minphase_4x

- Response filenames: MAKE.MODEL.CONFIG.CALIBRATION.response.yaml, e.g.:

    - Scripps.LCPO2000-CS5321.62sps.theoretical.response.yaml)
    
    - Scripps.LCPO2000-CS5321.125sps.theoretical.response.yaml)
    
    - SIO-LDEO.DPG.generic.theoretical.response.yaml)
    
    - SIO-LDEO.DPG.5004.calibrated.response.yaml)
    
- Instruments (in instrumention files):  IDENTIFIER.CONFIG, e.g.:

    - BBOBS1.1
    
    - BBOBS1.2
    
          
Allow network.yaml files to specify instrument orientations
------------------------------------------------------------

Change campaign.OBS_facilities.facilty.stations
------------------------------------------------------------

to station_names? or station_codes?

Add naming participants in campaign files
------------------------------------------------------------

So that DOIs are properly informed.

Maybe to network files too, so that facilities indicate the right people (might also help with resolving information gaps).

QUESTIONS    
======================

- Should I change network/general_information to network/fdsn_information?

- Should we use UCUM for response unit names?:

    - "M"->"m", "S"->"s", "COUNTS"->"{counts}", "PA"->"Pa" (or "PAL")
    
    - "V" is already UCUM

Use `reStructuredText
<http://docutils.sourceforge.net/rst.html>`_ to modify this file.
