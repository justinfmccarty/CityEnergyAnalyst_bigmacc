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


def write_pv_to_demand(config):
    locator = cea.inputlocator.InputLocator(config.scenario)
    print(config.general.project)
    pv_total = pd.read_csv(locator.PV_total_buildings(), index_col='Name')
    demand_total = pd.read_csv(locator.get_total_demand(format='csv'), index_col='Name')

    for bldg in pv_total.index.to_list():
        print(bldg)
        pv_bldg = pd.read_csv(locator.PV_results(bldg))
        hourly_results = locator.get_demand_results_file(bldg, format='csv')
        df_demand = pd.read_csv(hourly_results)
        df_demand['PV_kWh'] = 0
        df_demand['PV_kWh'] = pv_bldg['E_PV_gen_kWh'].astype(float)
        df_demand['GRID_kWh'] = df_demand[['GRID_a_kWh', 'GRID_l_kWh', 'GRID_v_kWh', 'GRID_ve_kWh', 'GRID_data_kWh',
                                           'GRID_pro_kWh', 'GRID_aux_kWh', 'GRID_ww_kWh', 'GRID_hs_kWh',
                                           'GRID_cs_kWh', 'GRID_cdata_kWh', 'GRID_cre_kWh']].sum(axis=1)
        df_demand['GRID_kWh'] = np.clip(df_demand['GRID_kWh'] - df_demand['PV_kWh'], 0, None)
        demand_total.loc[bldg]['PV_MWhyr'] = df_demand['PV_kWh'].sum() / 1000
        demand_total.loc[bldg]['GRID_MWhyr'] = df_demand['GRID_kWh'].sum() / 1000
        df_demand.to_csv(hourly_results)
        # write bldg to file
    # write total to file
    demand_total.to_csv(locator.get_total_demand(format='csv'))
    return print(' - Took PV results and added them to the demand file.')
