"""
This is a template script - an example of how a CEA script should be set up.

NOTE: ADD YOUR SCRIPT'S DOCUMENTATION HERE (what, why, include literature references)
"""

# import cea.bigmacc.bigmacc_util as util
import cea.resources.radiation_daysim.radiation_main
import os
import cea.config
# import cea.inputlocator
# import cea.demand.demand_main
# import cea.resources.radiation_daysim.radiation_main
# import cea.bigmacc.copy_results
# import cea.datamanagement.archetypes_mapper
import zipfile

import cea.bigmacc.bigmacc_util as util
import cea.bigmacc.create_rule_dataframe
# import numpy as np
# import itertools
# import distutils
# from distutils import dir_util
import shutil

__author__ = "Justin McCarty"
__copyright__ = " "
__credits__ = ["Justin McCarty"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = ""
__email__ = ""
__status__ = ""

def set(config):
    key_list = util.generate_key_list(config.bigmacc.strategies)
    run_rad = config.bigmacc.runradiation
    df = cea.bigmacc.create_rule_dataframe.main(config)
    config.bigmacc.copyrad = 'def' #df['copy_rad'].values[1]
    print(1)
    print(config.bigmacc.copyrad)

def pr(config):
    print(2)
    print(config.bigmacc.copyrad)


if __name__ == '__main__':
    set(cea.config.Configuration())
    pr(cea.config.Configuration())


    # project = r"C:\Users\justi\Documents\project"
    # destination = r"C:\Users\justi\Desktop\project"
    # parent = "parent"
    # scenario = "initial"
    # key = "key"
    #
    # # os.mkdir(os.path.join(destination,parent,scenario))
    #
    # zip_loc = os.path.join(project, parent, scenario)
    #
    # zip_dest = os.path.join(destination, parent)
    #
    # # root_loc = os.path.join()
    #
    # make_archive(zip_loc, os.path.join(zip_dest, key+".zip"))
    # un_zip(os.path.join(zip_dest, key))
    # config = cea.config.Configuration()
    # zip_loc = os.path.join(config.general.scenario)
    # zip_dest = config.bigmacc.keys
    #
    # # root_loc = os.path.join()
    #
    # make_archive(zip_loc, os.path.join(zip_dest, key + ".zip"))
    # un_zip(os.path.join(zip_dest, key))