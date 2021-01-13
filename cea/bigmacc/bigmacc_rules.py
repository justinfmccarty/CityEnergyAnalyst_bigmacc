"""
For the BIGMACC process each scenario will be checked to see which (if any) mitigation or adaptation measures it triggers.
This is run in the main script (bigmacc.py) after the archetype-mapping and before running the simulation
"""


import os
import cea.config
import cea.inputlocator
import cea.utilities.dbf

__author__ = "Justin McCarty"
__copyright__ = ""
__credits__ = ["Justin McCarty"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = ""
__email__ = ""
__status__ = ""


def runrad_rule(config): # SETS FOR HEATING REDUCED 1C (20C TO 19C) AND SETS FOR COOLING RAISED 1C (24C TO 25C)
    locator = cea.inputlocator.InputLocator(config.scenario)
    activekey = config.bigmacc.key




    if keys[0]==1:
        from shutil import copyfile
        copyfile(locator.get_alt_use_type_properties(), locator.get_database_use_types_properties())
        print(' - Replacing set temperatures for experiment {}.'.format(i))
    else:
        print(' - Experiment {} does not use altered set temperatures.'.format(i))
    return print(' - Temperature setpoints and setbacks checked.')

def settemps_rule(keys,config): # SETS FOR HEATING REDUCED 1C (20C TO 19C) AND SETS FOR COOLING RAISED 1C (24C TO 25C)
    locator = cea.inputlocator.InputLocator(config.scenario)

    if keys[0]==1:
        from shutil import copyfile
        copyfile(locator.get_alt_use_type_properties(), locator.get_database_use_types_properties())
        print(' - Replacing set temperatures for experiment {}.'.format(i))
    else:
        print(' - Experiment {} does not use altered set temperatures.'.format(i))
    return print(' - Temperature setpoints and setbacks checked.')

def greenroof_rule(keys,config):  # ALL BUILDINGS GET GREEN ROOFS
    locator = cea.inputlocator.InputLocator(config.scenario)
    if keys[1]==1:
        # in all buildings set type_roof = green_roof option
        arch_path = locator.get_building_architecture()
        arch = cea.utilities.dbf.dbf_to_dataframe(arch_path)
        arch['type_roof'] = 'ROOF_AS16'
        cea.utilities.dbf.dataframe_to_dbf(arch, arch_path)
        print(' - Replacing type_roof with green roof construction for experiment {}.'.format(i))
    else:
        print(' - Experiment {} does not implement out of ordinary green roofs.'.format(i))
    return print(' - Rule for green roof installation has been checked.')

def deepretrofit_rule(keys,config): # EXISTING BUILDINGS HAVE DEEP WALL AND WINDOW RETROFIT (WWR REDUCED)
    locator = cea.inputlocator.InputLocator(config.scenario)
    if keys[2] == 1:
        # in existing buildings set type_win, type_leak, type_wall = high_performance options
        typ_path = locator.get_building_typology()
        typ = cea.utilities.dbf.dbf_to_dataframe(typ_path)
        existing_bldgs = typ[typ['REFERENCE'] == 'existing']['Name'].values.tolist()

        arch_path = locator.get_building_architecture()
        arch = cea.utilities.dbf.dbf_to_dataframe(arch_path)
        # arch['type_win'] = 'WINDOW_AS6'
        arch.loc[arch.Name.isin(existing_bldgs), 'type_win'] = 'WINDOW_AS6'  # triple glazing low-e two way
        arch.loc[arch.Name.isin(existing_bldgs), 'type_leak'] = 'TIGHTNESS_AS2'  # second least leaky
        arch.loc[arch.Name.isin(existing_bldgs), 'type_wall'] = 'WALL_AS17'  # triple glazing low-e two way

        arch.loc[arch.Name.isin(existing_bldgs), 'wwr_north'] = 0.20
        arch.loc[arch.Name.isin(existing_bldgs), 'wwr_east'] = 0.20
        arch.loc[arch.Name.isin(existing_bldgs), 'wwr_south'] = 0.20
        arch.loc[arch.Name.isin(existing_bldgs), 'wwr_west'] = 0.20


        cea.utilities.dbf.dataframe_to_dbf(arch, arch_path)
        print(' - Replacing type_win, type_leak, type_wall with high performance retrofits and reducing WWR to 20% for experiment {}.'.format(i))
    else:
        print(' - Experiment {} does not implement out of ordinary wall and window constructions.'.format(i))
    return print(' - Retrofit rule has been checked.')


def passivehouse_rule(keys,config): # NEW BUILD REQ PASSIVE
    locator = cea.inputlocator.InputLocator(config.scenario)
    if keys[3] == 1:
        print(' - Setting all new construction to passive house standard for experiment {}.'.format(i))

        typ_path = locator.get_building_typology()
        typ = cea.utilities.dbf.dbf_to_dataframe(typ_path)
        new_bldgs = typ[typ['REFERENCE'] == 'new']['Name'].values.tolist()

        arch_path = locator.get_building_architecture()
        arch = cea.utilities.dbf.dbf_to_dataframe(arch_path)

        arch.loc[arch.Name.isin(existing_bldgs), 'type_base'] = 'WINDOW_AS6'  #
        arch.loc[arch.Name.isin(existing_bldgs), 'type_leak'] = 'TIGHTNESS_AS1'  #
        arch.loc[arch.Name.isin(existing_bldgs), 'type_win'] = 'WALL_AS17'  #
        arch.loc[arch.Name.isin(existing_bldgs), 'type_roof'] = 'WALL_AS17'  #
        arch.loc[arch.Name.isin(existing_bldgs), 'type_wall'] = 'WALL_AS17'  #
        arch.loc[arch.Name.isin(existing_bldgs), 'type_floor'] = 'WALL_AS17'  #
        arch.loc[arch.Name.isin(existing_bldgs), 'type_shade'] = 'WALL_AS17'  #
        arch.loc[arch.Name.isin(existing_bldgs), 'type_part'] = 'WALL_AS17'  #
        arch.loc[arch.Name.isin(existing_bldgs), 'wwr_north'] = 0.20
        arch.loc[arch.Name.isin(existing_bldgs), 'wwr_east'] = 0.20
        arch.loc[arch.Name.isin(existing_bldgs), 'wwr_south'] = 0.20
        arch.loc[arch.Name.isin(existing_bldgs), 'wwr_west'] = 0.20

        # check for green roof
        if keys[1] == 1:
            # in new buildings set roof_type to Passive+green roof
            arch.loc[arch.Name.isin(new_bldgs), 'type_roof'] = 'ROOF_AS18'  #
            cea.utilities.dbf.dataframe_to_dbf(arch, arch_path)
            print(' - Setting roof_type for passive+green roof for experiment {}.'.format(i))

        else:
            print(' - Regular passive house type roof used for experiment {}.'.format(i))
    else:
        print(' - Experiment {} does not require new construction to be passive house.'.format(i))
    return print(' - Passive house in new builds rule has been checked.')


def heatpump_rule(keys,config):  # NEW BUILD AND REFURBISHMENT/RETROFITS REQUIRE HEAT PUMP INSTALLATION (NO DISTRICT SERVICES)
    locator = cea.inputlocator.InputLocator(config.scenario)
    if keys[4] == 1:

        air_con_path = locator.get_building_air_conditioning()
        air_con = cea.utilities.dbf.dbf_to_dataframe(air_con_path)

        supply_path = locator.get_building_supply()
        supply = cea.utilities.dbf.dbf_to_dataframe(supply_path)
        # in all buildings set HVAC_HEATING_AS4, HVAC_COOLING_AS5, SUPPLY_HEATING_AS7, SUPPLY_COOLING_AS1
        air_con['type_cs'] = 'HVAC_COOLING_AS5'
        air_con['type_hs'] = 'HVAC_HEATING_AS4'
        supply['type_cs'] = 'SUPPLY_COOLING_AS1'
        supply['type_hs'] = 'SUPPLY_HEATING_AS7'
        supply['type_dhw'] = 'SUPPLY_HOTWATER_AS7'

        cea.utilities.dbf.dataframe_to_dbf(air_con, air_con_path)
        cea.utilities.dbf.dataframe_to_dbf(supply, supply_path)
        print(' - Aligning SUPPLY_HOTWATER_AS7, HVAC_HEATING_AS4, HVAC_COOLING_AS5, SUPPLY_HEATING_AS7, SUPPLY_COOLING_AS1 for heat pump operation in experiment {}.'.format(i))
    else:
        print(' - Experiment {} continues to use district heating with reqd minisplit cooling.'.format(i))
    return print(' - Heat pump rule has been checked.')


def masstimber_rule(keys,config):  # NEW BUILD REQUIRES MASS TIMBER STRUCTURAL SYSTEMS
    locator = cea.inputlocator.InputLocator(config.scenario)
    if keys[5] == 1:
        # in new buildings set type_cons = CONSTRUCTION_AS2
        typ_path = locator.get_building_typology()
        typ = cea.utilities.dbf.dbf_to_dataframe(typ_path)
        new_bldgs = typ[typ['REFERENCE'] == 'new']['Name'].values.tolist()

        arch_path = locator.get_building_architecture()
        arch = cea.utilities.dbf.dbf_to_dataframe(arch_path)

        arch.loc[arch.Name.isin(new_bldgs), 'type_cons'] = 'CONSTRUCTION_AS2'  #
        cea.utilities.dbf.dataframe_to_dbf(arch, arch_path)
        # COMPUTE EMBODIED CARBON
        print(' - Setting type_cons to CONSTRUCTION_AS2 in experiment {}.'.format(i))
    else:
        print(' - Experiment {} continues to use cement-based CONSTRUCTION_AS3 structure.'.format(i))
    return print(' - Rule for mass timber use in new construction checked.')


def seawater_rule(keys,config):  # DISTRICT COOLING SYSTEM INSTALLED LINKED TO WRECK BEACH
    locator = cea.inputlocator.InputLocator(config.scenario)
    if keys[6] == 1:
        # in all buildings set HVAC_HEATING_AS4, HVAC_COOLING_AS5, SUPPLY_HEATING_AS7, SUPPLY_COOLING_AS3
        air_con_path = locator.get_building_air_conditioning()
        air_con = cea.utilities.dbf.dbf_to_dataframe(air_con_path)

        supply_path = locator.get_building_supply()
        supply = cea.utilities.dbf.dbf_to_dataframe(supply_path)
        # in all buildings set HVAC_HEATING_AS4, HVAC_COOLING_AS5, SUPPLY_HEATING_AS7, SUPPLY_COOLING_AS1

        air_con['type_cs'] = 'HVAC_COOLING_AS5'
        supply['type_cs'] = 'SUPPLY_COOLING_AS3'

        cea.utilities.dbf.dataframe_to_dbf(air_con, air_con_path)
        cea.utilities.dbf.dataframe_to_dbf(supply, supply_path)


        print(' - Aligning HVAC_COOLING_AS5, SUPPLY_COOLING_AS3 for heatpump/seawater operation in experiment {}.'.format(i))
    else:
        print(' - Experiment {} continues to use district heating with reqd minisplit cooling.'.format(i))
    return print(' - Rule for seawater cooling loop checked.')


def rooftoppv_rule(keys,config):  # ALL BUILDINGS HAVE ROOFTOP PV INSTALLED
    locator = cea.inputlocator.InputLocator(config.scenario)
    if keys[7] == 1:


        arch_path = locator.get_building_architecture()
        arch = cea.utilities.dbf.dbf_to_dataframe(arch_path)

    #check for passive house
        if keys[3] == 1:
            #check for green roof
            if keys[1] == 1: #PV+GR+PH
                arch['type_roof'] = 'ROOF_AS19'
                print(' - Setting roof_type and solar heat gain coefficient for PV+green+passive house roof for experiment {}.'.format(i))
                config.bigmacc.heatgain = 0.6
            else: #PV+PH
                arch['type_roof'] = 'ROOF_AS21'
                print(' - Setting roof_type and solar heat gain coefficient for PV+passive house roof for experiment {}.'.format(i))
                config.bigmacc.heatgain = 0.25
        else:
            # check for green roof
            if keys[1] == 1: #PV+GR+ST
                arch['type_roof'] = 'ROOF_AS20'
                print(' - Setting roof_type and solar heat gain coefficient for PV+green+standard roof for experiment {}.'.format(i))
                config.bigmacc.heatgain = 0.4
            else: #PV+ST
                arch['type_roof'] = 'ROOF_AS22'
                print(' - Setting roof_type and solar heat gain coefficient for PV+standard roof for experiment {}.'.format(i))
                config.bigmacc.heatgain = 0.1

            cea.utilities.dbf.dataframe_to_dbf(arch, arch_path)
    else:
        print(' - Experiment {} does not have rooftop solar.'.format(i))
        config.bigmacc.heatgain = 0.0
    return print(' - Rule for rooftop PV use checked')

def rule_check(config):
    """
    Applies the current key to a set of rules. If a rule is triggered the script carries out an operation for that rule.

    :param config:
    :type config: cea.config.Configuration
    :return: print statement
    """

    locator = cea.inputlocator.InputLocator(config.scenario)
    key = cea.config.key
    print(key)
    keys = [int(x) for x in str(key)]
    print(keys[0])
    settemps_rule(keys,config) # 1
    greenroof_rule(keys,config) # 2
    deepretrofit_rule(keys,config) # 3
    passivehouse_rule(keys,config) # 4
    heatpump_rule(keys,config) # 5
    masstimber_rule(keys,config) # 6
    seawater_rule(keys,config) # 7
    rooftoppv_rule(keys,config) # 8

    return print('Where key ({}) triggered rules, actions were taken. Proceeding to simulation steps.'.format(key))

def main(config):
    rule_check(config)

if __name__ == '__main__':
    main(cea.config.Configuration())
