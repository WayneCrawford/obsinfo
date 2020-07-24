This directory contains sample information files in two directories:

* the ``/campaigns`` directory, which has subdirectories for each data collection
  campaign. Each subdirectory contains: 
  
  * ``{CAMPAIGN}.{FACILITY}.network.yaml``: to be filled in by the OBS facility operator
  * ``{CAMPAIGN}.campaign.yaml``: to be filled in by the chief scientist
  
* the ``/instrumentation`` directory, which contains subdirectories to be filled in by the facility operator.
  Each subdirectory corresponds to a facilty update and contains:
  
  * ``instrumentation.yaml``: An inventory of park instruments.  Refers to ``instrument_components`` file (in
    principal, could also refer to RESP or other standard files, although this has not been implemented in the
    code
  * ``instrument_components.yaml``: An inventory of instrumentation components used in the ``instrumentation``.
  * a ``/responses`` directory containing individual sensor, datalogger and filter stages
  
* a ``/project`` directory, which is just a test of a possible project-level (multiple campaigns) file

The information files can be in YAML or JSON format.


