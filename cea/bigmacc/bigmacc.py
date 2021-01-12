"""
This is a template script - an example of how a CEA script should be set up.

NOTE: ADD YOUR SCRIPT'S DOCUMENTATION HERE (what, why, include literature references)
"""


import os
import cea.config
import cea.inputlocator
import cea.utilities.dbf
import cea.demand.demand_main as dm
import cea.resources.radiation_daysim.radiation_main as rm
import cea.bigmacc.typology_mover as tm
import cea.bigmacc.zone_mover as zm
import cea.bigmacc.copy_results as cr
import cea.datamanagement.archetypes_mapper as am

__author__ = "Justin McCarty"
__copyright__ = ""
__credits__ = ["Justin McCarty"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = ""
__email__ = ""
__status__ = ""


#
# def run(config, locator):
#     print(5)
#     print(config.scenario)
#     print(locator.get_building_geometry_folder())
#
def run_bigmacc_rules(config, locator):
    """
    Applies the current key to a set of rules. If a rule is triggered the script carries out an operation for that rule.

    :param config:
    :type config: cea.config.Configuration
    :param locator:
    :type locator: cea.inputlocator.InputLocator
    :return:
    """

    key_directory = config.bigmacc.keys
    keylist = [dI for dI in os.listdir(key_directory) if os.path.isdir(os.path.join(key_directory, dI))]



    for i in keylist:
        keys = [int(x) for x in str(i)]
        print(keys[0])

        # SETPOINT
        if keys[0]==1:
            from shutil import copyfile
            copyfile(locator.get_alt_use_type_properties(), locator.get_database_use_types_properties())
            print(' - Replacing set temperatures for experiment {}.'.format(i))
        else:
            print(' - Experiment {} does not use altered set temperatures.'.format(i))

        # GREEN ROOF
        if keys[1]==1:
            # in all buildings set type_roof = green_roof option
            arch_path = locator.get_building_architecture()
            arch = cea.utilities.dbf.dbf_to_dataframe(arch_path)
            arch['type_roof'] = 'ROOF_AS16'
            cea.utilities.dbf.dataframe_to_dbf(arch, arch_path)
            print(' - Replacing type_roof with green roof construction for experiment {}.'.format(i))
        else:
            print(' - Experiment {} does not implement out of ordinary green roofs.'.format(i))

        # WALL AND WINDOW RETROFIT
        if keys[2] == 1:
            # in existing buildings set type_win, type_leak, type_wall = high_performance options
            typ_path = locator.get_building_typology()
            typ = cea.utilities.dbf.dbf_to_dataframe(typ_path)
            typ_exist = typ[typ['REFERENCE']=='existing']['Name'].values.tolist()

            #need to map based on the typ_exist list
            arch_path = locator.get_building_architecture()
            arch = cea.utilities.dbf.dbf_to_dataframe(arch_path)
            arch['type_win'] = 'WINDOW_AS6' #triple glazing low-e two way
            arch['type_leak'] = 'TIGHTNESS_AS2' #second best
            arch['type_wall'] = 'WALL_AS17'

            arch['wwr_north'] = 0.20
            arch['wwr_east'] = 0.20
            arch['wwr_south'] = 0.20
            arch['wwr_west'] = 0.20
            cea.utilities.dbf.dataframe_to_dbf(arch, arch_path)
            print(' - Replacing type_win, type_leak, type_wall with high performance retrofits and reducing WWR to 20% for experiment {}.'.format(i))
        else:
            print(' - Experiment {} does not implement out of ordinary wall and window constructions.'.format(i))

        # NEW BUILD REQ PASSIVE
        if keys[3] == 1:
            print(' - Setting all new construction to passive house standard for experiment {}.'.format(i))
            # check for green roof
            if keys[1] == 1:
                # in all buildings set roof_type to PV+green roof
                print(' - Setting roof_type for passive+green roof for experiment {}.'.format(i))
                config.bigmacc.heatgain = 0.4
                print(' - Reducing rooftop sensible heat gain by 40% for experiment {}.'.format(i))

                # perma set config.bigmacc.heatgain = 0.4
            else:
                print(' - Regular passive house type roof used for experiment {}.'.format(i))
        else:
            print(' - Experiment {} does not require new construction to be passive house.'.format(i))

        # HEAT PUMPS IN ALL BUILDINGS
        if keys[4] == 1:
            # in all buildings set HVAC_HEATING_AS4, HVAC_COOLING_AS5, SUPPLY_HEATING_AS7, SUPPLY_COOLING_AS1
            print(' - Aligning SUPPLY_HOTWATER_AS7, HVAC_HEATING_AS4, HVAC_COOLING_AS5, SUPPLY_HEATING_AS7, SUPPLY_COOLING_AS1 for heat pump operation in experiment {}.'.format(i))
        else:
            print(' - Experiment {} continues to use district heating with reqd minisplit cooling.'.format(i))

        # NEW BUILD REQ MASS TIMBER
        if keys[5] == 1:
            # in new buildings set type_cons = CONSTRUCTION_AS2
            # COMPUTE EMBODIED CARBON
            print(' - Setting type_cons to CONSTRUCTION_AS2 in experiment {}.'.format(i))
        else:
            print(' - Experiment {} continues to use cement-based CONSTRUCTION_AS3 structure.'.format(i))

        # SEAWATER COOLING LOOP
        if keys[6] == 1:
            # in all buildings set HVAC_HEATING_AS4, HVAC_COOLING_AS5, SUPPLY_HEATING_AS7, SUPPLY_COOLING_AS3
            print(' - Aligning HVAC_COOLING_AS5, SUPPLY_COOLING_AS3 for heatpump/seawater operation in experiment {}.'.format(i))
        else:
            print(' - Experiment {} continues to use district heating with reqd minisplit cooling.'.format(i))

        # ROOFTOP PV
        if keys[7] == 1:
            #check for passive house
            if keys[3] == 1:
                #check for green roof
                if keys[1] == 1: #PV+GR+PH
                    print(' - Setting roof_type and solar heat gain coefficient for PV+green+passive house roof for experiment {}.'.format(i))
                    config.bigmacc.heatgain = 0.6
                else: #PV+PH
                    print(' - Setting roof_type and solar heat gain coefficient for PV+passive house roof for experiment {}.'.format(i))
                    config.bigmacc.heatgain = 0.25
            else:
                # check for green roof
                if keys[1] == 1: #PV+GR+ST
                    print(' - Setting roof_type and solar heat gain coefficient for PV+green+standard roof for experiment {}.'.format(i))
                    config.bigmacc.heatgain = 0.4
                else: #PV+ST
                    print(' - Setting roof_type and solar heat gain coefficient for PV+standard roof for experiment {}.'.format(i))
                    config.bigmacc.heatgain = 0.1
        else:
            print(' - Experiment {} does not have rooftop solar.'.format(i))
            config.bigmacc.heatgain = 0.0



def main(config):
    locator = cea.inputlocator.InputLocator(config.scenario)




    # alt_use_type_properties = locator.get_alt_use_type_properties()
    # cea.bigmacc.utils.copy_results(alt_use_type_properties, locator.get_database_use_types_properties())

    # print(locator.get_demand_results_folder())
    # print(config.bigmacc.keys)
    # print(locator.get_weather_folder())

    # # load in the new weather file
    # weatherpath = os.path.join(config.bigmacc.keys, '000000', 'weather')
    # cr.main(weatherpath, locator.get_weather_folder())
    #
    # # load in the new typology file
    # typologypath = os.path.join(config.bigmacc.keys, '000000', 'typology')
    # cr.main(locator.get_building_properties_folder(), typologypath)
    #
    # # load in the new zone file
    # zonepath = os.path.join(config.bigmacc.keys, '000000', 'zone')
    # cr.main(zonepath, locator.get_building_geometry_folder())
    #
    # # clone out the simulation results directory
    # resultspath = os.path.join(config.bigmacc.keys,'000000', 'results')
    # cr.main(locator.get_data_results_folder(), resultspath)

    # am.main(config)

if __name__ == '__main__':
    main(cea.config.Configuration())
