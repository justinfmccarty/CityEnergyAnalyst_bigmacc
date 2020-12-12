"""
This is a template script - an example of how a CEA script should be set up.

NOTE: ADD YOUR SCRIPT'S DOCUMENTATION HERE (what, why, include literature references)
"""



import os
import cea.config
import cea.inputlocator
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

    # print(config.bigmacc.keys)
    # print(locator.get_building_geometry_folder())

    # key_directory = config.bigmacc.keys
    # keylist = [dI for dI in os.listdir(key_directory) if os.path.isdir(os.path.join(key_directory, dI))]
    # # temporary subset for debugging
    # # keylist = keylist[:5]
    #
    # for i in keylist:
    #     print(i)

    print(locator.get_demand_results_folder())
    print(config.bigmacc.keys)
    print(locator.get_weather_folder())

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

    am.main(config)

if __name__ == '__main__':
    main(cea.config.Configuration())
