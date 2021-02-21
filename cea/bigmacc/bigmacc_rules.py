"""
For the BIGMACC process each scenario will be checked to see which (if any) mitigation or adaptation measures it triggers.
This is run in the main script (bigmacc.py) after the archetype-mapping and before running the simulation
"""


import os
import cea.config
import cea.inputlocator
import cea.utilities.dbf
import cea.bigmacc.create_rule_dataframe

__author__ = "Justin McCarty"
__copyright__ = ""
__credits__ = ["Justin McCarty"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = ""
__email__ = ""
__status__ = ""


def necessary_cooling_hvac(service_df, val1, val2, val3):

    # check for existing cooling system
    if service_df['type_cs_y'] == 'HVAC_COOLING_AS0':
        # check for window ventilation
        if service_df['type_vent'] == 'HVAC_VENTILATION_AS0':
            return val1
        elif service_df['type_vent'] == 'HVAC_VENTILATION_AS3':
            return val1
        else:
            return val3
    else:
        return service_df['type_cs_y']

def necessary_cooling_supply(service_df, val1, val2, val3):

    # check for existing cooling system
    if service_df['type_cs_y'] == 'HVAC_COOLING_AS0':
        # check for window ventilation
        if service_df['type_vent'] == 'HVAC_VENTILATION_AS0':
            return val2
        elif service_df['type_vent'] == 'HVAC_VENTILATION_AS3':
            return val2
        else:
            return val2
    else:
        return service_df['type_cs_x']

def settemps_rule(df, config): # SETS FOR HEATING REDUCED 1C (20C TO 19C) AND SETS FOR COOLING RAISED 1C (24C TO 25C)

    print('---- CHECKING SETPOINT RULE ----')
    locator = cea.inputlocator.InputLocator(config.scenario)
    i = config.bigmacc.key
    keys = [int(x) for x in str(i)]
    if keys[0]==1:
        comfort_path = locator.get_building_comfort()

        comfort = cea.utilities.dbf.dbf_to_dataframe(comfort_path)

        comfort['Tcs_set_C'] = comfort['Tcs_set_C'] + df['SP_cool'].values.tolist()[0]
        comfort['Ths_set_C'] = comfort['Ths_set_C'] + df['SP_heat'].values.tolist()[0]
        comfort['Tcs_setb_C'] = comfort['Tcs_setb_C'] + df['SP_cool'].values.tolist()[0]
        comfort['Ths_setb_C'] = comfort['Ths_setb_C'] + df['SP_heat'].values.tolist()[0]
        cea.utilities.dbf.dataframe_to_dbf(comfort, comfort_path)

        print(' - Replacing set temperatures for experiment {}.'.format(i))
    else:
        print(' - Experiment {} does not use altered set temperatures.'.format(i))
    return print(' - Temperature setpoints and setbacks checked.')

def greenroof_rule(df, config):  # ALL BUILDINGS GET GREEN ROOFS
    print('---- CHECKING GREENROOF RULE ----')
    locator = cea.inputlocator.InputLocator(config.scenario)
    i = config.bigmacc.key
    keys = [int(x) for x in str(i)]
    if keys[1]==1:
        # in all buildings set type_roof = green_roof option
        arch_path = locator.get_building_architecture()
        arch = cea.utilities.dbf.dbf_to_dataframe(arch_path)
        arch['type_roof'] = str(df['GR_roof'].values.tolist()[0])
        cea.utilities.dbf.dataframe_to_dbf(arch, arch_path)
        print(' - Replacing type_roof with green roof construction for experiment {}.'.format(i))
    else:
        print(' - Experiment {} does not implement out of ordinary green roofs.'.format(i))
    return print(' - Rule for green roof installation has been checked.')

def deepretrofit_rule(df, config): # EXISTING BUILDINGS HAVE DEEP WALL AND WINDOW RETROFIT (WWR REDUCED)
    print('---- CHECKING DEEP RETROFIT RULE ----')

    locator = cea.inputlocator.InputLocator(config.scenario)
    i = config.bigmacc.key
    keys = [int(x) for x in str(i)]
    if keys[2] == 1:
        # in existing buildings set type_win, type_leak, type_wall = high_performance options
        typ_path = locator.get_building_typology()
        typ = cea.utilities.dbf.dbf_to_dataframe(typ_path)
        existing_bldgs = typ[typ['REFERENCE'] == 'existing']['Name'].values.tolist()

        arch_path = locator.get_building_architecture()
        arch = cea.utilities.dbf.dbf_to_dataframe(arch_path)

        arch.loc[arch.Name.isin(existing_bldgs), 'type_win'] = str(df['DR_win'].values.tolist()[0])  # triple glazing low-e two way
        arch.loc[arch.Name.isin(existing_bldgs), 'type_leak'] = str(df['DR_leak'].values.tolist()[0])  # second least leaky
        arch.loc[arch.Name.isin(existing_bldgs), 'type_wall'] = str(df['DR_wall'].values.tolist()[0])  # triple glazing low-e two way

        arch.loc[arch.Name.isin(existing_bldgs), 'wwr_north'] = float(df['DR_wwr'].values.tolist()[0])
        arch.loc[arch.Name.isin(existing_bldgs), 'wwr_east'] = float(df['DR_wwr'].values.tolist()[0])
        arch.loc[arch.Name.isin(existing_bldgs), 'wwr_south'] = float(df['DR_wwr'].values.tolist()[0])
        arch.loc[arch.Name.isin(existing_bldgs), 'wwr_west'] = float(df['DR_wwr'].values.tolist()[0])

        cea.utilities.dbf.dataframe_to_dbf(arch, arch_path)
        print(' - Replacing type_win, type_leak, type_wall with high performance retrofits and reducing WWR to 20% for experiment {}.'.format(i))

        pathway_code = config.general.parent
        pathway_items = pathway_code.split('_')
        year = int(pathway_items[1])
        pathway = pathway_items[2]

        print('---- CHECKING FOR DANGEROUS WARMING ----')
        if pathway == 'ssp585':
            if year > 2060:
                print(' - Experiment {} is entering a period of high warming and all buildings wil require cooling.'.format(i))
                air_con_path = locator.get_building_air_conditioning()
                air_con = cea.utilities.dbf.dbf_to_dataframe(air_con_path)
                supply_path = locator.get_building_supply()
                supply = cea.utilities.dbf.dbf_to_dataframe(supply_path)

                val1 = str(df['NEC_hvac_cs_nat_vent'].values.tolist()[0]) #HVAC_COOLING_AS7
                val2 = str(df['NEC_supply_cs'].values.tolist()[0]) #SUPPLY_COOLING_AS5
                val3 = str(df['NEC_hvac_cs_mech_vent'].values.tolist()[0]) #HVAC_COOLING_AS3

                service_df = supply.merge(air_con, on='Name')
                service_df['type_cs_y'] = service_df.apply(lambda x: necessary_cooling_hvac(x,
                                                                               val1,
                                                                               val2,
                                                                               val3),axis=1)
                service_df['type_cs_x'] = service_df.apply(lambda x: necessary_cooling_supply(x,
                                                                               val1,
                                                                               val2,
                                                                               val3), axis=1)
                supply = service_df[['Name', 'type_cs_x', 'type_hs_x', 'type_dhw_x', 'type_el']]
                supply = supply.rename(columns={'type_cs_x': 'type_cs', 'type_hs_x': 'type_hs', 'type_dhw_x': 'type_dhw'})

                air_con = service_df[['Name', 'type_cs_y', 'type_hs_y', 'type_dhw_y', 'type_ctrl', 'type_vent', 'heat_starts','heat_ends', 'cool_starts', 'cool_ends']]
                air_con = air_con.rename(columns={'type_cs_y': 'type_cs', 'type_hs_y': 'type_hs', 'type_dhw_y': 'type_dhw'})
                air_con['insert'] = 'testvalue'

                cea.utilities.dbf.dataframe_to_dbf(air_con, air_con_path)
                cea.utilities.dbf.dataframe_to_dbf(supply, supply_path)
            else:
                print(' - Pathway {} detected is on the higher end of warming but the time period {} does not warrant increased cooling service.'.format(pathway, year))
        else:
            print(' - Pathway {} detected is not in the range to warrant increased cooling service.'.format(pathway))
    else:
        print(' - Experiment {} does not implement out of ordinary wall and window constructions.'.format(i))
    return print(' - Retrofit rule has been checked.')


def passivehouse_rule(df, config): # NEW BUILD REQ PASSIVE
    print('---- CHECKING PASSIVE HOUSE RULE ----')

    locator = cea.inputlocator.InputLocator(config.scenario)
    i = config.bigmacc.key
    keys = [int(x) for x in str(i)]
    if keys[3] == 1:
        print(' - Setting all new construction to passive house standard for experiment {}.'.format(i))

        typ_path = locator.get_building_typology()
        typ = cea.utilities.dbf.dbf_to_dataframe(typ_path)
        new_bldgs = typ[typ['REFERENCE'] == 'new']['Name'].values.tolist()

        arch_path = locator.get_building_architecture()
        arch = cea.utilities.dbf.dbf_to_dataframe(arch_path)
        arch.loc[arch.Name.isin(new_bldgs), 'type_base'] = str(df['PH_base'].values.tolist()[0])
        arch.loc[arch.Name.isin(new_bldgs), 'type_leak'] = str(df['PH_leak'].values.tolist()[0])
        arch.loc[arch.Name.isin(new_bldgs), 'type_win'] = str(df['PH_win'].values.tolist()[0])
        arch.loc[arch.Name.isin(new_bldgs), 'type_roof'] = str(df['PH_roof'].values.tolist()[0])
        arch.loc[arch.Name.isin(new_bldgs), 'type_wall'] = str(df['PH_wall'].values.tolist()[0])
        arch.loc[arch.Name.isin(new_bldgs), 'type_floor'] = str(df['PH_floor'].values.tolist()[0])
        arch.loc[arch.Name.isin(new_bldgs), 'type_shade'] = str(df['PH_shade'].values.tolist()[0])
        arch.loc[arch.Name.isin(new_bldgs), 'type_part'] = str(df['PH_part'].values.tolist()[0])
        arch.loc[arch.Name.isin(new_bldgs), 'wwr_north'] = float(df['PH_wwr'].values.tolist()[0])
        arch.loc[arch.Name.isin(new_bldgs), 'wwr_east'] = float(df['PH_wwr'].values.tolist()[0])
        arch.loc[arch.Name.isin(new_bldgs), 'wwr_south'] = float(df['PH_wwr'].values.tolist()[0])
        arch.loc[arch.Name.isin(new_bldgs), 'wwr_west'] = float(df['PH_wwr'].values.tolist()[0])

        air_con_path = locator.get_building_air_conditioning()
        air_con = cea.utilities.dbf.dbf_to_dataframe(air_con_path)
        air_con.loc[air_con.Name.isin(new_bldgs), 'type_cs'] = str(df['PH_hvac_cs'].values.tolist()[0])

        print(' - Initial passive house types set for Experiment {}.'.format(i))
        # check for green roof
        if keys[1] == 1:
            # in new buildings set roof_type to Passive+green roof
            arch.loc[arch.Name.isin(new_bldgs), 'type_roof'] = str(df['PH_GR_roof'].values.tolist()[0])  #
            cea.utilities.dbf.dataframe_to_dbf(arch, arch_path)
            cea.utilities.dbf.dataframe_to_dbf(air_con, air_con_path)
            print(' - Setting roof_type for passive+green roof for experiment {}.'.format(i))
        else:
            cea.utilities.dbf.dataframe_to_dbf(arch, arch_path)
            cea.utilities.dbf.dataframe_to_dbf(air_con, air_con_path)
            print(' - Regular passive house type roof used for experiment {}.'.format(i))
    else:
        print(' - Experiment {} does not require new construction to be passive house.'.format(i))
    return print(' - Passive house in new builds rule has been checked.')


def heatpump_rule(df, config):  # NEW BUILD AND REFURBISHMENT/RETROFITS REQUIRE HEAT PUMP INSTALLATION (NO DISTRICT SERVICES)
    print('---- CHECKING HEATPUMP RULE ----')

    locator = cea.inputlocator.InputLocator(config.scenario)
    i = config.bigmacc.key
    keys = [int(x) for x in str(i)]
    if keys[4] == 1:

        air_con_path = locator.get_building_air_conditioning()
        air_con = cea.utilities.dbf.dbf_to_dataframe(air_con_path)

        supply_path = locator.get_building_supply()
        supply = cea.utilities.dbf.dbf_to_dataframe(supply_path)
        # in all buildings set HVAC_HEATING_AS4, HVAC_COOLING_AS5, SUPPLY_HEATING_AS7, SUPPLY_COOLING_AS1
        air_con['type_cs'] = str(df['HP_hvac_cs'].values.tolist()[0])
        air_con['type_hs'] = str(df['HP_hvac_hs'].values.tolist()[0])
        supply['type_cs'] = str(df['HP_supply_cs'].values.tolist()[0])
        supply['type_hs'] = str(df['HP_supply_hs'].values.tolist()[0])
        supply['type_dhw'] = str(df['HP_supply_dhw'].values.tolist()[0])

        print(' - Aligning HVAC+supply cooling, heating, and DHW for heat pump operation in experiment {}.'.format(i))
        # check for passive house
        if keys[3] == 1:
            typ_path = locator.get_building_typology()
            typ = cea.utilities.dbf.dbf_to_dataframe(typ_path)
            new_bldgs = typ[typ['REFERENCE'] == 'new']['Name'].values.tolist()
            # in new buildings set type_hvacCS to 3for2
            air_con.loc[air_con.Name.isin(new_bldgs), 'type_cs'] = str(df['HP_hvac_cs'].values.tolist()[0])
            cea.utilities.dbf.dataframe_to_dbf(air_con, air_con_path)
            cea.utilities.dbf.dataframe_to_dbf(supply, supply_path)
            print(' - Passive house detected, setting HVAC cs to use 3for2 hybrid AC for experiment {}.'.format(i))
        else:
            cea.utilities.dbf.dataframe_to_dbf(air_con, air_con_path)
            cea.utilities.dbf.dataframe_to_dbf(supply, supply_path)
    else:
        print(' - Experiment {} continues to use district heating with reqd minisplit cooling.'.format(i))
    return print(' - Heat pump rule has been checked.')


def masstimber_rule(df, config):  # NEW BUILD REQUIRES MASS TIMBER STRUCTURAL SYSTEMS
    print('---- CHECKING MASS TIMBER RULE ----')

    locator = cea.inputlocator.InputLocator(config.scenario)
    i = config.bigmacc.key
    keys = [int(x) for x in str(i)]
    if keys[5] == 1:
        # in new buildings set type_cons = CONSTRUCTION_AS2
        typ_path = locator.get_building_typology()
        typ = cea.utilities.dbf.dbf_to_dataframe(typ_path)
        new_bldgs = typ[typ['REFERENCE'] == 'new']['Name'].values.tolist()

        arch_path = locator.get_building_architecture()
        arch = cea.utilities.dbf.dbf_to_dataframe(arch_path)

        arch.loc[arch.Name.isin(new_bldgs), 'type_cons'] = str(df['MT_cons'].values.tolist()[0])  #
        cea.utilities.dbf.dataframe_to_dbf(arch, arch_path)
        # COMPUTE EMBODIED CARBON
        print(' - Setting type_cons to CONSTRUCTION_AS2 in experiment {}.'.format(i))
    else:
        print(' - Experiment {} continues to use cement-based CONSTRUCTION_AS3 structure.'.format(i))
    return print(' - Rule for mass timber use in new construction checked.')


def seawater_rule(df, config):  # DISTRICT COOLING SYSTEM INSTALLED LINKED TO WRECK BEACH
    print('---- CHECKING SEAWATER RULE ----')

    locator = cea.inputlocator.InputLocator(config.scenario)
    i = config.bigmacc.key
    keys = [int(x) for x in str(i)]
    if keys[6] == 1:
        config.bigmacc.water = True
        # in all buildings set HVAC_HEATING_AS4, HVAC_COOLING_AS5, SUPPLY_HEATING_AS7, SUPPLY_COOLING_AS3
        air_con_path = locator.get_building_air_conditioning()
        air_con = cea.utilities.dbf.dbf_to_dataframe(air_con_path)

        supply_path = locator.get_building_supply()
        supply = cea.utilities.dbf.dbf_to_dataframe(supply_path)
        # in all buildings set HVAC_HEATING_AS4, HVAC_COOLING_AS5, SUPPLY_HEATING_AS7, SUPPLY_COOLING_AS1

        air_con['type_cs'] = str(df['SW_hvac_cs'].values.tolist()[0])
        supply['type_cs'] = str(df['SW_supply_cs'].values.tolist()[0])

        cea.utilities.dbf.dataframe_to_dbf(air_con, air_con_path)
        cea.utilities.dbf.dataframe_to_dbf(supply, supply_path)


        print(' - Aligning HVAC_COOLING_AS5, SUPPLY_COOLING_AS3 for heatpump/seawater operation in experiment {}.'.format(i))
    else:
        print(' - Experiment {} continues to use district heating with reqd minisplit cooling.'.format(i))
    return print(' - Rule for seawater cooling loop checked.')


def rooftoppv_rule(df, config):  # ALL BUILDINGS HAVE ROOFTOP PV INSTALLED
    print('---- CHECKING ROOF PHOTOVOLTAICS RULE ----')

    locator = cea.inputlocator.InputLocator(config.scenario)
    i = config.bigmacc.key
    keys = [int(x) for x in str(i)]
    print(config.bigmacc.key)

    if keys[7] == 1:
        config.bigmacc.pv = True
        print(' - Setting run PV to True.')
        config.radiation.write_sensor_data = True
        print(' - Setting write-sensor-data to True.')

        arch_path = locator.get_building_architecture()
        arch = cea.utilities.dbf.dbf_to_dataframe(arch_path)

    #check for passive house
        if keys[3] == 1:
            #check for green roof
            if keys[1] == 1: #PV+GR+PH
                arch['type_roof'] = str(df['PV_GR_PH'].values.tolist()[0])
                print(' - Setting roof_type and solar heat gain coefficient for PV+green+passive house roof for experiment {}.'.format(i))
                config.bigmacc.heatgain = str(df['PV_GR_PH_hg'].values.tolist()[0])
                # config.bigmacc.heatgain is used in building_properties as a coefficient to change sensible gain on all roofs

                cea.utilities.dbf.dataframe_to_dbf(arch, arch_path)
            else: #PV+PH
                arch['type_roof'] = str(df['PV_PH'].values.tolist()[0])
                print(' - Setting roof_type and solar heat gain coefficient for PV+passive house roof for experiment {}.'.format(i))
                config.bigmacc.heatgain = str(df['PV_PH_hg'].values.tolist()[0])
                # config.bigmacc.heatgain is used in building_properties as a coefficient to change sensible gain on all roofs

                cea.utilities.dbf.dataframe_to_dbf(arch, arch_path)
        else:
            # check for green roof
            if keys[1] == 1: #PV+GR+ST
                arch['type_roof'] = str(df['PV_GR'].values.tolist()[0])
                print(' - Setting roof_type and solar heat gain coefficient for PV+green+standard roof for experiment {}.'.format(i))
                config.bigmacc.heatgain = str(df['PV_GR_hg'].values.tolist()[0])
                # config.bigmacc.heatgain is used in building_properties as a coefficient to change sensible gain on all roofs

                cea.utilities.dbf.dataframe_to_dbf(arch, arch_path)
            else: #PV+ST
                arch['type_roof'] = str(df['PV'].values.tolist()[0])
                print(' - Setting roof_type and solar heat gain coefficient for PV+standard roof for experiment {}.'.format(i))
                config.bigmacc.heatgain = float(df['PV_hg'].values.tolist()[0])
                # config.bigmacc.heatgain is used in building_properties as a coefficient to change sensible gain on all roofs

                cea.utilities.dbf.dataframe_to_dbf(arch, arch_path)
    else:
        config.bigmacc.pv = False
        print(' - Setting run PV to False.')
        config.radiation.write_sensor_data = False
        print(' - Setting write-sensor-data to False.')
        print(' - Experiment {} does not have rooftop solar.'.format(i))
        config.bigmacc.heatgain = 0.0
        # config.bigmacc.heatgain is used in building_properties as a coefficient to change sensible gain on all roofs

    return print(' - Rule for rooftop PV use checked')

def setrad_rule(df, config):
    config.bigmacc.runrad = df['run_rad'].values
    config.bigmacc.copyrad = str(df['copy_rad'].values.tolist()[0])

def rule_check(config):
    """
    Applies the current key to a set of rules. If a rule is triggered the script carries out an operation for that rule.

    :param config:
    :type config: cea.config.Configuration
    :return: print statement
    """

    rules_df = cea.bigmacc.create_rule_dataframe.main(config)
    rules_df_sub = rules_df[rules_df['keys'] == config.bigmacc.key]

    # necessary_cooling(rules_df_sub, config)  # 0 not needed only occurs under deep retrofits
    settemps_rule(rules_df_sub,config) # 1
    greenroof_rule(rules_df_sub,config) # 2
    deepretrofit_rule(rules_df_sub,config) # 3
    passivehouse_rule(rules_df_sub,config) # 4
    heatpump_rule(rules_df_sub,config) # 5
    masstimber_rule(rules_df_sub,config) # 6
    seawater_rule(rules_df_sub,config) # 7
    rooftoppv_rule(rules_df_sub,config) # 8
    setrad_rule(rules_df_sub, config)  # 9

    return print('Where key ({}) triggered rules, actions were taken. Proceeding to simulation steps.'.format(config.bigmacc.key))

def main(config):
    print('key in rules main')
    print(config.bigmacc.key)
    rule_check(config)

if __name__ == '__main__':
    main(cea.config.Configuration())
