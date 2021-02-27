"""
Wesbrook has a DH system fed first by heat pumps using waste and alst by NG peaking boilers. This script takes the
demand calculated by the CEA and reinterprets it for this system, outputting the results directly into the CEA
demand files.
"""

import pandas as pd
import time
import logging

logging.getLogger('numba').setLevel(logging.WARNING)
from itertools import repeat
import cea.utilities.parallel
import cea.config
import cea.utilities
import cea.inputlocator
import cea.bigmacc.bigmacc_util as util
import cea.demand.demand_main
import cea.resources.radiation_daysim.radiation_main
import cea.bigmacc.bigmacc_rules
import cea.datamanagement.archetypes_mapper
import cea.datamanagement.data_initializer
import cea.analysis.costs.system_costs
import cea.analysis.lca.main
import cea.utilities.dbf

__author__ = "Justin McCarty"
__copyright__ = ""
__credits__ = ["Justin McCarty"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = ""
__email__ = ""
__status__ = ""


def demand_source(locator, bldg, resource):
    # Qhs_sys_kWh, Qww_sys_kWh
    hourly_results = locator.get_demand_results_file(bldg, 'csv')
    df_demand = pd.read_csv(hourly_results)
    return df_demand[resource].rename(bldg)


def breakup_use(df, config):
    df = df.loc["total"]
    df = df.transpose()
    df.index = pd.date_range(start=f'1/1/{config.emissions.year_to_calculate}', periods=8760, freq='H')
    return df


def district_buildings(locator):
    supply_hs_df = pd.read_excel(locator.get_database_supply_assemblies(), sheet_name='HEATING')
    supply_dhw_df = pd.read_excel(locator.get_database_supply_assemblies(), sheet_name='HOT_WATER')
    hs_codes = supply_hs_df[supply_hs_df['feedstock'] == 'DISTRICT']['code'].to_list()
    dhw_codes = supply_dhw_df[supply_dhw_df['feedstock'] == 'DISTRICT']['code'].to_list()
    supply_df = cea.utilities.dbf.dbf_to_dataframe(locator.get_building_supply(), index='Name')

    def get_build_list(codes, supply_type):
        if supply_type in codes:
            return 'Yes'
        else:
            return 'No'

    supply_df['hs_keep'] = supply_df.apply(lambda x: get_build_list(hs_codes, x['type_hs']), axis=1)
    on_DH_hs = supply_df[supply_df['hs_keep'] == 'Yes']['Name'].to_list()

    supply_df['dhw_keep'] = supply_df.apply(lambda x: get_build_list(dhw_codes, x['type_dhw']), axis=1)
    on_DH_dhw = supply_df[supply_df['dhw_keep'] == 'Yes']['Name'].to_list()

    return on_DH_hs, on_DH_dhw


def ng(total, hplim):
    if total > hplim:
        return total - hplim
    else:
        return 0


def hp(total, ng_demand):
    if ng_demand > 0:
        return total - ng_demand
    else:
        return total


def hp1(hp_demand, trlim):
    if hp_demand >= trlim:
        return trlim
    else:
        return hp_demand


def hp2(hp_demand, hp1_demand, trlim):
    if hp1_demand < trlim:
        return 0
    else:
        return hp_demand - trlim


def calc_district_demand(df):
    months = list(range(1, 13, 1))
    triumf_max = [5, 3.5, 5, 9, 9, 9.5, 11, 10.5, 9.5, 9, 8, 6.5]  # monthly triumf output
    hp_max = [10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10]  # monthly HP capacities
    district = ((557900 + 75900) / 1078800)  # calc the share of the wesbrook and srn GFA as a fraction of whole
    triumf_district = [round(i * district * 1000, 2) for i in triumf_max]
    hp_district = [round(i * district * 1000, 2) for i in hp_max]
    triumf_limit = dict(zip(months, triumf_district))
    hp_limit = dict(zip(months, hp_district))

    df['tr_limit'] = df.index.month.map(triumf_limit)
    df['hp_limit'] = df.index.month.map(hp_limit)

    df['ng_demand'] = df.apply(lambda x: ng(x['total'], x['hp_limit']), axis=1)
    df['hp_demand'] = df.apply(lambda x: hp(x['total'], x['ng_demand']), axis=1)
    df['hp1_demand'] = df.apply(lambda x: hp1(x['hp_demand'], x['tr_limit']), axis=1)
    df['hp2_demand'] = df.apply(lambda x: hp2(x['hp_demand'], x['hp1_demand'], x['tr_limit']), axis=1)

    df['ng_source_demand'] = df['ng_demand'] / 0.95
    df['hp1_source_demand'] = df['hp1_demand'] / 3.4
    df['hp2_source_demand'] = df['hp2_demand'] / 2.7
    df['hp_source_demand'] = df['hp1_source_demand'] + df['hp2_source_demand']
    return df[['ng_source_demand', 'hp_source_demand']]


def write_ng_hs(config, loc, bl, hp_h, hp_ww, ng_h, ng_ww):
    hourly_results = loc.get_demand_results_file(bl, 'csv')
    df_demand = pd.read_csv(hourly_results)
    df_demand['GRID_hs_kWh'] = hp_h.loc[bl]
    df_demand['E_hs_kWh'] = hp_h.loc[bl]
    df_demand['NG_hs_kWh'] = ng_h.loc[bl]
    df_demand['DH_hs_kWh'] = 0

    df_demand['GRID_ww_kWh'] = hp_ww.loc[bl]
    df_demand['E_ww_kWh'] = hp_ww.loc[bl]
    df_demand['NG_ww_kWh'] = ng_ww.loc[bl]
    df_demand['DH_ww_kWh'] = 0

    df_demand['GRID_kWh'] = df_demand[['GRID_a_kWh', 'GRID_l_kWh', 'GRID_v_kWh', 'GRID_ve_kWh', 'GRID_data_kWh',
                                       'GRID_pro_kWh', 'GRID_aux_kWh', 'GRID_ww_kWh', 'GRID_hs_kWh',
                                       'GRID_cs_kWh', 'GRID_cdata_kWh', 'GRID_cre_kWh']].sum(axis=1)

    df_demand['E_sys_kWh'] = df_demand[['Eal_kWh', 'Ea_kWh', 'El_kWh', 'Ev_kWh', 'Eve_kWh', 'Edata_kWh',
                                        'Epro_kWh', 'Eaux_kWh', 'E_ww_kWh', 'E_hs_kWh', 'E_cs_kWh',
                                        'E_cre_kWh', 'E_cdata_kWh']].sum(axis=1)
    df_demand.fillna(0).to_csv(hourly_results,
                               columns=util.get_columns(config, type='hourly_demand'),
                               index=False)
    return


def write_hs(config, loc, bl, hp_h, ng_h):
    # open bldg demand file and replace _ww_kWh with following
    print(' - - - Resetting results for all district heat buildings...')
    hourly_results = loc.get_demand_results_file(bl, 'csv')
    df_demand = pd.read_csv(hourly_results)
    df_demand['GRID_hs_kWh'] = hp_h.loc[bl]
    df_demand['E_hs_kWh'] = hp_h.loc[bl]
    df_demand['NG_hs_kWh'] = ng_h.loc[bl]
    df_demand['DH_hs_kWh'] = 0

    df_demand.fillna(0).to_csv(hourly_results,
                               columns=util.get_columns(config, type='hourly_demand'),
                               index=False)
    return


def write_ng(config, loc, bl, hp_ww, ng_ww):
    # open bldg demand file and replace _ww_kWh with following
    print(' - - - Resetting results for district hot water bldgs...')
    hourly_results = loc.get_demand_results_file(bl, 'csv')
    df_demand = pd.read_csv(hourly_results)
    df_demand['GRID_ww_kWh'] = hp_ww.loc[bl]
    df_demand['E_ww_kWh'] = hp_ww.loc[bl]
    df_demand['NG_ww_kWh'] = ng_ww.loc[bl]
    df_demand['DH_ww_kWh'] = 0
    df_demand.fillna(0).to_csv(hourly_results,
                               columns=util.get_columns(config, type='hourly_demand'),
                               index=False)
    return


def write_both(config, loc, bl):
    hourly_results = loc.get_demand_results_file(bl, 'csv')
    df_demand = pd.read_csv(hourly_results)
    df_demand['GRID_kWh'] = df_demand[['GRID_a_kWh', 'GRID_l_kWh', 'GRID_v_kWh', 'GRID_ve_kWh', 'GRID_data_kWh',
                                       'GRID_pro_kWh', 'GRID_aux_kWh', 'GRID_ww_kWh', 'GRID_hs_kWh',
                                       'GRID_cs_kWh', 'GRID_cdata_kWh', 'GRID_cre_kWh']].sum(axis=1)

    df_demand['E_sys_kWh'] = df_demand[['Eal_kWh', 'Ea_kWh', 'El_kWh', 'Ev_kWh', 'Eve_kWh', 'Edata_kWh',
                                        'Epro_kWh', 'Eaux_kWh', 'E_ww_kWh', 'E_hs_kWh', 'E_cs_kWh',
                                        'E_cre_kWh', 'E_cdata_kWh']].sum(axis=1)
    df_demand.fillna(0).to_csv(hourly_results,
                               columns=util.get_columns(config, type='hourly_demand'),
                               index=False)
    return

def recalc_DH_pt1(config):
    # TODO rewrite so the district heat and district hot water can run independentely
    locator = cea.inputlocator.InputLocator(config.scenario)
    on_DH_hs, on_DH_dhw = district_buildings(locator)

    while (len(on_DH_hs) == 0 or len(on_DH_dhw) == 0):
        print(' - - - No buildings in district heat.')
        break

    heat_df = pd.DataFrame()
    print(' - - - Gathering space heating...')
    for bldg in on_DH_hs:
        heat_df = heat_df.append(demand_source(locator, bldg, 'Qhs_sys_kWh'))
    heat_df['Name'] = heat_df.index
    print(' - - Done')

    dhw_df = pd.DataFrame()
    print(' - - - Gathering DHW...')
    for bldg in on_DH_dhw:
        dhw_df = dhw_df.append(demand_source(locator, bldg, 'Qww_sys_kWh'))
    dhw_df['Name'] = dhw_df.index
    print(' - - Done')

    return heat_df, dhw_df


def recalc_DH_pt2(heat_df, dhw_df, config):
    print(' - - - Calculating share of district heat load...')

    demand_df = pd.concat([heat_df, dhw_df], ignore_index=True).groupby(['Name'], as_index=False).sum()
    demand_df = demand_df.set_index(demand_df['Name'], drop=True)
    del demand_df['Name']
    demand_df.loc["total"] = demand_df.sum()

    heat_df.loc["total"] = heat_df.sum()
    del heat_df['Name']
    dhw_df.loc["total"] = dhw_df.sum()
    del dhw_df['Name']

    heat_df_share = heat_df.divide(demand_df.loc['total'])
    dhw_df_share = dhw_df.divide(demand_df.loc['total'])

    heat_df_sh = heat_df_share.drop(['total'])
    dhw_df_sh = dhw_df_share.drop(['total'])

    r_df = calc_district_demand(pd.DataFrame(breakup_use(demand_df, config)))
    r_df['total'] = r_df['ng_source_demand'] + r_df['hp_source_demand']

    ng_src = pd.DataFrame(r_df.reset_index(drop=True).transpose().loc['ng_source_demand'])
    el_src = pd.DataFrame(r_df.reset_index(drop=True).transpose().loc['hp_source_demand'])

    heat_ng = heat_df_sh.transpose().mul(ng_src.values, axis=0).transpose()
    heat_el = heat_df_sh.transpose().mul(el_src.values, axis=0).transpose()

    dhw_ng = dhw_df_sh.transpose().mul(ng_src.values, axis=0).transpose()
    dhw_el = dhw_df_sh.transpose().mul(el_src.values, axis=0).transpose()

    return heat_ng, heat_el, dhw_ng, dhw_el


def recalc_DH(config):
    heat, dhw = recalc_DH_pt1(config)
    return recalc_DH_pt2(heat, dhw, config)


def write_recalc_DH(config):
    ng_heat, hp_heat, ng_dhw, hp_dhw = recalc_DH(config)
    locator = cea.inputlocator.InputLocator(config.scenario)
    on_DH_hs, on_DH_dhw = district_buildings(locator)
    all_bldgs = on_DH_hs + list(set(on_DH_dhw) - set(on_DH_hs))
    if on_DH_hs == on_DH_dhw:
        print(' - - - Changing results for all bldgs...')
        n = len(on_DH_hs)
        calc_hourly = cea.utilities.parallel.vectorize(write_ng_hs, config.get_number_of_processes())
        calc_hourly(
            repeat(config, n),
            repeat(locator, n),
            on_DH_hs,
            repeat(hp_heat, n),
            repeat(hp_dhw, n),
            repeat(ng_heat, n),
            repeat(ng_dhw, n))
    else:
        n = len(on_DH_hs)
        calc_hourly = cea.utilities.parallel.vectorize(write_hs, config.get_number_of_processes())
        calc_hourly(
            repeat(config, n),
            repeat(locator, n),
            on_DH_hs,
            repeat(hp_heat, n),
            repeat(ng_heat, n))

        n = len(on_DH_dhw)
        calc_hourly = cea.utilities.parallel.vectorize(write_ng, config.get_number_of_processes())
        calc_hourly(
            repeat(config, n),
            repeat(locator, n),
            on_DH_dhw,
            repeat(hp_dhw, n),
            repeat(ng_dhw, n))

        n = len(all_bldgs)
        calc_hourly = cea.utilities.parallel.vectorize(write_both, config.get_number_of_processes())
        calc_hourly(
            repeat(config, n),
            repeat(locator, n),
            all_bldgs)
    return print(' - District heating recalculated!')


def main(config):
    write_recalc_DH(config)
    return print(' - District heating dealt with!')

if __name__ == '__main__':
    t1 = time.perf_counter()
    write_recalc_DH(cea.config.Configuration())
    time_end = time.perf_counter() - t1
    print(time_end)
