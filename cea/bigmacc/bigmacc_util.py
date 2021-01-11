"""
General utilities for the bigmacc project.
"""



import os
import cea.config
import cea.inputlocator
import cea.demand.demand_main
import cea.resources.radiation_daysim.radiation_main
import cea.bigmacc.copy_results
import cea.datamanagement.archetypes_mapper
import configparser


__author__ = "Justin McCarty"
__copyright__ = ""
__credits__ = ["Justin McCarty"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = ""
__email__ = ""
__status__ = ""


def parsecommands(config_file, setting):
    config = configparser.ConfigParser()
    config.read(config_file)
    return config["commands"][setting]