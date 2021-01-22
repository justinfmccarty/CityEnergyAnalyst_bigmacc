"""
This is a template script - an example of how a CEA script should be set up.

NOTE: ADD YOUR SCRIPT'S DOCUMENTATION HERE (what, why, include literature references)
"""

import os

import pandas as pd

import cea.analysis.costs.system_costs
import cea.analysis.lca.main
import cea.bigmacc.copy_results
import cea.bigmacc.create_rule_dataframe
import cea.config
import cea.datamanagement.archetypes_mapper
import cea.demand.demand_main
import cea.inputlocator
import cea.resources.radiation_daysim.radiation_main
import cea.resources.radiation_daysim.radiation_main
import cea.utilities
import cea.utilities.dbf

__author__ = "Justin McCarty"
__copyright__ = " "
__credits__ = ["Justin McCarty"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = ""
__email__ = ""
__status__ = ""


def edit_typology(config):
    edit_typ_path = config.bigmacc.changes
    years_2050 = pd.read_excel(edit_typ_path, sheet_name='2050s')
    years_2080 = pd.read_excel(edit_typ_path, sheet_name='2080s')

    locator = cea.inputlocator.InputLocator(config.scenario)
    typ_path = locator.get_building_typology()
    typ = cea.utilities.dbf.dbf_to_dataframe(typ_path)

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

    cea.utilities.dbf.dataframe_to_dbf(new_df, typ_path)
    return print(' - Typology file fixed')


def run_changes(proj, config):
    folder = config.bigmacc.keys
    keys = [f.name for f in os.scandir(folder) if f.is_dir()]

    for name in keys:
        print(' - - Editing typology file for project-{}.'.format(name))
        config.general.project = os.path.join(r'F:\BIGMACC_WESBROOK\Projects', proj, name)

        edit_typology(config)

        print(' - - Running system-costs and lca emissions for project-{}.'.format(name))
        # running the emissions and costing calculations
        cea.analysis.costs.system_costs.main(config)
        cea.analysis.lca.main.main(config)
        print(' - Switch to next project.')


def main(config):
    project_list = ['wesbrook_2050_ssp126']  # , 'wesbrook_2050_ssp585', 'wesbrook_2080_ssp126', 'wesbrook_2080_ssp585']
    for proj in project_list:
        print(' - Beginning {}'.format(proj))
        config.general.parent = proj
        run_changes(proj, config)
        print(' - Finished with {}'.format(proj))
    return print(' - CHANGES COMPLETED')


if __name__ == '__main__':
    main(cea.config.Configuration())
