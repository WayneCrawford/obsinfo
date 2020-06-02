*******************
Information files
*******************

Basic principals
===================================

- Files, in JSON or YAML format, provide a hierearchy of objects, from Network to Filter, 
  that allow the user to fully specify seismological network stations based on their
  components and configurations. 
  
- Most objects correspond to StationXML elements, but there are also objects to
  specify processing steps and to configure the instrumentation.

- Filenames are {*specific element*}.{*object*}.{yaml,json}.

- The base level of each file contains provenance information: 

  - ``format_version`` (REQUIRED): version of the information file format
  - ``revision`` (REQUIRED): Who made the file and when
  - ``yaml_anchors`` (optional):  Used to define YAML anchors (groups
    of objects that can be inserted elsewhere, reducing redundancy/errors)
    
  plus the type-specific object:
  
  - {*object*}: same as in the filename

- Any object can have the fields:

  - ``notes``: Notes that will not be put into the StationXML file.
  - ``extras``: Fields that don't exist in the definition.

Files refer to other files "downstream" using
  `JSON Pointers <https://tools.ietf.org/html/rfc6901>`_ syntax ("``$ref:``"), which we
  have expanded to also work on YAML files. [#]_
  
.. [#] A ``$config:`` key could allow the code to evaluate some of the
  ``config`` and ``serial_number`` information before reading the
  referenced file, which could reduce the amount of information to read.
  Is it worth the added complexity?

Configuration
===================================
Stations can be configured using objects that duplicate the object they
will modify, but containing only the fields to be modified.  The
configurations can be specified directly at the station level, or they can
be pre-defined in the instrumentation or instrument_component 
using ``Configuration Definitions``, which can then be referenced at the
station level.

1) **Configuration Definitions**: specify possible configurations:
   
   - ``serial_number_definitions``: (differences between individual elements)
   - ``config_definitions``: (options for a given element)
  
2) **Configuration Choices**: choose the configuration
   to use at a given station and/or instrumentation:

   - ``serial_number`` implements the corresponding ``serial_number_definition``
   - ``config`` implements the corresponding ``config_definition``
   - direct configuration
   
``serial_number`` also sets the corresponding ``equipment:serial_number``
field.  Direct configuration overwrites any duplicated fields in ``config``,
 which overwrites any duplicated fields in ``serial_number``.
It is an error to specify a ``config`` with no corresponding
``config_definition``, but it is ok to specify a ``serial_number`` with no
corresponding ``serial_number_definition`` (it will simply set the
``equipment:serial_number`` field).

As an example of how an object can modify an existing object, here is
a (simplied) Datalogger specification.

If the file LC2000.datalogger.yaml#datalogger contains::

   datalogger:
        equipment:
            model: "CS5321/22"
            description: "CS5321/22 delta-sigma A/D converter + FIR digital filter"
        note: "I like to write things down"
        sample_rate: 125
        config_definitions:
            "125sps":
                equipment:
                    description: "CS5321/22 delta-sigma A/D converter + FIR digital filter [config=125sps]"
                sample_rate: 125
            "500sps":
                equipment:
                    description: "Crazy 500sps config"
                sample_rate: 500
    
and is instantiated as::
    
        base: $ref: "LC2000.datalogger.yaml#datalogger"
        config: "500sps"

the result would be::

        equipment:
            model: "CS5321/22"
            description: "Crazy 500sps config"
        note: "I like to write things down"
        sample_rate: 500
    
Most Configuration Choices are made in the ``Network`` file,
but `Instrument Component Configuration`_ Choices can also be made
in the ``Instrumentation`` file (for example, to set the default
preamplifier gain for a given instrumentation).  Choices made
"higher up" will override any conflicting Choices "lower down".
For example, a Choice made in an ``Instrumentation Configuration``_
object have precedence over those given in the corresponding
``Instrumentation``_ object)


Objects
===================================
A chain of objects is needed to fully specify a station and its processing.
All of the objects can be in one file, but they are usually divided into
different files for clarity, portability, and to avoid repetition (DRY).
Typical file levels are Network, Instrumentation, Instrument Components
(Sensors, Dataloggers and Preamplifiers), Responses and Filters.

