"""
Wesbrook has a DH system fed first by heat pumps using waste and alst by NG peaking boilers. This script takes the
demand calculated by the CEA and reinterprets it for this system, outputting the results directly into the CEA
demand files.
"""

import pandas as pd
import logging
logging.getLogger('numba').setLevel(logging.WARNING)
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
    triumf_max = [5, 3.5, 5, 9, 9, 9.5, 11, 10.5, 9.5, 9, 8, 6.5]
    hp_max = [10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10]
    district = ((557900 + 75900) / 1078800)
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


def recalc_DH(config):
    # TODO rewrite so the district heat and district hot water can run independentely
    locator = cea.inputlocator.InputLocator(config.scenario)
    on_DH_hs, on_DH_dhw = district_buildings(locator)

    while (len(on_DH_hs) == 0 or len(on_DH_dhw) == 0):
        print('wrong')
        break

    heat_df = pd.DataFrame()
    print(' - - - Gathering space heating...')
    for bldg in on_DH_hs:
        heat_df = heat_df.append(demand_source(locator, bldg, 'Qhs_sys_kWh'))
    heat_df['Name'] = heat_df.index

    dhw_df = pd.DataFrame()
    print(' - - - Gathering DHW...')
    for bldg in on_DH_dhw:
        dhw_df = dhw_df.append(demand_source(locator, bldg, 'Qww_sys_kWh'))
    dhw_df['Name'] = dhw_df.index

    demand_df = pd.concat([heat_df, dhw_df], ignore_index=True).groupby(['Name'], as_index=False).sum()
    demand_df = demand_df.set_index(demand_df['Name'], drop=True)
    del demand_df['Name']
    demand_df.loc["total"] = demand_df.sum()

    heat_df.loc["total"] = heat_df.sum()
    del heat_df['Name']
    dhw_df.loc["total"] = dhw_df.sum()
    del dhw_df['Name']

    def calc_share(demand, total):
        return demand / total
    print(' - - - Calculating share of district heat load...')

    heat_df_share = heat_df.apply(lambda x: calc_share(x, heat_df.loc['total']), axis=1)
    dhw_df_share = dhw_df.apply(lambda x: calc_share(x, dhw_df.loc['total']), axis=1)

    demand_DH_heat = pd.DataFrame(breakup_use(heat_df, config))
    demand_DH_dhw = pd.DataFrame(breakup_use(dhw_df, config))

    demand_DH_heat = calc_district_demand(demand_DH_heat)
    demand_DH_dhw = calc_district_demand(demand_DH_dhw)

    hp_dhw = demand_DH_dhw['hp_source_demand'].reset_index(drop=True).transpose() * dhw_df_share
    hp_heat = demand_DH_heat['hp_source_demand'].reset_index(drop=True).transpose() * heat_df_share

    ng_dhw = demand_DH_dhw['ng_source_demand'].reset_index(drop=True).transpose() * dhw_df_share
    ng_heat = demand_DH_heat['ng_source_demand'].reset_index(drop=True).transpose() * heat_df_share

    all_bldgs = on_DH_hs + list(set(on_DH_dhw) - set(on_DH_hs))
    if on_DH_hs == on_DH_dhw:
        print(' - - - Changing results for all bldgs...')
        for bldg in all_bldgs:
            # open bldg demand file and replace _ww_kWh with following
            hourly_results = locator.get_demand_results_file(bldg, 'csv')
            df_demand = pd.read_csv(hourly_results)
            df_demand['GRID_hs_kWh'] = hp_heat.loc[bldg]
            df_demand['E_hs_kWh'] = hp_heat.loc[bldg]
            df_demand['NG_hs_kWh'] = ng_heat.loc[bldg]
            df_demand['DH_hs_kWh'] = 0

            df_demand['GRID_ww_kWh'] = hp_dhw.loc[bldg]
            df_demand['E_ww_kWh'] = ng_heat.loc[bldg]
            df_demand['NG_ww_kWh'] = ng_dhw.loc[bldg]
            df_demand['DH_ww_kWh'] = 0

            df_demand['GRID_kWh'] = df_demand[['GRID_a_kWh', 'GRID_l_kWh', 'GRID_v_kWh', 'GRID_ve_kWh','GRID_data_kWh',
                                               'GRID_pro_kWh', 'GRID_aux_kWh', 'GRID_ww_kWh','GRID_hs_kWh',
                                               'GRID_cs_kWh', 'GRID_cdata_kWh', 'GRID_cre_kWh']].sum(axis=1)

            df_demand['E_sys_kWh'] = df_demand[['Eal_kWh', 'Ea_kWh', 'El_kWh', 'Ev_kWh', 'Eve_kWh', 'Edata_kWh',
                                                'Epro_kWh', 'Eaux_kWh', 'E_ww_kWh', 'E_hs_kWh', 'E_cs_kWh',
                                                'E_cre_kWh', 'E_cdata_kWh']].sum(axis=1)
            df_demand.to_csv(hourly_results)

    else:
        for bldg in on_DH_hs:
            # open bldg demand file and replace _ww_kWh with following
            print(' - - - Resetting results for all district heat buildings...')
            hourly_results = locator.get_demand_results_file(bldg, 'csv')
            df_demand = pd.read_csv(hourly_results)
            df_demand['GRID_hs_kWh'] = hp_heat.loc[bldg]
            df_demand['E_hs_kWh'] = hp_heat.loc[bldg]
            df_demand['NG_hs_kWh'] = ng_heat.loc[bldg]
            df_demand['DH_hs_kWh'] = 0

            df_demand.to_csv(hourly_results)

        for bldg in on_DH_dhw:
            # open bldg demand file and replace _ww_kWh with following
            print(' - - - Resetting results for district hot water bldgs...')
            hourly_results = locator.get_demand_results_file(bldg, 'csv')
            df_demand = pd.read_csv(hourly_results)
            df_demand['GRID_ww_kWh'] = hp_dhw.loc[bldg]
            df_demand['E_ww_kWh'] = hp_dhw.loc[bldg]
            df_demand['NG_ww_kWh'] = ng_dhw.loc[bldg]
            df_demand['DH_ww_kWh'] = 0
            df_demand.to_csv(hourly_results)

        for bldg in all_bldgs:
            hourly_results = locator.get_demand_results_file(bldg, 'csv')
            df_demand = pd.read_csv(hourly_results)
            df_demand['GRID_kWh'] = df_demand[['GRID_a_kWh','GRID_l_kWh','GRID_v_kWh','GRID_ve_kWh','GRID_data_kWh',
                                               'GRID_pro_kWh','GRID_aux_kWh','GRID_ww_kWh','GRID_hs_kWh',
                                               'GRID_cs_kWh','GRID_cdata_kWh','GRID_cre_kWh']].sum(axis=1)

            df_demand['E_sys_kWh'] = df_demand[['Eal_kWh', 'Ea_kWh', 'El_kWh', 'Ev_kWh', 'Eve_kWh', 'Edata_kWh',
                                                'Epro_kWh', 'Eaux_kWh', 'E_ww_kWh', 'E_hs_kWh', 'E_cs_kWh',
                                                'E_cre_kWh', 'E_cdata_kWh']].sum(axis=1)
            df_demand.to_csv(hourly_results)
    return print(' - District heating recalculated!')


