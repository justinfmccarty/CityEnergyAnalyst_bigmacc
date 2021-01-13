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
import cea.bigmacc.create_rule_dataframe as createdf
import numpy as np
import itertools

__author__ = "Justin McCarty"
__copyright__ = ""
__credits__ = ["Justin McCarty"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = ""
__email__ = ""
__status__ = ""



def order_key_list(run_list,key_list):
  no_run_rad_list = list(set(key_list) - set(run_list))
  final_list = list()
  final_list.extend(run_list)
  final_list.extend(no_run_rad_list)
  return final_list

def main(config):
    llist = order_key_list(config.bigmacc.runradiation, generate_key_list(config.bigmacc.strategies))
    print(llist[0:16])


if __name__ == '__main__':
    main(cea.config.Configuration())