--------------------------------------------------------------------------------

Network
***************************************

Specify the stations deployed by an OBS facility during an experiment.  Fields
are:

:``facility``: Basic information about the OBS facility.  ``ref_name`` should
    match the second field in the filename.  ``full_name`` will be
    put in the StationXML file
  
:``campaign_ref_name``: Should match the ``reference_name`` field in the
    Campaign file
   
:``network_info``: FDSN network information.  If you have declared a network
    with FDSN, the contents of these fields should match the
    values on the FDSN website
   
:``stations``: descriptions of each station.  Subfields are objects with key = 
    {``STATION_NAME``} and value = `Station`_ object.

--------------------------------------------------------------------------------

Station
***************************************

Description of one station.
  
:``site``: StationXML "site" field
  
:``start_date``: StationXML station ``start_date`` field.  Also used for
    channels if they are not separately entered
    
:``end_date``: StationXML station ``end_date`` field.
  
:``location_code``: Station location code.  Will also be used for
    channels if they are not separately entered.

:``locations``: descriptions of each location code:  fields are the same
    as in StationXML except ``uncertainties.m`` (all values are in
    meters) and ``localisation_method`` (description of how the
    location was determined)
    
:``processing``: Provenance information about how the data was transformed from
    raw to the final version.  There is no corresponds field in
    StationXML, so subfields are saved as StationXML comments
    
:``extras``: Subfields are saved to StationXML comments.

:``instruments``: List of `Instrumentation Configuration`_ s making up the
   station   

--------------------------------------------------------------------------------

Instrumentation Configuration
*********************************
A configured `Instrumentation`_ object

In the list below, later fields can modify earlier ones
    
:``base``: An `Instrumentation`_ object

Configuration Choice Fields (all optional)
-------------------------------------------------

:``serial_number``: Specify the `Instrumentation`_  serial number (and
    ``serial_number_definition`` if it exists)
              
:``config``: Specify the `Instrumentation`_ ``config_definition``
  
