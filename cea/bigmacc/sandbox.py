"""
The BIGMACC script.
"""

import os
import pandas as pd
import time
import logging

logging.getLogger('numba').setLevel(logging.WARNING)
import shutil
import cea.utilities.parallel
import cea.config
import cea.utilities
import cea.inputlocator
import cea.demand.demand_main
import cea.resources.radiation_daysim.radiation_main
import cea.bigmacc.bigmacc_rules
import cea.datamanagement.archetypes_mapper
import cea.datamanagement.data_initializer
import cea.analysis.costs.system_costs
import cea.analysis.lca.main
from itertools import repeat

import cea.demand.schedule_maker.schedule_maker as schedule_maker
import cea.bigmacc.bigmacc_util as util
import distutils
import cea.technologies.solar.photovoltaic as photovoltaic
import cea.resources.water_body_potential as water
import cea.bigmacc.netcdf_writer as netcdf_writer
from distutils import dir_util

__author__ = "Justin McCarty"
__copyright__ = ""
__credits__ = ["Justin McCarty"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = ""
__email__ = ""
__status__ = ""





def rewrite_to_csv(bldg,locator):
    """
    Used to rewrite the annual results per building after calculating
    the district heating supply.
    """

    df_ann = pd.read_csv(locator.get_total_demand('csv'), index_col='Name')

    # print(' - Rewriting annual results following recalculation.')

    hourly_results = locator.get_demand_results_file(bldg, 'csv')
    df_hourly = pd.read_csv(hourly_results, index_col='DATE')
    df_ann.at[bldg, 'GRID_MWhyr'] = df_hourly['GRID_kWh'].sum() / 1000
    df_ann.at[bldg, 'E_sys_MWhyr'] = 0
    df_ann.at[bldg, 'PV_MWhyr'] = df_hourly['PV_kWh'].sum() / 1000
    df_ann.at[bldg, 'NG_hs_MWhyr'] = 5
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

    # df_ann['GRID0_kW'] = df_ann[['GRID_a0_kW', 'GRID_l0_kW', 'GRID_v0_kW', 'GRID_ve0_kW', 'GRID_data0_kW',
    #                                    'GRID_pro0_kW', 'GRID_aux0_kW', 'GRID_ww0_kW', 'GRID_hs0_kW',
    #                                    'GRID_cs0_kW', 'GRID_cdata0_kW', 'GRID_cre0_kW']].sum(axis=1)
    #
    # df_ann['E_sys0_kW'] = df_ann[['Eal0_kW', 'Ea0_kW', 'El0_kW', 'Ev0_kW', 'Eve0_kW', 'Edata0_kW',
    #                                     'Epro0_kW', 'Eaux0_kW', 'E_ww0_kW', 'E_hs0_kW', 'E_cs0_kW',
    #                                     'E_cre0_kW', 'E_cdata0_kW']].sum(axis=1)

    # df_ann.to_csv(locator.get_total_demand('csv'), index=True, float_format='%.3f', na_rep=0)
    return df_ann.loc[bldg]

def run_parallel(config):

    locator = cea.inputlocator.InputLocator(config.scenario)
    n = len(config.demand.buildings)

    df = pd.read_csv(locator.get_total_demand('csv'), index_col='Name')

    print(df['NG_hs_MWhyr'])
    calc_hourly = cea.utilities.parallel.vectorize(rewrite_to_csv, config.get_number_of_processes())

    res = calc_hourly(
        config.demand.buildings,
        repeat(locator, n))


    return print(pd.concat(res,axis=1).transpose()['NG_hs_MWhyr'])


def calc_annual(bldg,locator):
    """
    Used to rewrite the annual results per building after calculating
    the district heating supply.
    """

    df_ann = pd.read_csv(locator.get_total_demand('csv'), index_col='Name')

    # print(' - Rewriting annual results following recalculation.')

    hourly_results = locator.get_demand_results_file(bldg, 'csv')
    df_hourly = pd.read_csv(hourly_results, index_col='DATE')
    df_ann.at[bldg, 'GRID_MWhyr'] = df_hourly['GRID_kWh'].sum() / 1000
    df_ann.at[bldg, 'E_sys_MWhyr'] = 0
    df_ann.at[bldg, 'PV_MWhyr'] = df_hourly['PV_kWh'].sum() / 1000
    df_ann.at[bldg,'NG_hs_MWhyr'] = df_hourly['NG_hs_kWh'].sum() / 1000
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

    # df_ann['GRID0_kW'] = df_ann[['GRID_a0_kW', 'GRID_l0_kW', 'GRID_v0_kW', 'GRID_ve0_kW', 'GRID_data0_kW',
    #                                    'GRID_pro0_kW', 'GRID_aux0_kW', 'GRID_ww0_kW', 'GRID_hs0_kW',
    #                                    'GRID_cs0_kW', 'GRID_cdata0_kW', 'GRID_cre0_kW']].sum(axis=1)
    #
    # df_ann['E_sys0_kW'] = df_ann[['Eal0_kW', 'Ea0_kW', 'El0_kW', 'Ev0_kW', 'Eve0_kW', 'Edata0_kW',
    #                                     'Epro0_kW', 'Eaux0_kW', 'E_ww0_kW', 'E_hs0_kW', 'E_cs0_kW',
    #                                     'E_cre0_kW', 'E_cdata0_kW']].sum(axis=1)

    # df_ann.to_csv(locator.get_total_demand('csv'), index=True, float_format='%.3f', na_rep=0)
    return df_ann.loc[bldg]

def run(config):
    locator = cea.inputlocator.InputLocator(config.scenario)
    bldg_list = config.demand.buildings
    results = dict()

    for i in bldg_list:
        results[i] = calc_annual(i, locator)

    # hourly_results = locator.get_demand_results_file('B000', 'csv')
    # print(hourly_results)
    # df_hourly = pd.read_csv(hourly_results, index_col='DATE')
    # return df_hourly
    return pd.DataFrame.from_dict(results)



if __name__ == '__main__':
   t1 = time.perf_counter()
   res = run_parallel(cea.config.Configuration())
   time_end = time.perf_counter() - t1
   print(time_end)
