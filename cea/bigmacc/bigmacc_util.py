"""
General utilities for the bigmacc project.
"""

import os
import cea.config
import cea.inputlocator
import cea.demand.demand_main
# import cea.resources.radiation_daysim.radiation_main
import cea.bigmacc.copy_results
import cea.datamanagement.archetypes_mapper
import configparser
import itertools

__author__ = "Justin McCarty"
__copyright__ = ""
__credits__ = ["Justin McCarty"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = ""
__email__ = ""
__status__ = ""


def generate_key_list(n):
    # https://stackoverflow.com/questions/14931769/how-to-get-all-combination-of-n-binary-value
    key_list = []
    elements = [list(i) for i in itertools.product([0, 1], repeat=n)]
    for key in elements:
        result = ''.join(str(i) for i in key)
        key_list.append(result)
    return key_list


def change_key(key):
    s = list(key)
    s[0] = '0'
    s[4] = '0'
    s[5] = '0'
    s[6] = '0'
    return "".join(s)

def print_test(item):
    print(item)
    return item
