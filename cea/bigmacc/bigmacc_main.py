"""
The BIGMACC script.
"""

import logging
import os
import time
import pandas as pd

logging.getLogger('numba').setLevel(logging.WARNING)
import cea.config
import cea.utilities
import cea.inputlocator
import cea.demand.demand_main
import cea.resources.radiation_daysim.radiation_main
import cea.bigmacc.bigmacc_rules
import cea.bigmacc.wesbrook_DH
import cea.datamanagement.archetypes_mapper
import cea.datamanagement.data_initializer
import cea.analysis.costs.system_costs
import cea.analysis.lca.main
import cea.bigmacc.bigmacc_util as util
import cea.bigmacc.sandbox
import cea.bigmacc.bigmacc_operations as bigmacc
import cea.bigmacc.netcdf_writer as netcdf_writer

__author__ = "Justin McCarty"
__copyright__ = ""
__credits__ = ["Justin McCarty"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = ""
__email__ = ""
__status__ = ""


def main(config):
    print('STARTING UP THE BIGMACC SCRIPT')
    cea.datamanagement.data_initializer.main(config)
    key_list = util.generate_key_list(config)

    # look for special outputs path, make if not there
    bigmacc_outputs_path = os.path.join(config.bigmacc.data, config.general.parent, 'bigmacc_out', config.bigmacc.round)
    if os.path.exists(bigmacc_outputs_path):
        pass
    else:
        os.mkdir(bigmacc_outputs_path)

    # look for logger file, make if not there
    if os.path.exists(os.path.join(bigmacc_outputs_path, 'logger.csv')):
        pass
    else:
        initialdf = pd.DataFrame(columns=['Experiments', 'Completed', 'Experiment Time', 'Unique Radiation'])
        initialdf.to_csv(os.path.join(bigmacc_outputs_path, 'logger.csv'))

    # enter the iteration loop
    for key in key_list:
        config.bigmacc.key = key
        print(config.bigmacc.key)
        try:

            # cea.bigmacc.sandbox.sandbox_run(config)
            if config.bigmacc.rerun != True:
                t1 = time.perf_counter()
                bigmacc.run(config)
                time_end = time.perf_counter() - t1
                print('Completed iteration: %d.2 seconds' % time_end)
            else:
                t1 = time.perf_counter()
                bigmacc.rerun(config)
                time_end = time.perf_counter() - t1
                print('Completed iteration: %d.2 seconds' % time_end)
        except:
            print(f'THERE WAS AN ERROR IN {key}.')
            error_path = os.path.join(bigmacc_outputs_path, 'error_logger.csv')

            if os.path.exists(error_path):
                pass
            else:
                initialdf = pd.DataFrame(columns=['Experiment'])
                initialdf.to_csv(error_path)
            error_df = pd.read_csv(error_path, index_col='Unnamed: 0')
            error_df = error_df.append(pd.DataFrame({'Experiments': 'exp_{}'.format(key)}))
            error_df.to_csv(error_path)
            error_df.to_csv(r"C:\Users\justi\Desktop\error_log_backup.csv")

    print('Writing the whole scenario netcdf.')
    netcdf_writer.main(config, time='whole')

    print('Simulations completed. Move to next scenario.')


if __name__ == '__main__':
    main(cea.config.Configuration())
