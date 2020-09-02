"""
Create OCA-JSON object from obs-info network
"""
import obsinfo
import json


class network:
    """OCA network description format

    Now that the instrument_components no longer name the response_stages
    but give a list instead, will have to deduce the OCA-compatible terms:
        - In Sensor: first item is sensor, any other are ana_filts
        - In Preamplifier: any items are ana_filts
        - In Datalogger: last item is digital_filter, second to last is
            digitizer, any prior are ana_filts
    """

    def __init__(self, obs_network, debug=False):
        """
        Create an OCA network object

        Contains stations without component details
        """
        for station_code, station in obs_network.stations.items():
            if debug:
                print(station_code)
                print("A:", station.comments)
            station.partial_fill_instrument(
                obs_network.instrumentation_file,
                referring_file=obs_network.basepath)
            if debug:
                print("B:", station.comments)
            # self.stations[station_code]=station
        if debug:
            for key, station in obs_network.stations.items():
                print(station.comments)

        if debug:
            for key, station in obs_network.stations.items():
                print("B-Ca:", key, station.comments)
        self.dict = dict()
        self.__make_network_header(obs_network)
        self.__make_authors(obs_network)

        if debug:
            for key, station in obs_network.stations.items():
                print("B-Cb:", key, station.comments)
        self.dict["stations"] = []
        for key, station in obs_network.stations.items():
            if debug:
                print("C:", key, station.comments)
            oca_station = self.__make_station_header(station)
            # oca_station={"open_date":'duh',"close_date":'der'}
            oca_station = self.__make_devices_and_channels(
                oca_station, station.instrument.das_components
            )
            self.dict["stations"].append(oca_station)

    #     def dict(self,debug=False):
    #         """Make an oca JSON string """
    #         return self.dict

    def __repr__(self):
        return "<OCA_Network: fdsn_code={}>".format(
            self.dict["network"]["fdsn_code"])

    def __make_network_header(self, obs_network):
        netinfo = obs_network.network_info
        # Forces authorship of comments to network.yaml revision author
        for comment in netinfo.comments:
            comments = {"value": comment, "authors": ["auth1"]}
        self.dict["network"] = {
            "fdsn_code": netinfo.code,
            "temporary": True,
            "open_date": netinfo.start_date.isoformat(),
            "close_date": netinfo.end_date.isoformat(),
            "description": netinfo.description,
            "comments": comments,
        }

    def __make_authors(self, obs_network):
        """ Fills in author(s) information"""
        self.dict["comment_authors"] = dict()
        i = 0
        for author in obs_network.revision["authors"]:
            i = i + 1
            phones = list()
            if "phones" in author:
                for phone in author["phones"]:
                    phones.append({"phone_number": phone}),
            au_dict = {
                "firstname": author["first_name"],
                "lastname": author["last_name"],
                "emails": [author.get("email", "")],
                "phones": phones,
            }
            self.dict["comment_authors"]["auth" + str(i)] = au_dict

    def __make_station_header(self, obs_station, debug=False):
        """ Makes OCA STATION HEADER
        returns station dictionary
         """
        oca_station = dict()
        if debug:
            print("comments=", obs_station.comments)
            print("nClock_corrections=", len(obs_station.clock_corrections))
            print("nSupplements=", len(obs_station.supplements))
        oca_comments = [x for x in obs_station.comments]
        if obs_station.supplements:
            for key, value in obs_station.supplements.items():
                if debug:
                    print(key)
                oca_comments.append(
                    json.dumps({key: value}).replace('"', "'"))
        if obs_station.clock_corrections:
            for key, value in obs_station.clock_corrections.items():
                if debug:
                    print(key)
                oca_comments.append(
                    json.dumps({key: value}).replace('"', "'"))
        if debug:
            print("----")

        sta_position = obs_station.locations[obs_station.location_code][
                                             "position"]
        oca_station = {
            "IR_code": obs_station.code,
            "site": obs_station.site,
            "comments": oca_comments,
            "open_date": obs_station.start_date,
            "close_date": obs_station.end_date,
            "longitude": sta_position[0],
            "latitude": sta_position[1],
            "altitude": sta_position[2],
            "altitude_unit": "m",
            "first_install": obs_station.start_date,
        }
        return oca_station

    def __make_devices_and_channels(self, oca_station, das_components):

        oca_station["channels"] = list()
        devices = dict()
        for das_code, values in das_components.items():
            devices, device_codes = self.__add_devices(devices, values)
            ###
            ch = self.__make_channel(
                das_code,
                device_codes,
                values,
                oca_station["open_date"],
                oca_station["close_date"],
            )
            oca_station["channels"].append(ch)
        oca_station["installed_devices"] = devices
        return oca_station

    def __add_devices(self, devices, values, debug=False):
        """
        Find devices or add to dictionary of "installed devices"

        devices= existing dictionary of devices
        values = values corresponding to this das_component
        """
        codes = dict()
        if debug:
            print("===", values)

        sensor = self.__make_devicedict("sensor", values["sensor"].equipment)
        azimuth, dip = obsinfo.get_azimuth_dip(
            values["sensor"].seed_codes, values["orientation_code"]
        )
        sensor["azimuth_error"] = azimuth[1]
        sensor["dip_error"] = dip[1]
        sensor["local_depth"] = 0
        sensor["vault"] = "seafloor"
        sensor["config"] = "single"
        devices, codes["sensor"] = self.__find_append_device(devices, sensor,
                                                             "sensor")

        anafilter = self.__make_devicedict(
            "anafilter", values["preamplifier"].equipment)
        devices, codes["anafilter"] = self.__find_append_device(
            devices, anafilter, "anafilter")

        das = self.__make_devicedict("das", values["datalogger"].equipment)
        devices, codes["das"] = self.__find_append_device(devices, das,
                                                          "das")
        return devices, codes

    def __make_devicedict(self, metatype, equipment):
        # if type(equipment) == dict:
        #    equipment=FDSN_EquipmentType(equipment)
        SN = equipment.serial_number
        devicedict = {
            "metatype": metatype,
            "manufacturer": equipment.manufacturer,
            "model": equipment.model,
            "serial_number": "unknown" if SN is None else SN,
        }
        return devicedict

    def __find_append_device(self, devices, device, device_name):
        """
        Find or append device to dictionary of devices

        device codes are '{device_name}_N', where N is a counter for
        that type of device
        """
        n_matching_devices = 0
        for device_code, value in devices.items():
            if device_name not in device_code:
                continue
            else:
                n_matching_devices = n_matching_devices + 1
                if device == value:
                    return devices, device_code
        device_code = device_name + "_" + str(n_matching_devices + 1)
        devices[device_code] = device
        return devices, device_code

    def __make_channel(self, das_code, device_codes, values, open_date,
                       close_date, debug=False):
        if debug:
            print("das_code=", das_code)
            print("device_codes=", device_codes)
            print("values=", values)
        das = das_code.split("_")
        das_component = das[0]
        if len(das) > 1:
            das_connector = das[1]
        else:
            das_connector = "1"
        azimuth, dip = obsinfo.get_azimuth_dip(
            values["sensor"].seed_codes, values["orientation_code"]
        )
        ana_filter_list = []
        for comp_type in ["sensor", "preamplifier", "datalogger"]:
            if comp_type in values:
                if debug:
                    print(f"values[{comp_type}]=", values[comp_type])
        ch = {
            "location_code": values["location_code"],
            "seed_code": obsinfo.make_channel_code(
                values["sensor"].seed_codes,
                values["band_code"],
                values["inst_code"],
                values["orientation_code"],
                values["sample_rate"],
            ),
            "sensor": device_codes["sensor"],
            "sensor_component": values["orientation_code"],
            "analog_filter_list": ana_filter_list,
            "das": device_codes["das"],
            "das_connector": das_connector,
            "das_component": das_component,
            "das_digital_filter": values["datalogger"].reference_code,
            "data_format": "STEIM1",
            "polarity_reversal": dip == "-90.0",
            "open_date": open_date,
            "close_date": close_date,
            "channel_flags": "CG",
        }
        return ch
