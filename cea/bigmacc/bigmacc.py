"""
This is a template script - an example of how a CEA script should be set up.

NOTE: ADD YOUR SCRIPT'S DOCUMENTATION HERE (what, why, include literature references)
"""



import os
import cea.config
import cea.inputlocator
import cea.demand.demand_main
import cea.resources.radiation_daysim.radiation_main
import cea.bigmacc.copy_results
import cea.datamanagement.archetypes_mapper
import cea.bigmacc.bigmacc_util as bigmacc_util


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
    

    # identify key variables or paths
    key_directory = config.bigmacc.keys
    keylist = [dI for dI in os.listdir(key_directory) if os.path.isdir(os.path.join(key_directory, dI))]

    keylist = keylist[:3] # temporary subset for debugging




    for i in keylist:
        print('START: experiment {}.'.format(i))
        cea.config.key = i






        # load in the new weather file
        print(' - Transferring weather file for experiment {}.'.format(i))
        weatherpath = os.path.join(config.bigmacc.keys, '{}'.format(i), 'weather')
        try:
            cea.bigmacc.copy_results.main(weatherpath, locator.get_weather_folder())
        except:
            pass

        # load in the new typology file
        print(' - Transferring typology file for experiment {}.'.format(i))
        typologypath = os.path.join(config.bigmacc.keys, '{}'.format(i), 'typology')
        try:
            cea.bigmacc.copy_results.main(locator.get_building_properties_folder(), typologypath)
        except:
            pass

        # load in the new zone file
        print(' - Transferring zone file for experiment {}.'.format(i))
        zonepath = os.path.join(config.bigmacc.keys, '{}'.format(i), 'zone')
        try:
            cea.bigmacc.copy_results.main(zonepath, locator.get_building_geometry_folder())
        except:
            pass

        # run the archetype mapper to leverage the newly loaded typology file and set parameters
        print(' - Running archetype mapper for experiment {}.'.format(i))
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
        if config.bigmacc.commandpath == True:
            print(' - Running radiation simulation for experiment {}.'.format(i))
            try:
                cea.resources.radiation_daysim.radiation_main.main(config)
            except:
                pass
        else:
            print(' - Experiment {} does not require new radiation simulation.'.format(i))

        print(' - Running demand simulation for experiment {}.'.format(i))
        try:
            cea.demand.demand_main.main(config)
        except:
            pass

        ## STORE RESULT ---

        # clone out the simulation results directory
        print(' - Transferring results directory for experiment {}.'.format(i))
        resultspath = os.path.join(config.bigmacc.keys, '{}'.format(i), 'results')
        try:
            cea.bigmacc.copy_results.main(locator.get_data_results_folder(), resultspath)
        except:
            pass


        ## RESET FILES FOR NEXT ---
        cea.utilities.data_initializer.main(config)
        print('END: experiment {}. \n'.format(i))



if __name__ == '__main__':
    main(cea.config.Configuration())
