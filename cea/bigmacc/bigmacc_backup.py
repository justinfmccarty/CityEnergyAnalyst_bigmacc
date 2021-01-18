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
import cea.bigmacc.copy_results
import cea.bigmacc.bigmacc_rules
import cea.datamanagement.archetypes_mapper
import cea.datamanagement.data_initializer
import cea.analysis.costs.system_costs
import cea.analysis.lca.main
import cea.demand.schedule_maker.schedule_maker as schedule_maker
import cea.bigmacc.bigmacc_util as util
import distutils
import cea.technologies.solar.photovoltaic as photovoltaic
import cea.resources.water_body_potential as water
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
    This is the main entry point to your script. Any parameters used by your script must be present in the ``config``
    parameter. The CLI will call this ``main`` function passing in a ``config`` object after adjusting the configuration
    to reflect parameters passed on the command line / user interface

    :param config:
    :type config: cea.config.Configuration
    :return:
    """

    locator = cea.inputlocator.InputLocator(config.scenario)
    i = config.bigmacc.key
    print('i')
    print(i)
    # SCENARIO SETUP ---

    scen_check = pd.read_csv(os.path.join(config.bigmacc.keys, 'logger.csv'), index_col='Unnamed: 0')
    experiment_key = 'exp_{}'.format(i)
    print(experiment_key)
    if experiment_key in scen_check['Experiments'].values.tolist():
        print('Experiment was finished previously, moving to next.')
        pass

    else:
        print('START: experiment {}.'.format(i))

        # INITIALIZE TIMER ---
        t0 = time.perf_counter()
        if os.path.exists(os.path.join(config.bigmacc.keys, i)):
            print(' - Folder exists for experiment {}.'.format(i))
        else:
            os.mkdir(os.path.join(config.bigmacc.keys, i))
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
            print(' - Running radiation simulation for experiment {}.'.format(i))
            if os.path.exists(locator.get_radiation_building('B000')):
                print(' - Radiation folder exists for experiment {}, using that.'.format(i))
            else:
                print(' - Radiation running for experiment {}.'.format(i))
                cea.resources.radiation_daysim.radiation_main.main(config)
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

        print(' - Running demand simulation for experiment {}.'.format(i))
        cea.demand.demand_main.main(config)

        print(' - Run PV is {}.'.format(config.bigmacc.pv))
        # if PV simulation is needed, run it.
        if config.bigmacc.pv == True:
            print(' - Running PV simulation for experiment {}.'.format(i))
            photovoltaic.main(config)

        print('Run water-body exchange is {}.'.format(config.bigmacc.water))
        # if water-body simulation is needed, run it.
        if config.bigmacc.water == True:
            print(' - Running water body simulation for experiment {}.'.format(i))
            water.main(config)

        # running the emissions and costing calculations
        cea.analysis.costs.system_costs.main(config)
        cea.analysis.lca.main.main(config)

        # clone out the simulation inputs and outputs directory
        print(' - Transferring results directory for experiment {}.'.format(i))

        inputs_path = os.path.join(config.bigmacc.keys, i, config.general.scenario_name, 'inputs')
        outputs_path = os.path.join(config.bigmacc.keys, i, config.general.scenario_name, 'outputs', 'data')
        # costs_path = os.path.join(config.bigmacc.keys, i, 'outputs', 'data', 'costs')
        # demand_path = os.path.join(config.bigmacc.keys, i, 'outputs', 'data', 'demand')
        # emissions_path = os.path.join(config.bigmacc.keys, i, 'outputs', 'data', 'emissions')
        # rad_path = os.path.join(config.bigmacc.keys, i, 'outputs', 'data', 'solar-radiation')

        distutils.dir_util.copy_tree(locator.get_data_results_folder(), outputs_path)
        distutils.dir_util.copy_tree(locator.get_input_folder(), inputs_path)

        time_elapsed = time.perf_counter() - t0

        log_df = pd.read_csv(os.path.join(config.bigmacc.keys, 'logger.csv'),
                             index_col='Unnamed: 0')
        log_df = log_df.append(pd.DataFrame({'Experiments': 'exp_{}'.format(i),
                                             'Completed': 'True',
                                             'Experiment Time': '%d.2 seconds' % time_elapsed,
                                             'Unique Radiation': config.bigmacc.runrad}, index=[0]), ignore_index=True)
        log_df.to_csv(os.path.join(config.bigmacc.keys, 'logger.csv'))

        # delete results
        shutil.rmtree(locator.get_costs_folder())
        shutil.rmtree(locator.get_demand_results_folder())
        shutil.rmtree(locator.get_lca_emissions_results_folder())
        shutil.rmtree(locator.get_solar_radiation_folder())
        shutil.rmtree(locator.get_potentials_folder())
        print('END: experiment {}. \n'.format(i))


def main(config):


    cea.datamanagement.data_initializer.main(config)
    key_list = util.generate_key_list(config)

    if os.path.exists(os.path.join(config.bigmacc.keys, 'logger.csv')):
        pass
    else:
        initialdf = pd.DataFrame(columns=['Experiments', 'Completed', 'Experiment Time', 'Unique Radiation'])
        initialdf.to_csv(os.path.join(config.bigmacc.keys, 'logger.csv'))
        initialdf = []

    for i in key_list:
        config.bigmacc.key = i
        print('key in main')
        print(config.bigmacc.key)
        run(config)

    print('Simulations completed. Move to next scenario.')


if __name__ == '__main__':
    main(cea.config.Configuration())