:``datalogger_config``: Specify the `Datalogger`_ ``config_definition``
    for all channels (shortcut for
    ``channel_mods: {base: {datalogger: config}}``

:``datalogger_serial_number``: Specify the `Datalogger`_ ``serial_number`` (and
    ``serial_number_definition`` if it exists).  Shortcut for
    ``channel_mods: {base: {datalogger: serial_number}}``

:``sensor_config``: Shortcut for
    ``channel_mods: {base: {sensor: config}}``

:``sensor_serial_number``: Shortcut for
    ``channel_mods: {base: {sensor: serial_number}}``

:``preamplifier_config``: Shortcut for
    ``channel_mods: {base: {preamplifier: config}}``

:``preamplifier_serial_number``: Shortcut for
    ``channel_mods: {base: {preamplifier: serial_number}}``

:``channel_mods``: Specify `Channel`_ configurations.
                
    :``base``: `Channel Configuration`_ applied to all channels.
    
    :``by_orientation``/{ORIENTATION-CODE}: `Channel Configuration`_ applied to
      individual channels, keyed by their SEED orientation code
  
    :``by_das``/{DAS-CODE}: `Channel Configuration`_ applied to individual channels,
      keyed by their data acquisition system (DAS) code.
      Use when a station has more than one channel with the same
      orientation code.

    :``by_chan_loc``/{CHAN_LOC}: `Channel Configuration`_ applied to individual
      channels, keyed by their channel and location codes.
      Alternative to ``by_das``, when it's easier/clearer to write out
      channel_location codes

--------------------------------------------------------------------------------

Channel Configuration
*********************************
Specify `Channel`_ modificiations and deployment-specific information

:``sensor``: Modifications to Sensor (see `Instrument Component Configuration`_)

:``datalogger``: Modifications to Datalogger (see `Instrument Component Configuration`_)

:``preamplifier``: Modifications to Preamplifier (see `Instrument Component Configuration`_)

:``location_code``: Channel's location code
              
:``start_date``: Channel start date (if different from station)

:``end_date``: channel end date (if different from station)
              

--------------------------------------------------------------------------------

Instrument Component Configuration
***************************************
Specify `Instrument Component`_ modifications

:``base``: Full Instrument Component description (see `Instrument Component`_)

Configuration Choice Fields
-------------------------------------------------

:``config``: Activate `Instrument Component`_-level
    ``configuration_definition``
  
:``serial_number``: Specify Instrument Component serial number and apply
    corresponding ``serial_number_definitions``, if they exist
              

--------------------------------------------------------------------------------

Instrumentation
***************************************

Specify a scientfic instrument (OBS, field station), as equipment and channels

Fields are:

:``facility``: (optional) information about the facility managing this
               instrumentation

:``equipment``: Corresponds to StationXML Equipment object
  
:``base_channel``: (optional) A `Channel`_ object.
                 Simplifies specifying ``das_channels`` (below) if
                 the same datalogger|preamplifier|sensor is used on more than
                 one channel.  Choose the most common instrumentation channel
                 (for example, many seismometers have the same sensor
                 description on three channels).  The "``orientation_code``"
                 subfield is ignored.
:``das_channels``: A possibly incomplete `Channel`_ object.  Values provided
                 replace those in ``base_channel``

Configuration Definition Fields
-------------------------------------------------

Modifications to the above-mentioned fields.

:``config_definitions``: optional configurations 
      
:``serial_number_definitions``: serial number based modifications
   

--------------------------------------------------------------------------------

Channel
***************************************

Specify an Instrumentation Channel (Instrument Components and an
orientation code). `Response`_ objects for each Instrument component are stacked
from sensor (top) to datalogger (bottom)

Fields: 
-------------------------------------------------
:``sensor``:  Sensor Instrument_Component

:``preamplifier``: (optional) Preamplifier Instrument_Component

:``datalogger``: Datalogger Instrument_Component

:``preamlifier_config``: (optional) preamplifier configuration code

:``sensor_config``: (optional) sensor configuration code

:``datalogger_config``: (optional) datalogger configuration code

:``orientation_code``: SEED orientation code.

:``location_code``: Channel location code, if different from station
                    location code
                    
:``datalogger_modifs``: Modifications to the ``datalogger``: an object
                        with the same structure as the ``datalogger``
                        object, but only the values to change 
                        specified (not validated by schema)

:``sensor_modifs``: Modifications to the ``sensor``: as above

:``preamplifier_modifs``: Modifications to the ``preamplifier``: as above

--------------------------------------------------------------------------------

Instrument Component
***************************************

Specify an Instrument Component: ``sensor``, ``preamplifier`` or ``datalogger``.

Shared fields:
-------------------------------------------------

:``equipment``: Corresponds to StationXML Equipment object
  
:``config_description``: Description of the default configuration.  Can be left
                       empty if there is only one configuration.

:``responses_ordered``: an ordered list of responses (see `Response`_)

Configuration Definition Fields
-------------------------------------------------

modifications to the above-mentioned fields (plus any specific to the given
Instrument Component type).
    
:``serial_number_definitions``: serial-number based modifications

:``config_definitions``: optional configurations 


Component-specific Fields: 
-------------------------------------------------

Datalogger
---------------------

:``sample_rate``: samples per second

:``delay_correction``: time correction applied to data to compensate FIR delay:

    :numeric: seconds delay to specify in last stage (for software correction
              of delay)
    :``True``: specify a correction in each stage corresponding to the specified
           delay in that stage
    :``False``: No correction will be specified (same as numeric = 0)

Sensor
---------------------

:``seed_codes``: SEED codes to give to channels using this sensor

    :``band_base``: Base SEED band code: "B" for broadband, "S" for short
                  period: obsinfo will determine the sample-rate-dependent band
                  codes to use for a given acquisition channel.
    :``instrument``: SEED instrument code
    :``orientation``: SEED orientation codes that can be associated with this
                    sensor. Each code is a key for an object containing:

                    :``azimuth.deg``: 2-element array of [value, uncertainty]
                    :``dip.deg``: 2-element array of [value, uncertainty]

Preamplifier
---------------------
None
 
--------------------------------------------------------------------------------

Response
***************************************

:``stages``: List of response stages, most sub-elements are StationXML fields

    :``description``: string
    
    :``name``: string [``None``]

    :`input_units``: object with fields ``name`` and ``description``
    
    :``output_units``: object with fields ``name`` and ``description``
    
    :``gain``: object with fields ``value`` and ``frequency``
    
    :``decimation_factor``: factor by which this stage decimates data [1]
    
    :``output_sample_rate``: output sample rate [sps]
    
    :``delay``: Delay in seconds of the stage [0]
    
    :``calibration_date``: date of calibration that gave this response [`None`]
    
    :``filter``: `Filter`_ object

--------------------------------------------------------------------------------

Filter
***************************************

Description of a filter.  Keys depend on the ``type``

Common fields:
-------------------------------------------------

:``type``: "``PolesZeros``", "``Coefficients``", "``ResponseList``",
         "``FIR``", "``ANALOG``", "``DIGITAL``" or "``AD_CONVERSION``"

`PolesZeros`-specific fields:
-------------------------------------------------

:``units``: string (only ``rad/s`` has been verified)

:``poles``: List of poles in the above units.  Each elements is a 2-element array
          containing the real and imaginary parts

:``zeros``:  List of zeros, specified as above

:``normalization_frequency``: As in StationXML

:``normatlization_factor``: As in StationXML


`FIR`-specific fields:
-------------------------------------------------

:``symmetry``: ``ODD``, ``EVEN`` or ``NONE``

:``delay.samples``: samples delay for this FIR stage

:``coefficients``: list of FIR coefficients

:``coefficient_divisor``: Value to divide coefficients by to obtain equal energy
                        in the input and the output


`Coefficients`-specific fields:
-------------------------------------------------

:``transfer_function_type``: "``ANALOG (RADIANS/SECOND)``", "``ANALOG (HERTZ)``", or
                           "``DIGITAL``"

:``numerator_coefficients``: list

:``denominator_coefficients``: list


`ResponseList`-specific fields:
-------------------------------------------------

List of [frequency (Hz), amplitude, phase (degrees)] lists


`ANALOG`-specific fields:
-------------------------------------------------

None.  Becomes a StationXML `PolesZeros` stage without poles or zeros,
``normalization_freq`` = 0 and ``normalization_factor`` = 1.0


`DIGITAL`-specific fields:
-------------------------------------------------

None.  Becomes a StationXML `Coefficients` stage with 
``numerator = [1.0]`` and ``denominator = []``


`AD_CONVERSION`-specific fields:
-------------------------------------------------

:``input_full_scale``: full scale value (volts)

:``output_full scale``: full scale value (counts)

Behaves the same as `DIGITAL`, the fields are for information only.


--------------------------------------------------------------------------------

Processing
***************************************
Steps used in processing data (Provenance metadata).  
NO STATIONXML EQUIVALENT, values are saved in StationXML comments

:``clock_correct_linear drift``: correction for a linear drift.  Values are:

    :``time_base``: string describing the instrument's onboard time base 
    :``reference``: string describing the time reference used for synchronization
    :``start_sync_reference``: time of start sync, viewed on reference clock
    :``start_sync_instrument``: time of start sync, viewed on instrument clock
                              (can be '0' if same as ``start_sync_reference``)
    :``end_sync_reference``: time of end sync, viewed on reference clock
    :``end_sync_instrument``: time of end sync, viewed on instrument clock

:``clock_correct_leapsecond``: correction for leapsecond(s).  Values are:

    :``time``: Time of the leap second
    :``type``: '+' or '-'
    :``description``: "Positive leapsecond (a 61-second minute)" or
        "Negative leapsecond (a 59-second minute)"
    :``corrected_in_end_sync``: is the provided end_sync_instrument corrected
        for this leapsecond?
    :``corrected_in_data``: were the OBS output data automatically/previously
                            corrected for this leapsecond?
