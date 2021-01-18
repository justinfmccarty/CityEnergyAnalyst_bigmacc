"""
This is a template script - an example of how a CEA script should be set up.

NOTE: ADD YOUR SCRIPT'S DOCUMENTATION HERE (what, why, include literature references)
"""

# import cea.bigmacc.bigmacc_util as util
import cea.resources.radiation_daysim.radiation_main
import os
import itertools
import time
import cea.inputlocator
import cea.config
import distutils
from distutils import dir_util
import pandas as pd
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
    util.make_archive(os.path.join(config.general.scenario),
                      os.path.join(config.bigmacc.keys,  "01.zip"))
    util.un_zip(os.path.join(config.bigmacc.keys, '01'))

def copy(config):
    locator = cea.inputlocator.InputLocator(config.scenario)

    inputs_path = os.path.join(config.bigmacc.keys, '02', 'inputs')
    outputs_path = os.path.join(config.bigmacc.keys, '02', 'outputs', 'data')

    distutils.dir_util.copy_tree(locator.get_data_results_folder(), outputs_path)
    distutils.dir_util.copy_tree(locator.get_input_folder(), inputs_path)

def log(config):
    key_list = util.generate_key_list(config.bigmacc.strategies)

    initialdf = pd.DataFrame(columns=['Experiments','Completed','Experiment Time','Unique Radiation'])
    initialdf.to_csv(os.path.join(config.bigmacc.keys, 'logger.csv'))

    time_elapsed = time.perf_counter() - 1
    key_list = [0,1,2,3,4,5]
    for i in key_list:
        log_df = pd.read_csv(os.path.join(config.bigmacc.keys, 'logger.csv'),
                             index_col='Unnamed: 0')
        log_df = log_df.append(pd.DataFrame({'Experiments': 'exp_{}'.format(i),
                                             'Completed': 'True',
                                             'Experiment Time': '%d.2 seconds' % time_elapsed,
                                             'Unique Radiation': config.bigmacc.runrad}, index=[0]), ignore_index=True)
    log_df.to_csv(os.path.join(config.bigmacc.keys, 'logger.csv'))


def check(config):
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    for i in list(range(1,10)):
        print('{} one'.format(i))
        if os.path.exists(locator.get_schedule_model_folder()):
            print('{} two'.format(i))
            break
        else:
            print(i)
    print('All')


def main(config):
    print(util.generate_key_list(config))


if __name__ == '__main__':
    main(cea.config.Configuration())
