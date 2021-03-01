"""
General utilities for the bigmacc project.
"""

import os
import zipfile
import itertools
import shutil
import cea.inputlocator
import pandas as pd
import numpy as np
import time
import cea.config
from itertools import repeat
import cea.utilities.parallel


__author__ = "Justin McCarty"
__copyright__ = ""
__credits__ = ["Justin McCarty"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = ""
__email__ = ""
__status__ = ""


def generate_key_list(config):
    # https://stackoverflow.com/questions/14931769/how-to-get-all-combination-of-n-binary-value
    key_list = []
    elements = [list(i) for i in itertools.product([0, 1], repeat=config.bigmacc.strategies)]
    for key in elements:
        result = ''.join(str(i) for i in key)
        key_list.append(result)

    rad_list = config.bigmacc.runradiation
    shorter_list = [x for x in key_list if x not in rad_list]
    rad_list.extend(shorter_list)
    return rad_list


def change_key(key):
    s = list(key)
    s[0] = '0'
    s[4] = '0'
    s[5] = '0'
    s[6] = '0'
    return "".join(s)

def unique_PV(config):
    rad_list = config.bigmacc.runradation

    pv_list = []
    for key in rad_list:
        keys = [int(x) for x in str(key)]
        if keys[7]==0:
            pass
        else:
            pv_list.append(key)



def create_rad_subs(config):
    all_keys = generate_key_list(config)

    # create dicts for each unique sets of rad files
    main_dict = dict()
    for i in config.bigmacc.runradiation:
        main_dict[i] = []

    # add the keys that need to be run for the main rad file to that rad file
    for key in all_keys:
        member = change_key(key)
        main_dict[member].append(key)

    # join dicts into one list
    main_list = []
    for k in main_dict.keys():
        main_list = main_list + main_dict[k]
    return main_list


def check_rad_files_ready(config, key):
    if key in config.bigmacc.runradiation:
        return False
    else:
        return True


def print_test(item):
    print(item)
    return item

def get_columns(config,type=None):
    locator = cea.inputlocator.InputLocator(config.scenario)
    if type=='hourly_demand':
        cols = pd.read_csv(locator.get_hourly_demand_columns(config.bigmacc.data))
        return cols.columns.tolist()
    elif type == 'ann_demand':
        cols = pd.read_csv(locator.get_annual_demand_columns(config.bigmacc.data))
        return cols.columns.tolist()
    else:
        return print('Specify type as hourly_demand or annual_demand')



def make_archive(source, destination):
    base = os.path.basename(destination)
    name = base.split('.')[0]
    format = base.split('.')[1]
    archive_from = os.path.dirname(source)
    archive_to = os.path.basename(source.strip(os.sep))
    # print(source, destination, archive_from, archive_to)
    shutil.make_archive(name, format, archive_from, archive_to)
    shutil.move('%s.%s' % (name, format), destination)


def un_zip(zipped_loc):
    with zipfile.ZipFile(os.path.join(zipped_loc + ".zip"), "r") as zip_ref:
        zip_ref.extractall(os.path.join(zipped_loc))


def get_key(df):
    key = df['experiments']
    integer = str(key.split("_")[1])
    return integer


def process_pv(config,bldg,locator):
    pv_bldg = pd.read_csv(locator.PV_results(bldg))
    hourly_results = locator.get_demand_results_file(bldg, format='csv')
    df_demand = pd.read_csv(hourly_results)
    df_demand['PV_kWh'] = 0
    df_demand['PV_kWh'] = pv_bldg['E_PV_gen_kWh']
    df_demand['GRID_kWh'] = df_demand[['GRID_a_kWh', 'GRID_l_kWh', 'GRID_v_kWh', 'GRID_ve_kWh', 'GRID_data_kWh',
                                       'GRID_pro_kWh', 'GRID_aux_kWh', 'GRID_ww_kWh', 'GRID_hs_kWh',
                                       'GRID_cs_kWh', 'GRID_cdata_kWh', 'GRID_cre_kWh']].sum(axis=1)
    df_demand['GRID_kWh'] = np.clip(df_demand['GRID_kWh'] - df_demand['PV_kWh'], 0, None)

    df_demand.fillna(0).to_csv(hourly_results,
                               columns=get_columns(config,type='hourly_demand'),
                               index=False)
    return


def write_pv_to_demand_multi(config):
    locator = cea.inputlocator.InputLocator(config.scenario)
    pv_total = pd.read_csv(locator.PV_total_buildings(), index_col='Name')

    bldg_list = pv_total.index.to_list()

    n = len(bldg_list)
    calc_hourly = cea.utilities.parallel.vectorize(process_pv, config.get_number_of_processes())
    calc_hourly(
        repeat(config, n),
        bldg_list,
        repeat(locator, n))

    # write total to file
    return print(' - PV results added them to the demand file.')


def rewrite_annual_demand(config):
    """
    Used to rewrite the annual results per building after calculating
    the district heating supply and the PV supply.
    """
    locator = cea.inputlocator.InputLocator(config.scenario)
    df_ann = pd.read_csv(locator.get_total_demand('csv'),
                         index_col='Name')
    print(' - Rewriting annual results following recalculation.')

    for bldg in df_ann.index.to_list():
        hourly_results = locator.get_demand_results_file(bldg, 'csv')
        df_hourly = pd.read_csv(hourly_results, index_col='DATE')
        df_ann.at[bldg, 'GRID_MWhyr'] = df_hourly['GRID_kWh'].sum() / 1000
        df_ann.at[bldg, 'E_sys_MWhyr'] = df_hourly['E_sys_kWh'].sum() / 1000
        df_ann.at[bldg, 'PV_MWhyr'] = df_hourly['PV_kWh'].sum() / 1000
        df_ann.at[bldg, 'NG_hs_MWhyr'] = df_hourly['NG_hs_kWh'].sum() / 1000
        df_ann.at[bldg, 'NG_ww_MWhyr'] = df_hourly['NG_ww_kWh'].sum() / 1000
        df_ann.at[bldg, 'GRID_hs_MWhyr'] = df_hourly['GRID_hs_kWh'].sum() / 1000
        df_ann.at[bldg, 'GRID_ww_MWhyr'] = df_hourly['GRID_ww_kWh'].sum() / 1000
        df_ann.at[bldg, 'E_hs_MWhyr'] = df_hourly['E_hs_kWh'].sum() / 1000
        df_ann.at[bldg, 'E_ww_MWhyr'] = df_hourly['E_ww_kWh'].sum() / 1000

        df_ann.at[bldg, 'DH_hs_MWhyr'] = 0
        df_ann.at[bldg, 'DH_ww_MWhyr'] = 0
        df_ann.at[bldg, 'DH_hs0_kW'] = 0
        df_ann.at[bldg, 'DH_ww0_kW'] = 0

        df_ann.at[bldg, 'GRID_hs0_kW'] = df_hourly['GRID_hs_kWh'].max()
        df_ann.at[bldg, 'E_hs0_kW'] = df_hourly['E_hs_kWh'].max()
        df_ann.at[bldg, 'NG_hs0_kW'] = df_hourly['NG_hs_kWh'].max()
        df_ann.at[bldg, 'GRID_ww0_kW'] = df_hourly['GRID_ww_kWh'].max()
        df_ann.at[bldg, 'E_ww0_kW'] = df_hourly['E_ww_kWh'].max()
        df_ann.at[bldg, 'NG_ww0_kW'] = df_hourly['NG_ww_kWh'].max()

    df_ann['GRID0_kW'] = df_ann[['GRID_a0_kW', 'GRID_l0_kW', 'GRID_v0_kW', 'GRID_ve0_kW', 'GRID_data0_kW',
                                 'GRID_pro0_kW', 'GRID_aux0_kW', 'GRID_ww0_kW', 'GRID_hs0_kW',
                                 'GRID_cs0_kW', 'GRID_cdata0_kW', 'GRID_cre0_kW']].sum(axis=1)

    df_ann['E_sys0_kW'] = df_ann[['Eal0_kW', 'Ea0_kW', 'El0_kW', 'Ev0_kW', 'Eve0_kW', 'Edata0_kW',
                                  'Epro0_kW', 'Eaux0_kW', 'E_ww0_kW', 'E_hs0_kW', 'E_cs0_kW',
                                  'E_cre0_kW', 'E_cdata0_kW']].sum(axis=1)

    df_ann.to_csv(locator.get_total_demand('csv'),
                  columns=get_columns(config,type='annual_demand'),
                  index=True,
                  float_format='%.3f', na_rep=0)
    return print(' - Annual results rewritten!')

def main(config):
    write_pv_to_demand_multi(config)
    rewrite_annual_demand(config)

if __name__ == '__main__':
   t1 = time.perf_counter()
   main(cea.config.Configuration())
   time_end = time.perf_counter() - t1
   print(time_end)