def rewrite_to_csv(config):
    """
    Used to rewrite the annual results per building after calculating
    the district heating supply.
    """
    locator = cea.inputlocator.InputLocator(config.scenario)
    df_ann = pd.read_csv(locator.get_total_demand('csv'), index_col='Name')

    for bldg in df_ann.index.to_list():
        hourly_results = locator.get_demand_results_file(bldg, 'csv')
        df_hourly = pd.read_csv(hourly_results, index_col='DATE')
        df_ann.loc[bldg]['GRID_MWhyr'] = df_hourly['GRID_kWh'].sum() / 1000
        df_ann.loc[bldg]['GRID_MWhyr'] = df_hourly['GRID_kWh'].sum() / 1000
        df_ann.loc[bldg]['E_sys_MWhyr'] = df_hourly['E_sys_kWh'].sum() / 1000
        df_ann.loc[bldg]['PV_MWhyr'] = df_hourly['PV_kWh'].sum() / 1000
        df_ann.loc[bldg]['NG_hs_MWhyr'] = df_hourly['NG_hs_kWh'].sum() / 1000
        df_ann.loc[bldg]['NG_ww_MWhyr'] = df_hourly['NG_ww_kWh'].sum() / 1000
        df_ann.loc[bldg]['GRID_hs_MWhyr'] = df_hourly['GRID_hs_kWh'].sum() / 1000
        df_ann.loc[bldg]['GRID_ww_MWhyr'] = df_hourly['GRID_ww_kWh'].sum() / 1000
        df_ann.loc[bldg]['E_hs_MWhyr'] = df_hourly['E_hs_kWh'].sum() / 1000
        df_ann.loc[bldg]['E_ww_MWhyr'] = df_hourly['E_ww_kWh'].sum() / 1000

        df_ann.loc[bldg]['DH_hs_MWhyr'] = 0
        df_ann.loc[bldg]['DH_ww_MWhyr'] = 0
        df_ann.loc[bldg]['DH_hs0_kW'] = 0
        df_ann.loc[bldg]['DH_ww0_kW'] = 0

        df_ann.loc[bldg]['GRID_hs0_kW'] = df_hourly['GRID_hs_kWh'].max()
        df_ann.loc[bldg]['E_hs0_kW'] = df_hourly['E_hs_kWh'].max()
        df_ann.loc[bldg]['NG_hs0_kW'] = df_hourly['NG_hs_kWh'].max()
        df_ann.loc[bldg]['GRID_ww0_kW'] = df_hourly['GRID_ww_kWh'].max()
        df_ann.loc[bldg]['E_ww0_kW'] = df_hourly['E_ww_kWh'].max()
        df_ann.loc[bldg]['NG_ww0_kW'] = df_hourly['NG_ww_kWh'].max()

    df_ann['GRID0_kW'] = df_ann[['GRID_a0_kW', 'GRID_l0_kW', 'GRID_v0_kW', 'GRID_ve0_kW', 'GRID_data0_kW',
                                       'GRID_pro0_kW', 'GRID_aux0_kW', 'GRID_ww0_kW', 'GRID_hs0_kW',
                                       'GRID_cs0_kW', 'GRID_cdata0_kW', 'GRID_cre0_kW']].sum(axis=1)

    df_ann['E_sys0_kW'] = df_ann[['Eal0_kW', 'Ea0_kW', 'El0_kW', 'Ev0_kW', 'Eve0_kW', 'Edata0_kW',
                                        'Epro0_kW', 'Eaux0_kW', 'E_ww0_kW', 'E_hs0_kW', 'E_cs0_kW',
                                        'E_cre0_kW', 'E_cdata0_kW']].sum(axis=1)

    df_ann.to_csv(locator.get_total_demand('csv'), index=True, float_format='%.3f', na_rep=0)
    return print(' - Annual results rewritten!')

def main(config):
    recalc_DH(config)
    rewrite_to_csv(config)
    return print(' - District heating dealt with!')

if __name__ == '__main__':
    main(cea.config.Configuration())