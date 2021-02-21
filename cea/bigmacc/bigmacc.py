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
import cea.bigmacc.wesbrook_DH
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


def run(config):
    print('Key in run')
    print(config.bigmacc.key)
    """
    This is the main script for the bigmacc process. It iteartes through various CEA and bigmacc operations for each
    key (i.e. 01011101). It ends by saving a sample of the hourly results across the key for each building in a netcdf 
    and then wiping the project files to reset them for the next iteration. 

    :param config:
    :type config: cea.config.Configuration
    :return:
    """

    locator = cea.inputlocator.InputLocator(config.scenario)
    i = config.bigmacc.key
    print(i)
    # SCENARIO SETUP ---

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
        if os.path.exists(os.path.join(config.bigmacc.data, config.general.parent, i)):
            print(' - Folder exists for experiment {}.'.format(i))
        else:
            os.mkdir(os.path.join(config.bigmacc.data, config.general.parent, i))
            print(' - Folder does not exist for experiment {}, creating now.'.format(i))

        # run the archetype mapper to leverage the newly loaded typology file and set parameters
        print(' - Running archetype mapper for experiment {} to remove changes made in the last experiment.'.format(i))
        cea.datamanagement.archetypes_mapper.main(config)

        # run the rule checker to set the scenario parameters
        print(' - Running rule checker for experiment {}.'.format(i))
        cea.bigmacc.bigmacc_rules.main(config)

        # SIMULATIONS ---

        print(' - Run radiation is {}.'.format(config.bigmacc.runrad))
        print(' - Write sensor data is {}.'.format(config.radiation.write_sensor_data))
        # checking on need for radiation simulation

        if config.bigmacc.runrad == True:
            # this nested statement is for when we rerun the simulations and no longer need to run the unique radiation
            if config.bigmacc.rerun != True:
                print(' - Running radiation simulation for experiment {}.'.format(i))
                if os.path.exists(locator.get_radiation_building('B000')):
                    print(' - Radiation folder exists for experiment {}, copying.'.format(i))
                else:
                    print(' - Radiation running for experiment {}.'.format(i))
                    cea.resources.radiation_daysim.radiation_main.main(config)
            else:
                print(' - Copying radiation simulation data from previous run for experiment {}.'.format(i))
                old_rad_files = os.path.join(config.bigmacc.data, config.general.parent, i,
                                             config.general.scenario_name, 'outputs', 'data', 'solar-radiation')
                distutils.dir_util.copy_tree(old_rad_files, locator.get_solar_radiation_folder())
        else:
            radfiles = config.bigmacc.copyrad
            print(' - Copying radiation results from {}.'.format(radfiles))
            distutils.dir_util.copy_tree(radfiles, locator.get_solar_radiation_folder())
            # shutil.copy(radfiles, locator.get_solar_radiation_folder())
            print(' - Experiment {} does not require new radiation simulation.'.format(i))

        # running demand forecasting
        if os.path.exists(locator.get_schedule_model_file('B000')):
            print(' - Schedules exist for experiment {}.'.format(i))
        else:
            print(' - Schedule maker running for experiment {}.'.format(i))
            schedule_maker.main(config)

        # check to see if we need to rerun demand or if we can copy
        if config.bigmacc.rerun != True:
            print(' - Running demand simulation for experiment {}.'.format(i))
            cea.demand.demand_main.main(config)
        else:
            if keys[0]==1:
                print(' - Running demand simulation for experiment {}.'.format(i))
                cea.demand.demand_main.main(config)
            elif keys[6]==1:
                print(' - Running demand simulation for experiment {}.'.format(i))
                cea.demand.demand_main.main(config)
            else:
                print(' - Looking for demand results data from previous run for experiment {}.'.format(i))
                old_demand_files = os.path.join(config.bigmacc.data, config.general.parent, i,
                                            config.general.scenario_name, 'outputs', 'data', 'demand')
                if os.path.exists(old_demand_files):
                    print(' - Copy demand results files from previous run of experiment {}.'.format(i))
                    distutils.dir_util.copy_tree(old_demand_files, locator.get_demand_results_folder())
                else:
                    print(' - No results found.')
                    print(' - Running demand simulation for experiment {}.'.format(i))
                    cea.demand.demand_main.main(config)

        if config.bigmacc.pv == True:
            print(' - Run PV is {}.'.format(config.bigmacc.pv))
            if config.bigmacc.rerun == True:
                print(' - Looking for radiation simulation data from previous run for experiment {}.'.format(i))
                old_pv_files = os.path.join(config.bigmacc.data, config.general.parent, i,
                                            config.general.scenario_name, 'outputs', 'data', 'potentials', 'solar')
                if os.path.exists(old_pv_files):
                    print(' - Copying PV files from previous run of experiment {}.'.format(i))
                    distutils.dir_util.copy_tree(old_pv_files, locator.solar_potential_folder())
                else:
                    print(' - PV files do not exist for previous run of experiment {} at {}.'.format(i, old_pv_files))
                    print(' - Running PV simulation for experiment {}.'.format(i))
                    photovoltaic.main(config)
            else:
                # if PV simulation is needed, run it.
                print(' - Running PV simulation for experiment {}.'.format(i))
                photovoltaic.main(config)

        print('Run water-body exchange is {}.'.format(config.bigmacc.water))
        # if water-body simulation is needed, run it.
        if config.bigmacc.water == True:
            print(' - Running water body simulation for experiment {}.'.format(i))
            water.main(config)

        # recalculating the supply split between grid and ng in the websrook DH
        if keys[4] == 1:
            print(' - Do not run district heat recalculation.')
        else:
            print(' - Run district heat recalculation.')
            cea.bigmacc.wesbrook_DH.main(config)

        if keys[7] == 1:
            print(' - PV use detected. Adding PV generation to demand files.')
            util.write_pv_to_demand(config)
        else:
            print(' - No PV use detected.')

        # running the emissions and costing calculations
        print(' - Run cost and emissions scripts.')
        cea.analysis.costs.system_costs.main(config)
        cea.analysis.lca.main.main(config)

        # clone out the simulation inputs and outputs directory
        print(' - Transferring results directory for experiment {}.'.format(i))

        new_inputs_path = os.path.join(config.bigmacc.data, config.general.parent, i,
                                       config.general.scenario_name, 'inputs')
        new_outputs_path = os.path.join(config.bigmacc.data, config.general.parent, i,
                                        config.general.scenario_name, 'outputs', 'data')

        distutils.dir_util.copy_tree(locator.get_data_results_folder(), new_outputs_path)
        distutils.dir_util.copy_tree(locator.get_input_folder(), new_inputs_path)

        time_elapsed = time.perf_counter() - t0

        # save log information
        log_df = pd.read_csv(os.path.join(bigmacc_outputs_path, 'logger.csv'),
                             index_col='Unnamed: 0')
        log_df = log_df.append(pd.DataFrame({'Experiments': 'exp_{}'.format(i),
                                             'Completed': 'True',
                                             'Experiment Time': '%d.2 seconds' % time_elapsed,
                                             'Unique Radiation': config.bigmacc.runrad}, index=[0]), ignore_index=True)
        log_df.to_csv(os.path.join(bigmacc_outputs_path, 'logger.csv'))
        log_df.to_csv(r"C:\Users\justi\Desktop\126logger_backup.csv", )

        # write netcdf of hourly_results
        netcdf_writer.main(config, time='hourly')

        # delete results
        shutil.rmtree(locator.get_costs_folder())
        shutil.rmtree(locator.get_demand_results_folder())
        shutil.rmtree(locator.get_lca_emissions_results_folder())
        shutil.rmtree(locator.get_solar_radiation_folder())
        shutil.rmtree(locator.get_potentials_folder())

        # when the setpoint is changed it is in a deeper database than the archetypes mapper can reach so reset it here
        if keys[0] == 1:
            cea.datamanagement.data_initializer.main(config)
        else:
            pass
        print('END: experiment {}. \n'.format(i))


def main(config):
    print('STARTING UP THE BIGMACC SCRIPT')
    cea.datamanagement.data_initializer.main(config)
    key_list = util.generate_key_list(config)

    bigmacc_outputs_path = os.path.join(config.bigmacc.data, config.general.parent, 'bigmacc_out', config.bigmacc.round)
    if os.path.exists(bigmacc_outputs_path):
        pass
    else:
        os.mkdir(bigmacc_outputs_path)

    if os.path.exists(os.path.join(bigmacc_outputs_path, 'logger.csv')):
        pass
    else:
        initialdf = pd.DataFrame(columns=['Experiments', 'Completed', 'Experiment Time', 'Unique Radiation'])
        initialdf.to_csv(os.path.join(bigmacc_outputs_path, 'logger.csv'))

    for key in key_list:
        config.bigmacc.key = key
        print(config.bigmacc.key)
        run(config)

    print('Writing the whole scenario netcdf.')
    netcdf_writer.main(config, time='whole')

    print('Simulations completed. Move to next scenario.')


if __name__ == '__main__':
    main(cea.config.Configuration())
