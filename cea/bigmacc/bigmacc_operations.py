"""
The BIGMACC script.
"""

import os
import pandas as pd
import time
import logging

logging.getLogger('numba').setLevel(logging.WARNING)
import shutil
import cea.config
import cea.utilities
import cea.inputlocator
import cea.demand.demand_main
import cea.resources.radiation_daysim.radiation_main
import cea.bigmacc.bigmacc_rules
import cea.bigmacc.wesbrook_DH_multi
import cea.bigmacc.wesbrook_DH_single
import cea.datamanagement.archetypes_mapper
import cea.datamanagement.data_initializer
import cea.analysis.costs.system_costs
import cea.analysis.lca.main
import cea.demand.schedule_maker.schedule_maker as schedule_maker
import cea.bigmacc.bigmacc_util as util
import distutils
import cea.technologies.solar.photovoltaic as photovoltaic
import cea.resources.water_body_potential as water
import cea.bigmacc.netcdf_writer as netcdf_writer
from distutils import dir_util

__author__ = "Justin McCarty"
__copyright__ = ""
__credits__ = ["Justin McCarty"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = ""
__email__ = ""
__status__ = ""


def run_bigmacc(config):
    """
    This is the main script for the bigmacc process. It iteartes through various CEA and bigmacc operations for each
    key (i.e. 01011101). It ends by saving a sample of the hourly results across the key for each building in a netcdf
    and then wiping the project files to reset them for the next iteration.

    :param config:
    :type config: cea.config.Configuration
    :return:
    """
    locator = cea.inputlocator.InputLocator(config.scenario)

    # set the key (i.e. 01010100)
    print('Key in run')
    i = config.bigmacc.key
    print(i)

    # SCENARIO SETUP ---
    cea.datamanagement.data_initializer.main(config)

    # use the scenario code to set the year for the lca and other operations that need the current year
    pathway_code = config.general.parent
    pathway_items = pathway_code.split('_')
    scenario_year = int(pathway_items[1])
    config.emissions.year_to_calculate = scenario_year

    bigmacc_outputs_path = os.path.join(config.bigmacc.data, config.general.parent, 'bigmacc_out', config.bigmacc.round)

    scen_check = pd.read_csv(os.path.join(bigmacc_outputs_path, 'logger.csv'), index_col='Unnamed: 0')
    experiment_key = 'exp_{}'.format(i)
    print(experiment_key)
    keys = [int(x) for x in str(i)]
    if experiment_key in scen_check['Experiments'].values.tolist():
        print('Experiment was finished previously, moving to next.')
        pass
    else:
        print('START: experiment {}.'.format(i))

        # INITIALIZE TIMER ---
        t0 = time.perf_counter()

        # run the archetype mapper to leverage the newly loaded typology file and set parameters
        print(' - Running archetype mapper for experiment {} to remove changes made in the last experiment.'.format(i))
        cea.datamanagement.archetypes_mapper.main(config)

        # run the rule checker to set the scenario parameters
        print(' - Running rule checker for experiment {}.'.format(i))
        cea.bigmacc.bigmacc_rules.main(config)

        # SIMULATIONS ---
        print(' - Run radiation is {}.'.format(config.bigmacc.runrad))
        print(' - Write sensor data is {}.'.format(config.radiation.write_sensor_data))

        # SIMULATION 1 checking on need for radiation simulation
        unique_rad_files = os.path.join(config.bigmacc.data, config.general.parent, 'bigmacc_in',
                                     util.change_key(i), 'solar-radiation')
        if i in config.bigmacc.runradiation:
            # everytime the runradiation list is triggered a new set of files is loaded in
            shutil.rmtree(locator.get_solar_radiation_folder())
            if config.bigmacc.rerun == True:
                print(' - Rerun mode, copying radiation files for experiment {}.'.format(i))
                distutils.dir_util.copy_tree(unique_rad_files, locator.get_solar_radiation_folder())
            else:
                print(' - Radiation running for experiment {}.'.format(i))
                cea.resources.radiation_daysim.radiation_main.main(config)
                print(' - Copying radiation files to repo for experiment {}.'.format(i))
                distutils.dir_util.copy_tree(locator.get_solar_radiation_folder(), unique_rad_files)
        else:
            print(' - Previous iteration radiation files are equivalent for experiment {}.'.format(i))

        if not os.path.exists(locator.get_solar_radiation_folder()):
            print(' - Radiation files for experiment {} not found, running radiation script.'.format(i))
            cea.resources.radiation_daysim.radiation_main.main(config)

        # SIMULATION 2 check to see if schedules need to be made
        bldg_names = locator.get_zone_building_names()
        for name in bldg_names:
            if not os.path.exists(locator.get_schedule_model_file(name)):
                print(' - Schedule maker running for building {}.'.format(name))
                schedule_maker.schedule_maker_main(locator, config)
            else:
                print(' - Schedules exist for building {}.'.format(name))
        print(' - Schedules exist for experiment {}.'.format(i))

        # SIMULATION 3 run demand
        # cea.demand.demand_main.main(config)

        if config.bigmacc.rerun != True:
            print(' - Running demand simulation for experiment {}.'.format(i))
            cea.demand.demand_main.main(config)
        else:
            if keys[0] == 1:
                print(' - Running demand simulation for experiment {}.'.format(i))
                cea.demand.demand_main.main(config)
            elif keys[6] == 1:
                print(' - Running demand simulation for experiment {}.'.format(i))
                cea.demand.demand_main.main(config)
            else:
                print(' - Copying demand results for experiment {}.'.format(i))
                                                config.bigmacc.key,'initial','outputs','data','demand')
                distutils.dir_util.copy_tree(old_demand_files, locator.get_demand_results_folder())

        if not os.path.exists(locator.get_demand_results_folder()):
            print(' - Demand results for experiment {} not found, running radiation script.'.format(i))
            cea.demand.demand_main.main(config)


        # SIMULATION 4 check to see if pv needs to run
        if config.bigmacc.pv == True:
            unique_pv_files = os.path.join(config.bigmacc.data, config.general.parent, 'bigmacc_in',
                                        util.change_key(i),'potentials', 'solar')
            if i in config.bigmacc.runradiation:
                shutil.rmtree(locator.solar_potential_folder())
                if config.bigmacc.rerun == True:
                    print(' - Rerun mode, copying PV files for experiment {}.'.format(i))
                    distutils.dir_util.copy_tree(unique_pv_files, locator.solar_potential_folder())
                else:
                    print(' - Radiation running for experiment {}.'.format(i))
                    photovoltaic.main(config)
                    print(' - Copying PV files to repo for experiment {}.'.format(i))
                    distutils.dir_util.copy_tree(locator.solar_potential_folder(),unique_pv_files)
            else:
                print(' - Previous iteration PV results files are equivalent for experiment {}.'.format(i))

            # last check for the PV files
            if not os.path.exists(locator.solar_potential_folder()):
                print(' - PV results do not exist running simulation for experiment {}.'.format(i))
                photovoltaic.main(config)
        else:
            print(f' - PV does not exist in scenario {i}.')

        # SIMULATION 5 recalculating the supply split between grid and ng in the wesbrook DH
        if keys[4] == 1:
            print(' - Do not run district heat recalculation.')
        else:
            print(' - Run district heat recalculation.')
            cea.bigmacc.wesbrook_DH_multi.main(config)

        # include PV results in demand results files for costing and emissions
        if keys[7] == 1:
            print(' - PV use detected. Adding PV generation to demand files.')
            util.write_pv_to_demand_multi(config)
        else:
            print(' - No PV use detected.')

        print(f' - Writing annual results for {i}.')
        util.rewrite_annual_demand(config)

        # SIMULATION 6 & 7 running the emissions and costing calculations
        print(' - Run cost and emissions scripts.')
        cea.analysis.costs.system_costs.main(config)
        cea.analysis.lca.main.main(config)

        # FILE MANAGEMENT ---

        # clone out the simulation inputs and outputs directory
        print(' - Transferring results directory for experiment {}.'.format(i))

        new_inputs_path = os.path.join(config.bigmacc.data, config.general.parent, 'bigmacc_out',
                                               config.bigmacc.key, 'inputs')
        # new_outputs_path_demand = os.path.join(config.bigmacc.data, config.general.parent, 'bigmacc_out',
        #                                        config.bigmacc.key, 'demand')

        if config.bigmacc.rerun != True:
            distutils.dir_util.copy_tree(locator.get_input_folder(), new_inputs_path)
            # distutils.dir_util.copy_tree(locator.get_demand_results_folder(), new_outputs_path_demand)
        else:
            distutils.dir_util.copy_tree(locator.get_input_folder(), new_inputs_path)
            # distutils.dir_util.copy_tree(locator.get_demand_results_folder(), new_outputs_path_demand)

        log_df = pd.read_csv(os.path.join(bigmacc_outputs_path, 'logger.csv'),
                             index_col='Unnamed: 0')
        # write netcdf of hourly_results
        print('Writing the hourly results to zarr.')
        netcdf_writer.main(config, time_scale='hourly')
        if len(log_df['Completed']) < (len(util.generate_key_list(config)) - 1):
            print('Writing the annual results to netcdf.')
        else:
            print('Writing the annual results to zarr.')
        netcdf_writer.main(config, time_scale='whole')

        time_elapsed = time.perf_counter() - t0

        # save log information
        log_df = log_df.append(pd.DataFrame({'Experiments': 'exp_{}'.format(i),
                                             'Completed': 'True',
                                             'Experiment Time': time_elapsed,
                                             'Unique Radiation': config.bigmacc.runrad}, index=[0]), ignore_index=True)
        log_df.to_csv(os.path.join(bigmacc_outputs_path, 'logger.csv'))
        log_df.to_csv(r"C:\Users\justi\Desktop\126logger_backup.csv", )

        # when the setpoint is changed it is in a deeper database than the archetypes mapper can reach so reset it here
        if keys[0] == 1:
            print(' - Rerun data initializer.')
            cea.datamanagement.data_initializer.main(config)
        else:
            pass
        print('END: experiment {}. \n'.format(i))
