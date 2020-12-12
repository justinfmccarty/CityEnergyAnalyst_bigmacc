"""
This is a template script - an example of how a CEA script should be set up.

NOTE: ADD YOUR SCRIPT'S DOCUMENTATION HERE (what, why, include literature references)
"""



import os
import cea.config
import cea.inputlocator
import cea.demand.demand_main as dm
import cea.resources.radiation_daysim.radiation_main as rm
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

    # identify key variables or paths
    key_directory = config.bigmacc.keys
    keylist = [dI for dI in os.listdir(key_directory) if os.path.isdir(os.path.join(key_directory, dI))]

    keylist = keylist[:3] # temporary subset for debugging

    for i in keylist:
        print('START: experiment {}.'.format(i))

        # load in the new weather file
        print(' - Transferring weather file for experiment {}.'.format(i))
        weatherpath = os.path.join(config.bigmacc.keys, '{}'.format(i), 'weather')
        cr.main(weatherpath, locator.get_weather_folder())

        # load in the new typology file
        print(' - Transferring typology file for experiment {}.'.format(i))
        typologypath = os.path.join(config.bigmacc.keys, '{}'.format(i), 'typology')
        cr.main(locator.get_building_properties_folder(), typologypath)

        # load in the new zone file
        print(' - Transferring zone file for experiment {}.'.format(i))
        zonepath = os.path.join(config.bigmacc.keys, '{}'.format(i), 'zone')
        cr.main(zonepath, locator.get_building_geometry_folder())

        # run the archetype mapper to leverage the newly loaded typology file and set parameters
        am.main(config)

        ## SIMULATIONS ---

        rm.main(config)
        dm.main(config)

        ## STORE RESULT ---

        # clone out the simulation results directory
        print(' - Transferring results directory for experiment {}.'.format(i))
        resultspath = os.path.join(config.bigmacc.keys, '{}'.format(i), 'results')
        cr.main(locator.get_data_results_folder(), resultspath)

        print('END: experiment {}. \n'.format(i))



if __name__ == '__main__':
    main(cea.config.Configuration())
