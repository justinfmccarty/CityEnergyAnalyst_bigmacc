"""
This is a template script - an example of how a CEA script should be set up.

NOTE: ADD YOUR SCRIPT'S DOCUMENTATION HERE (what, why, include literature references)
"""

# import cea.bigmacc.bigmacc_util as util
import cea.resources.radiation_daysim.radiation_main
import os
import xlsxwriter
import itertools
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
import cea.bigmacc.copy_results
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


def check(config):
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    for i in list(range(1, 10)):
        print('{} one'.format(i))
        if os.path.exists(locator.get_schedule_model_folder()):
            print('{} two'.format(i))
            break
        else:
            print(i)
    print('All')


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


def checkscen(config):
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)

    air_con_path = locator.get_building_air_conditioning()
    air_con = cea.utilities.dbf.dbf_to_dataframe(air_con_path)

    supply_path = locator.get_building_supply()
    supply = cea.utilities.dbf.dbf_to_dataframe(supply_path)

    df = supply.merge(air_con, on='Name')

    supply = df[['Name', 'type_cs_x', 'type_hs_x', 'type_dhw_x', 'type_el']]
    supply = supply.rename(columns={'type_cs_x': 'type_cs', 'type_hs_x': 'type_hs', 'type_dhw_x': 'type_dhw'})

    air_con = df[['Name', 'type_cs_y', 'type_hs_y', 'type_dhw_y', 'type_ctrl', 'type_vent', 'heat_starts', 'heat_ends',
                  'cool_starts', 'cool_ends']]
    air_con = air_con.rename(columns={'type_cs_y': 'type_cs', 'type_hs_y': 'type_hs', 'type_dhw_y': 'type_dhw'})
    # df.to_csv(r"C:\Users\justi\Desktop\test1.csv")
    cea.utilities.dbf.dataframe_to_dbf(air_con, r"C:\Users\justi\Desktop\air_con.dbf")
    cea.utilities.dbf.dataframe_to_dbf(supply, r"C:\Users\justi\Desktop\supply.dbf")


def prt(config):

    return print(config.bigmacc.keys)


def edit_typology(config):

    edit_typ_path = r"F:\BIGMACC_WESBROOK\Wesbrook Changes\typology_year_map.xlsx"
    years_2050 = pd.read_excel(edit_typ_path, sheet_name='2050s')
    years_2080 = pd.read_excel(edit_typ_path, sheet_name='2080s')

    locator = cea.inputlocator.InputLocator(config.scenario)
    typ_path = locator.get_building_typology()
    print(typ_path)
    typ = cea.utilities.dbf.dbf_to_dataframe(typ_path)

    typ.to_csv(r"C:\Users\justi\Desktop\test0.csv")

    pathway_code = config.general.parent
    pathway_items = pathway_code.split('_')
    scenario_year = int(pathway_items[1])

    if scenario_year == 2050:
        new_df = typ.merge(years_2050, on='Name')
        del new_df['YEAR']
        new_df = new_df.rename(columns={'YEAR 2050':'YEAR'})
    elif scenario_year == 2080:
        new_df = typ.merge(years_2080, on='Name')
        del new_df['YEAR']
        new_df = new_df.rename(columns={'YEAR 2080':'YEAR'})
    else:
        new_df = pd.DataFrame()
        print('Year designation is incorrect')

    # new_df.to_csv(r"C:\Users\justi\Desktop\test1.csv")
    # cea.utilities.dbf.dataframe_to_dbf(typ, typ_path)
    return print(' - Typology file fixed')

def run_changes(proj,config):
    folder = config.bigmacc.keys
    keys = [f.name for f in os.scandir(folder) if f.is_dir()]

    for name in keys:
        print(' - Editing typology file for project-{}.'.format(name))
        config.general.project = os.path.join(r'F:\BIGMACC_WESBROOK\Projects',proj,name)
        # config.general.scenario_name = os.path.join(name, 'initial')

        edit_typology(config)

        print(' - Running system-costs and lca emissions for project-{}.'.format(name))
        # # running the emissions and costing calculations
        # cea.analysis.costs.system_costs.main(config)
        # cea.analysis.lca.main.main(config)
        print(' - Switch to next project.')

def main(config):
    project_list = ['wesbrook_2050_ssp126']#, 'wesbrook_2050_ssp585', 'wesbrook_2080_ssp126', 'wesbrook_2080_ssp585']
    for proj in project_list:
        run_changes(proj,config)
        print(' - Finished with {}'.format(proj))
    return print(' - CHANGES COMPLETED')


if __name__ == '__main__':
    main(cea.config.Configuration())
