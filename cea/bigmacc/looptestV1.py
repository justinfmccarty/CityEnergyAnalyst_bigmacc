"""
This is a template script - an example of how a CEA script should be set up.

NOTE: ADD YOUR SCRIPT'S DOCUMENTATION HERE (what, why, include literature references)
"""

# import cea.bigmacc.bigmacc_util as util
import cea.resources.radiation_daysim.radiation_main
import os
import winsound
import xlsxwriter
import cea.bigmacc.netcdf_writer as netcdf_writer

import itertools
import numpy as np
import cea.analysis.costs.system_costs
import cea.analysis.lca.main
import time
import cea.inputlocator
import cea.config
import distutils
from distutils import dir_util
import pandas as pd
import cea.utilities
import cea.demand.demand_main
import cea.resources.radiation_daysim.radiation_main
import cea.bigmacc.deprecated.copy_results
import cea.datamanagement.archetypes_mapper
import zipfile
import cea.utilities.dbf

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
    config.bigmacc.copyrad = 'def'  # df['copy_rad'].values[1]
    print(1)
    print(config.bigmacc.copyrad)


def pr(config):
    util.make_archive(os.path.join(config.general.scenario),
                      os.path.join(config.bigmacc.keys, "01.zip"))
    util.un_zip(os.path.join(config.bigmacc.keys, '01'))


def copy(config):
    locator = cea.inputlocator.InputLocator(config.scenario)

    inputs_path = os.path.join(config.bigmacc.keys, '02', 'inputs')
    outputs_path = os.path.join(config.bigmacc.keys, '02', 'outputs', 'data')

    distutils.dir_util.copy_tree(locator.get_data_results_folder(), outputs_path)
    distutils.dir_util.copy_tree(locator.get_input_folder(), inputs_path)


def log(config):
    key_list = util.generate_key_list(config.bigmacc.strategies)

    initialdf = pd.DataFrame(columns=['Experiments', 'Completed', 'Experiment Time', 'Unique Radiation'])
    initialdf.to_csv(os.path.join(config.bigmacc.keys, 'logger.csv'))

    time_elapsed = time.perf_counter() - 1
    key_list = [0, 1, 2, 3, 4, 5]
    for i in key_list:
        log_df = pd.read_csv(os.path.join(config.bigmacc.keys, 'logger.csv'),
                             index_col='Unnamed: 0')
        log_df = log_df.append(pd.DataFrame({'Experiments': 'exp_{}'.format(i),
                                             'Completed': 'True',
                                             'Experiment Time': '%d.2 seconds' % time_elapsed,
                                             'Unique Radiation': config.bigmacc.runrad}, index=[0]), ignore_index=True)
    log_df.to_csv(os.path.join(config.bigmacc.keys, 'logger.csv'))


def change():
    os.chdir('F:\BIGMACC_WESBROOK\Projects')


def check():
    print(os.getcwd())


def writingexcel(config):
    rules_df = cea.bigmacc.create_rule_dataframe.main(config)
    df = rules_df[rules_df['keys'] == config.bigmacc.key]
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)

    usetype_path = locator.get_database_use_types_properties()
    usetype_IC = pd.read_excel(usetype_path, sheet_name='INDOOR_COMFORT')
    # usetype_IL = pd.read_excel(usetype_path, sheet_name='INTERNAL_LOADS')
    usetype_IC['Tcs_set_C'] = usetype_IC['Tcs_set_C'] + df['SP_cool'].values.tolist()[0]
    usetype_IC['Ths_set_C'] = usetype_IC['Ths_set_C'] + df['SP_heat'].values.tolist()[0]
    usetype_IC['Tcs_setb_C'] = usetype_IC['Tcs_setb_C'] + df['SP_cool'].values.tolist()[0]
    usetype_IC['Ths_setb_C'] = usetype_IC['Ths_setb_C'] + df['SP_heat'].values.tolist()[0]

    # Create a Pandas Excel writer using XlsxWriter as the engine.
    writer = pd.ExcelWriter(locator.get_database_use_types_properties(), engine='xlsxwriter')

    # Write each dataframe to a different worksheet.
    usetype_IC.to_excel(writer, sheet_name='INDOOR_COMFORT')
    # usetype_IL.to_excel(writer, sheet_name='INTERNAL_LOADS')
    writer.save()


