"""
This is a template script - an example of how a CEA script should be set up.

NOTE: ADD YOUR SCRIPT'S DOCUMENTATION HERE (what, why, include literature references)
"""

# import cea.bigmacc.bigmacc_util as util
import cea.resources.radiation_daysim.radiation_main
# import os
# import cea.config
# import cea.inputlocator
# import cea.demand.demand_main
# import cea.resources.radiation_daysim.radiation_main
# import cea.bigmacc.copy_results
# import cea.datamanagement.archetypes_mapper
# # import cea.bigmacc.bigmacc_util as bigmacc_util
# import cea.bigmacc.create_rule_dataframe as createdf
# import numpy as np
# import itertools
# import distutils
# from distutils import dir_util
# import shutil

__author__ = "Justin McCarty"
__copyright__ = ""
__credits__ = ["Justin McCarty"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = ""
__email__ = ""
__status__ = ""

#
# def order_key_list(run_list, key_list):
#     no_run_rad_list = list(set(key_list) - set(run_list))
#     final_list = list()
#     final_list.extend(run_list)
#     final_list.extend(no_run_rad_list)
#     return final_list
#
#
# def run(config):
#     locator = cea.inputlocator.InputLocator(config.scenario)
#     i = 'testnite'
#
#     inputs_path = os.path.join(config.general.project, i, 'inputs')
#     outputs_path = os.path.join(config.general.project, i, 'outputs')
#
#     distutils.dir_util.copy_tree(locator.get_data_results_folder(), outputs_path)
#     distutils.dir_util.copy_tree(locator.get_input_folder(), inputs_path)
#

def main(n):
    # util.print_test(n)
    print(n)

if __name__ == '__main__':
    # main(cea.config.Configuration())
    main(3)
