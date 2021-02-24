import warnings
import os
import numpy as np
from itertools import repeat
import cea.config
import cea.inputlocator
import cea.utilities.parallel
import pandas as pd
import cea.config
import cea.utilities
import cea.inputlocator
import cea.demand.demand_main
import cea.resources.radiation_daysim.radiation_main
import cea.bigmacc.bigmacc_rules
import cea.bigmacc.bigmacc_util as util
import cea.datamanagement.archetypes_mapper
import cea.datamanagement.data_initializer
import cea.analysis.costs.system_costs
import winsound
import cea.bigmacc.netcdf_writer as netcdf_writer
import cea.analysis.lca.main

warnings.filterwarnings("ignore")


def test_process(bldg, locator):
    print(locator.get_demand_results_file(bldg, format='csv'))
    # print(bldg)

def process_hourly(bldg, locator):
    # print(bldg)
    pv_bldg = pd.read_csv(locator.PV_results(bldg))
    hourly_results = locator.get_demand_results_file(bldg, format='csv')
    df_demand = pd.read_csv(hourly_results)
    df_demand['PV_kWh'] = 0
    df_demand['PV_kWh'] = pv_bldg['E_PV_gen_kWh'].astype(float)
    df_demand['GRID_kWh'] = df_demand[['GRID_a_kWh', 'GRID_l_kWh', 'GRID_v_kWh', 'GRID_ve_kWh', 'GRID_data_kWh',
                                       'GRID_pro_kWh', 'GRID_aux_kWh', 'GRID_ww_kWh', 'GRID_hs_kWh',
                                       'GRID_cs_kWh', 'GRID_cdata_kWh', 'GRID_cre_kWh']].sum(axis=1)
    df_demand['GRID_kWh'] = np.clip(df_demand['GRID_kWh'] - df_demand['PV_kWh'], 0, None)

    df_demand.to_csv(hourly_results)
    return

def multiprocess_write_pv_hourly(config):

    # multithreading by building

    locator = cea.inputlocator.InputLocator(config.scenario)
    pv_total = pd.read_csv(locator.PV_total_buildings(), index_col='Name')
    bldg_list = pv_total.index.to_list()
    n = len(bldg_list)
    calc_hourly = cea.utilities.parallel.vectorize(process_hourly, config.get_number_of_processes())

    calc_hourly(
        bldg_list,
        repeat(locator, n))
    return print(f'Multiprocessing of hourly completed for {config.bigmacc.key}.')


def process_whole(config, key):
    demand_total_path = os.path.join(config.bigmacc.data,
                                     config.general.parent,
                                     key,
                                     'initial',
                                     'outputs',
                                     'data',
                                     'demand',
                                     'Total_demand.csv')
    demand_total = pd.read_csv(demand_total_path, index_col='Name')
    bldg_list = demand_total.index.to_list()
    print(demand_total_path)
    for bldg in bldg_list:
        hourly_demand_path = os.path.join(config.bigmacc.data,
                                     config.general.parent,
                                     key,
                                     'initial',
                                     'outputs',
                                     'data',
                                     'demand',
                                     f'{bldg}.csv')
        hourly_demand = pd.read_csv(hourly_demand_path)
        demand_total.loc[bldg]['PV_MWhyr'] = hourly_demand['PV_kWh'].sum() / 1000
        demand_total.loc[bldg]['GRID_MWhyr'] = hourly_demand['GRID_kWh'].sum() / 1000
    demand_total.to_csv(demand_total_path)
    return print(f'Multiprocessing of annual completed for {key}.')



def multiprocess_write_pv_whole(config, key_list):

    # multithreading by strategy

    calc_whole = cea.utilities.parallel.vectorize(process_whole, config.get_number_of_processes())

    n = len(key_list)
    calc_whole(
        repeat(config, n),
        key_list
        )
    return


def multiprocess_pv_main(config, type=None):
    key_list = util.create_rad_subs(config)

    if type == 'hourly':
        print('Reprocessing hourly resolution for PV results')
        pv_keys = []
        for key in key_list:
            keys = [int(x) for x in str(key)]
            if keys[7] == 1:
                print(f'Add key {key}.')
                pv_keys.append(key)
            else:
                print(f'Do not add key {key}')

        for key in pv_keys:
            config.bigmacc.key = key
            config.general.project = os.path.join(config.bigmacc.data, config.general.parent, key)
            check_path = os.path.join(config.bigmacc.data, config.general.parent,
                                      'bigmacc_out', config.bigmacc.round,
                                      f"hourly_{config.general.parent}_{config.bigmacc.key}")
            if os.path.exists(check_path):
                print(f' - Completed rewrite of PV for {key}.')
            else:
                print(' - - - - - - Move to next - - - - - - ')
                print(config.general.project)
                keys = [int(x) for x in str(key)]
                if keys[7] == 1:
                    print(' - PV use detected. Adding PV generation to demand files.')
                    multiprocess_write_pv_hourly(config)
                    cea.analysis.costs.system_costs.main(config)
                    cea.analysis.lca.main.main(config)
                    netcdf_writer.main(config, time='hourly')
                else:
                    print(' - No PV use detected.')

    elif type == 'whole':
        print('Reprocessing strategy resolution for PV results')

        pv_keys = []
        for key in key_list:
            keys = [int(x) for x in str(key)]
            if keys[7] == 1:
                print(f'Add key {key}.')
                pv_keys.append(key)
            else:
                print(f'Do not add key {key}')

        multiprocess_write_pv_whole(config, pv_keys)
        netcdf_writer.main(config, time='hourly')

    else:
        print('Specify type= hourly or whole')

    return print('Completed reprocess of PV')


if __name__ == '__main__':
    duration = 2000  # milliseconds
    freq = 440  # Hz
    multiprocess_pv_main(cea.config.Configuration(),type='hourly')
    winsound.Beep(freq, duration)
    multiprocess_pv_main(cea.config.Configuration(),type='whole')
    winsound.Beep(freq, duration)