def testif(config):
    # exp_01011111
    # exp_01100010

    keys3 = 1
    keys1 = 0
    if keys3 == 1:
        # check for green roof
        if keys1 == 1:  # PV+GR+PH
            print('PV+GR+PH')

            # print('Writing File')
        else:  # PV+PH
            print('PV+PH')

            # print('Writing File')
    else:
        # check for green roof
        if keys1 == 1:  # PV+GR+ST
            print('PV+GR+ST')

            # print('Writing File')
        else:  # PV+ST
            print('PV+ST')

        print('Writing File')


def write_pv_to_demand(config):
    locator = cea.inputlocator.InputLocator(config.scenario)

    pv_total = pd.read_csv(locator.PV_total_buildings(), index_col='Name')
    demand_total = pd.read_csv(locator.get_total_demand(format='csv'), index_col='Name')

    for bldg in pv_total.index.to_list()[1:8]:
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

    return print('Took PV results and added them to the demand file.')


def generate_key_list(config):
    # https://stackoverflow.com/questions/14931769/how-to-get-all-combination-of-n-binary-value
    key_list = []
    elements = [list(i) for i in itertools.product([0, 1], repeat=config.bigmacc.strategies)]
    for key in elements:
        result = ''.join(str(i) for i in key)
        key_list.append(result)

    run_rad = config.bigmacc.runradiation
    rad_list = run_rad.copy()
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

def transfer(i,des,src):

    if os.path.exists(des):
        print(f'{i} --- Directory exists.')
        pass
    else:
        print(f'{i} --- Transfer start.')
        t1 = time.perf_counter()
        shutil.copytree(src, des)
        # distutils.dir_util.copy_tree(src, des)
        time_end = time.perf_counter() - t1
        print('%d.2 seconds' % time_end)
    return (print(f'--- NEXT ---'))

def write_PV(config):
    key_list = util.create_rad_subs(config)

    done = []
    # enter the iteration loop
    for key in key_list:
        config.bigmacc.key = key
        config.general.project = os.path.join(config.bigmacc.data, config.general.parent, key)
        check_path = os.path.join(config.bigmacc.data, config.general.parent,
                                  'bigmacc_out', config.bigmacc.round,
                                  f"hourly_{config.general.parent}_{config.bigmacc.key}")
        if os.path.exists(check_path):
            print(f' - Completed rewrite of PV for {key}.')
            pass
        else:
            print(' - - - - - - Move to next - - - - - - ')
            print(config.general.project)
            keys = [int(x) for x in str(key)]
            if keys[7] == 1:
                print(' - PV use detected. Adding PV generation to demand files.')
                util.write_pv_to_demand(config)
                done.append(key)
                cea.analysis.costs.system_costs.main(config)
                cea.analysis.lca.main.main(config)
                netcdf_writer.main(config, time='hourly')
            else:
                print(' - No PV use detected.')

    rewrite_pv_path = os.path.join(config.bigmacc.data,
                                   config.general.parent,
                                   'bigmacc-out',
                                   config.bigmacc.round)
    log_df = pd.DataFrame(pd.Series(done,name='completed'))
    print(log_df)
    log_df.to_csv(os.path.join(rewrite_pv_path, 'pv_rewrite_logger.csv'))
    duration = 2000  # milliseconds
    freq = 440  # Hz
    winsound.Beep(freq, duration)

def write_test():
    path = r"C:\Users\justi\Desktop\Total_demand.csv"
    df = pd.read_csv(path,index_col='Name')
    path2 = r"C:\Users\justi\Desktop\Total_demand_alt.csv"
    df.to_csv(path2, float_format='%.3f', na_rep=0)


if __name__ == '__main__':
    write_PV(cea.config.Configuration())



