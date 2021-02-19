"""
The BIGMACC script.
"""

import os
import pandas as pd
import logging
import xarray as xr
logging.getLogger('numba').setLevel(logging.WARNING)
import cea.config
import cea.utilities
import cea.inputlocator
import cea.demand.demand_main
import cea.resources.radiation_daysim.radiation_main
import cea.bigmacc.bigmacc_rules
import cea.bigmacc.wesbrook_DH
import cea.utilities.dbf
import cea.datamanagement.archetypes_mapper
import cea.datamanagement.data_initializer
import cea.analysis.costs.system_costs
import cea.analysis.lca.main
import cea.bigmacc.bigmacc_util as util

__author__ = "Justin McCarty"
__copyright__ = ""
__credits__ = ["Justin McCarty"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = ""
__email__ = ""
__status__ = ""


def hourly_xr_get_hourly_results(scenario, strategy, bldg):
    bldg_path = os.path.join(os.getcwd(), scenario, strategy, 'initial', 'outputs', 'data', 'demand',
                             '{}.csv'.format(bldg))
    data = pd.read_csv(bldg_path)
    return data


def hourly_xr_create_hourly_results_df(config,strategy):
    buildings = util.generate_key_list(config)
    scenario = config.general.parent

    interior_temp_dict = dict()
    pv_gen_dict = dict()
    operative_temp_dict = dict()
    district_dhw_dict = dict()
    district_heat_dict = dict()
    district_cool_dict = dict()
    electrical_aux_dict = dict()
    electrical_dhw_dict = dict()
    electrical_heat_dict = dict()
    electrical_cool_dict = dict()
    heatloss_rad_dict = dict()
    heatgain_solar_dict = dict()

    grid_dict = dict()
    electrical_appliances_dict = dict()
    electrical_ev_dict = dict()
    electrical_refrig_dict = dict()
    electrical_data_cool_dict = dict()
    electrical_ind_process_dict = dict()
    electrical_data_dict = dict()
    ng_dhw_dict = dict()
    ng_heat_dict = dict()
    heat_enduse_sys_dict = dict()
    heat_enduse_dict = dict()
    dhw_enduse_sys_dict = dict()
    dhw_enduse_dict = dict()
    cool_enduse_sys_dict = dict()
    cool_enduse_dict = dict()

    for bldg in buildings:
        data = hourly_xr_get_hourly_results(scenario, strategy, bldg)
        interior_temp_dict[bldg] = data['T_int_C']  # 0
        pv_gen_dict[bldg] = data['PV_kWh']  # 1
        operative_temp_dict[bldg] = data['theta_o_C']  # 2
        district_dhw_dict[bldg] = data['DH_ww_kWh']  # 3
        district_heat_dict[bldg] = data['DH_hs_kWh']  # 4
        district_cool_dict[bldg] = data['DC_cs_kWh']  # 5
        electrical_aux_dict[bldg] = data['Eaux_kWh']  # 6
        electrical_dhw_dict[bldg] = data['E_ww_kWh']  # 7
        electrical_heat_dict[bldg] = data['E_hs_kWh']  # 8
        electrical_cool_dict[bldg] = data['E_cs_kWh']  # 9
        heatloss_rad_dict[bldg] = data['I_rad_kWh']  # 10
        heatgain_solar_dict[bldg] = data['I_sol_kWh']  # 11

        grid_dict[bldg] = data['GRID_kWh']  # 12
        electrical_appliances_dict[bldg] = data['Eal_kWh']  # 13
        electrical_ev_dict[bldg] = data['Ev_kWh']  # 14
        electrical_refrig_dict[bldg] = data['E_cre_kWh']  # 15
        electrical_data_cool_dict[bldg] = data['E_cdata_kWh']  # 16
        electrical_ind_process_dict[bldg] = data['Epro_kWh']  # 17
        electrical_data_dict[bldg] = data['Edata_kWh']  # 18
        ng_dhw_dict[bldg] = data['NG_ww_kWh']  # 19
        ng_heat_dict[bldg] = data['NG_hs_kWh']  # 20
        heat_enduse_sys_dict[bldg] = data['Qhs_sys_kWh']  # 21
        heat_enduse_dict[bldg] = data['Qhs_kWh']  # 22
        dhw_enduse_sys_dict[bldg] = data['Qww_sys_kWh']  # 23
        dhw_enduse_dict[bldg] = data['Qww_kWh']  # 24
        cool_enduse_sys_dict[bldg] = data['Qcs_sys_kWh']  # 25
        cool_enduse_dict[bldg] = data['Qcs_kWh']  # 26

    return [interior_temp_dict, pv_gen_dict, operative_temp_dict, district_dhw_dict,
            district_heat_dict, district_cool_dict, electrical_aux_dict, electrical_dhw_dict, electrical_heat_dict,
            electrical_cool_dict, heatloss_rad_dict, heatgain_solar_dict, grid_dict, electrical_appliances_dict,
            electrical_ev_dict, electrical_refrig_dict, electrical_data_cool_dict,
            electrical_ind_process_dict, electrical_data_dict, ng_dhw_dict, ng_heat_dict,
            heat_enduse_sys_dict, heat_enduse_dict, dhw_enduse_sys_dict, dhw_enduse_dict,
            cool_enduse_sys_dict, cool_enduse_dict]


def hourly_xr_get_annual_results(scen, sset):
    embodied_carbon_path = os.path.join(os.getcwd(), scen, sset, 'initial', 'outputs', 'data', 'emissions',
                                        'Total_LCA_embodied.csv')
    operational_carbon_path = os.path.join(os.getcwd(), scen, sset, 'initial', 'outputs', 'data', 'emissions',
                                           'Total_LCA_operation.csv')
    building_tac_path = os.path.join(os.getcwd(), scen, sset, 'initial', 'outputs', 'data', 'costs', 'building_tac.csv')
    supply_syst_path = os.path.join(os.getcwd(), scen, sset, 'initial', 'outputs', 'data', 'costs',
                                    'supply_system_costs_today.csv')

    emb_carbon = pd.read_csv(embodied_carbon_path)['GHG_sys_embodied_tonCO2'].sum()
    op_carbon_district = pd.read_csv(operational_carbon_path)['GHG_sys_district_scale_tonCO2'].sum()
    op_carbon_building = pd.read_csv(operational_carbon_path)['GHG_sys_building_scale_tonCO2'].sum()
    build_costs_opex = pd.read_csv(building_tac_path)['opex_building_systems'].sum()
    build_costs_capex = pd.read_csv(building_tac_path)['capex_building_systems'].sum()
    supply_costs_opex = pd.read_csv(supply_syst_path)['Opex_sys_USD'].sum()
    supply_costs_capex = pd.read_csv(supply_syst_path)['Capex_total_sys_USD'].sum()

    return [emb_carbon, op_carbon_district, op_carbon_building, build_costs_opex, build_costs_capex, supply_costs_opex,
            supply_costs_capex]


def hourly_xr_create_hourly_dataset(config, sset):
    scen = config.general.parent
    time_arr = pd.date_range("{}-01-01".format(scen.split('_')[1]), periods=8760, freq="h")
    data = hourly_xr_create_hourly_results_df(scen, sset)
    annual_results = hourly_xr_get_annual_results(scen, sset)
    d = xr.Dataset(
        data_vars=dict(
            interior_temp_C=(["buildings", "times"], pd.DataFrame.from_dict(data[0]).to_numpy()),
            pv_generated_kwh=(["buildings", "times"], pd.DataFrame.from_dict(data[1]).to_numpy()),
            operative_temp_C=(["buildings", "times"], pd.DataFrame.from_dict(data[2]).to_numpy()),
            district_dhw_kwh=(["buildings", "times"], pd.DataFrame.from_dict(data[3]).to_numpy()),
            district_heat_kwh=(["buildings", "times"], pd.DataFrame.from_dict(data[4]).to_numpy()),
            district_cool_kwh=(["buildings", "times"], pd.DataFrame.from_dict(data[5]).to_numpy()),
            electric_aux_kwh=(["buildings", "times"], pd.DataFrame.from_dict(data[6]).to_numpy()),
            electric_dhw_kwh=(["buildings", "times"], pd.DataFrame.from_dict(data[7]).to_numpy()),
            electric_heating_kwh=(["buildings", "times"], pd.DataFrame.from_dict(data[8]).to_numpy()),
            electric_cooling_kwh=(["buildings", "times"], pd.DataFrame.from_dict(data[9]).to_numpy()),
            radiative_heat_loss_kwh=(["buildings", "times"], pd.DataFrame.from_dict(data[10]).to_numpy()),
            solar_heat_gain=(["buildings", "times"], pd.DataFrame.from_dict(data[11]).to_numpy()),

            grid_supply_kwh=(["buildings", "times"], pd.DataFrame.from_dict(data[12]).to_numpy()),
            electric_plug_kwh=(["buildings", "times"], pd.DataFrame.from_dict(data[13]).to_numpy()),
            electric_vehicles_kwh=(["buildings", "times"], pd.DataFrame.from_dict(data[14]).to_numpy()),
            electric_refrigerator_kwh=(["buildings", "times"], pd.DataFrame.from_dict(data[15]).to_numpy()),
            electric_datacool_kwh=(["buildings", "times"], pd.DataFrame.from_dict(data[16]).to_numpy()),
            electric_industrial_process_kwh=(["buildings", "times"], pd.DataFrame.from_dict(data[17]).to_numpy()),
            electric_data_kwh=(["buildings", "times"], pd.DataFrame.from_dict(data[18]).to_numpy()),
            ng_dhw_kwh=(["buildings", "times"], pd.DataFrame.from_dict(data[19]).to_numpy()),
            ng_heat_kwh=(["buildings", "times"], pd.DataFrame.from_dict(data[20]).to_numpy()),
            enduse_heat_sys_kwh=(["buildings", "times"], pd.DataFrame.from_dict(data[21]).to_numpy()),
            enduse_heat_kwh=(["buildings", "times"], pd.DataFrame.from_dict(data[22]).to_numpy()),
            enduse_dhw_sys_kwh=(["buildings", "times"], pd.DataFrame.from_dict(data[23]).to_numpy()),
            enduse_dhw_kwh=(["buildings", "times"], pd.DataFrame.from_dict(data[24]).to_numpy()),
            enduse_cool_sys_kwh=(["buildings", "times"], pd.DataFrame.from_dict(data[25]).to_numpy()),
            enduse_cool_kwh=(["buildings", "times"], pd.DataFrame.from_dict(data[26]).to_numpy()),
        ),
        coords=dict(
            bldgs=("building", util.generate_key_list(config)),
            time=time_arr,
        ),
        attrs=dict(scenario=scen,
                   strategy_set=sset,
                   embodied_tonCO2=annual_results[0],
                   operating_district_tonCO2=annual_results[1],
                   operating_building_tonCO2=annual_results[2],
                   building_opex_USD=annual_results[3],
                   building_capex_USD=annual_results[4],
                   supply_opex_USD=annual_results[5],
                   supply_capex_USD=annual_results[6]))
    return d


def whole_xr_get_annual_results_bldg(config, sset):
    scen = config.general.parent

    embodied_carbon_path = os.path.join(os.getcwd(), scen, sset, 'initial', 'outputs', 'data', 'emissions',
                                        'Total_LCA_embodied.csv')
    operational_carbon_path = os.path.join(os.getcwd(), scen, sset, 'initial', 'outputs', 'data', 'emissions',
                                           'Total_LCA_operation.csv')
    building_tac_path = os.path.join(os.getcwd(), scen, sset, 'initial', 'outputs', 'data', 'costs', 'building_tac.csv')
    supply_syst_path = os.path.join(os.getcwd(), scen, sset, 'initial', 'outputs', 'data', 'costs',
                                    'supply_system_costs_today.csv')
    building_demand_path = os.path.join(os.getcwd(), scen, sset, 'initial', 'outputs', 'data', 'demand',
                                        'Total_demand.csv')
    building_comfort_path = os.path.join(os.getcwd(), scen, sset, 'initial', 'inputs', 'building-properties',
                                         'indoor_comfort.dbf')

    gross_area_sqm = pd.read_csv(building_tac_path, index_col='Name')['GFA_m2']
    floor_area_sqm = pd.read_csv(building_tac_path, index_col='Name')['footprint']
    height_above_ground_m = pd.read_csv(building_tac_path, index_col='Name')['height_ag']
    height_below_ground_m = pd.read_csv(building_tac_path, index_col='Name')['height_bg']
    primary_use = pd.read_csv(building_tac_path, index_col='Name')['1ST_USE']
    year = pd.read_csv(building_tac_path, index_col='Name')['YEAR']
    base_type = pd.read_csv(building_tac_path, index_col='Name')['STANDARD']
    emb_carbon = pd.read_csv(embodied_carbon_path, index_col='Name')['GHG_sys_embodied_tonCO2']
    op_carbon_district = pd.read_csv(operational_carbon_path, index_col='Name')['GHG_sys_district_scale_tonCO2']
    op_carbon_building = pd.read_csv(operational_carbon_path, index_col='Name')['GHG_sys_building_scale_tonCO2']
    build_costs_opex = pd.read_csv(building_tac_path, index_col='Name')['opex_building_systems']
    build_costs_capex = pd.read_csv(building_tac_path, index_col='Name')['capex_building_systems']
    supply_costs_opex = pd.read_csv(supply_syst_path, index_col='Name')['Opex_sys_USD']
    supply_costs_capex = pd.read_csv(supply_syst_path, index_col='Name')['Capex_total_sys_USD']

    total_demand = pd.read_csv(building_demand_path, index_col='Name')

    def calc_teui(qh, qc, el_all, el_hs, el_ww, el_cs, gfa):
        el = el_all - (el_hs + el_ww + el_cs)
        return (qh + qc + el) / gfa

    total_demand['teui'] = total_demand.apply(lambda x: calc_teui(x['QH_sys_MWhyr'],
                                                                  x['QC_sys_MWhyr'],
                                                                  x['E_sys_MWhyr'],
                                                                  x['E_hs_MWhyr'],
                                                                  x['E_ww_MWhyr'],
                                                                  x['E_cs_MWhyr'],
                                                                  x['GFA_m2']), axis=1)
    teui = total_demand['teui']
    pv = total_demand['PV_MWhyr']

    indoor_comfort_df = cea.utilities.dbf.dbf_to_dataframe(building_comfort_path)

    buildings = util.generate_key_list(config)
    hours_above_cool_sb_dict = dict()
    hours_below_heat_sb_dict = dict()
    hours_above_cool_sp_dict = dict()
    hours_below_heat_sp_dict = dict()
    hours_above_30C_dict = dict()
    hours_below_15C_dict = dict()

    for bldg in buildings:
        data = hourly_xr_get_hourly_results(scen, sset, bldg)
        hours_above_cool_sb_dict[bldg] = (data['T_int_C'].values > indoor_comfort_df.loc[bldg]['Tcs_setb_C']).sum()
        hours_below_heat_sb_dict[bldg] = (data['T_int_C'].values < indoor_comfort_df.loc[bldg]['Ths_setb_C']).sum()
        hours_above_cool_sp_dict[bldg] = (data['T_int_C'].values > indoor_comfort_df.loc[bldg]['Tcs_set_C']).sum()
        hours_below_heat_sp_dict[bldg] = (data['T_int_C'].values < indoor_comfort_df.loc[bldg]['Ths_set_C']).sum()
        hours_above_30C_dict[bldg] = (data['T_int_C'].values > 30).sum()
        hours_below_15C_dict[bldg] = (data['T_int_C'].values < 15).sum()

    above_sb = pd.Series(hours_above_cool_sb_dict).rename('hours_above_sb')
    below_sb = pd.Series(hours_below_heat_sb_dict).rename('hours_below_sb')

    above_sp = pd.Series(hours_above_cool_sp_dict).rename('hours_above_sp')
    below_sp = pd.Series(hours_below_heat_sp_dict).rename('hours_below_sp')

    above_30C = pd.Series(hours_above_30C_dict).rename('hours_above_30C')
    below_15C = pd.Series(hours_below_15C_dict).rename('hours_below_15C')

    ann_res = [gross_area_sqm, floor_area_sqm, height_above_ground_m, height_below_ground_m, primary_use, year,
               base_type,
               emb_carbon, op_carbon_district, op_carbon_building, build_costs_opex, build_costs_capex,
               supply_costs_opex, supply_costs_capex,
               teui, pv, above_sb, below_sb, above_sp, below_sp, above_30C, below_15C]

    return pd.concat(ann_res, axis=1)


def whole_xr_create_annual_dataset(config):
    sset_list =util.generate_key_list(config)
    scen = config.general.parent
    datasets = []
    for i in sset_list[0:2]:
        ann_res = whole_xr_get_annual_results_bldg(scen, i)
        ann_res = ann_res.rename_axis(None, axis=1).rename_axis('Name', axis=0)
        ann_res_ds = xr.Dataset.from_dataframe(ann_res, sparse=False)
        ann_res_ds = ann_res_ds.assign_coords(strategy_set=i)
        datasets.append(ann_res_ds)
    return xr.concat(datasets, dim='strategy_set')


def netcdf_main(config):
    for sset in util.generate_key_list(config)[0:2]:
        hourly = hourly_xr_create_hourly_dataset(config, sset)
        # hourly.to_netcdf(f"/hourly_{scen}_{sset}.nc")

    whole = whole_xr_create_annual_dataset(config)
    # whole.to_netcdf(f"/whole_{scen}.nc")


# netcdf_main(scen, 8)