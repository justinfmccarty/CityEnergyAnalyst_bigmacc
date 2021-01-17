"""
The BIGMACC script.
"""

import os
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
import cea.bigmacc.bigmacc_util as util
import distutils
from distutils import dir_util

__author__ = "Justin McCarty"
__copyright__ = ""
__credits__ = ["Justin McCarty"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = ""
__email__ = ""
__status__ = ""


def main(config):
    """
    This is the main entry point to your script. Any parameters used by your script must be present in the ``config``
    parameter. The CLI will call this ``main`` function passing in a ``config`` object after adjusting the configuration
    to reflect parameters passed on the command line / user interface

    :param config:
    :type config: cea.config.Configuration
    :return:
    """

    locator = cea.inputlocator.InputLocator(config.scenario)

    ## SCENARIO SETUP ---
    key_list = util.generate_key_list(config.bigmacc.strategies)

    for i in key_list:
        print('START: experiment {}.'.format(i))
        cea.config.key = i

        os.mkdir(os.path.join(config.bigmacc.keys, i))
        # run the archetype mapper to leverage the newly loaded typology file and set parameters
        print(' - Running archetype mapper for experiment {} to remove changes made in the last experiment.'.format(i))
        try:
            cea.datamanagement.archetypes_mapper.main(config)
        except:
            pass

        # run the rule checker to set the scenario parameters
        print(' - Running rule checker for experiment {}.'.format(i))
        try:
            cea.bigmacc.bigmacc_rules.main(config)
        except:
            pass

        ## SIMULATIONS ---
        if config.bigmacc.runrad == True:
            print(' - Running radiation simulation for experiment {}.'.format(i))
            try:
                cea.resources.radiation_daysim.radiation_main.main(config)
            except:
                pass
        else:
            radfiles = config.bigmacc.copyrad
            distutils.dir_util.copy_tree(radfiles, locator.get_solar_radiation_folder())
            print(' - Experiment {} does not require new radiation simulation.'.format(i))

        print(' - Running demand simulation for experiment {}.'.format(i))
        try:
            cea.demand.demand_main.main(config)
        except:
            pass

        ## STORE RESULT ---

        # clone out the simulation inputs and outputs directory
        print(' - Transferring results directory for experiment {}.'.format(i))

        # inputs_path = os.path.join(config.bigmacc.keys, i, 'inputs')
        # outputs_path = os.path.join(config.bigmacc.keys, i, 'outputs', 'data')
        #
        # distutils.dir_util.copy_tree(locator.get_data_results_folder(), outputs_path)
        # distutils.dir_util.copy_tree(locator.get_input_folder(), inputs_path)
        #
        # shutil.make_archive(config.bigmacc.scenario, 'zip', os.path.join(config.bigmacc.keys, i))

        util.make_archive(os.path.join(config.general.scenario),
                          os.path.join(config.bigmacc.keys, i + ".zip"))
        util.un_zip(os.path.join(config.bigmacc.keys, i))

        ## RESET FILES FOR NEXT ---
        # cea.datamanagement.data_initializer.main(config)

        # delete results
        shutil.rmtree(locator.get_data_results_folder())
        print('END: experiment {}. \n'.format(i))


if __name__ == '__main__':
    main(cea.config.Configuration())
