
import warnings
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
import cea.bigmacc.wesbrook_DH
import cea.datamanagement.archetypes_mapper
import cea.datamanagement.data_initializer
import cea.analysis.costs.system_costs
import cea.analysis.lca.main

warnings.filterwarnings("ignore")


def test_process(bldg, locator):
    # print(locator.get_demand_results_file(bldg, format='csv'))
    print(bldg)

def multiprocess_write_pv(config):

    locator = cea.inputlocator.InputLocator(config.scenario)
    pv_total = pd.read_csv(locator.PV_total_buildings(), index_col='Name')
    bldg_list = pv_total.index.to_list()

    n = len(bldg_list)
    calc = cea.utilities.parallel.vectorize(test_process, config.get_number_of_processes())

    calc(
        bldg_list,
        repeat(locator, n))

if __name__ == '__main__':
    multiprocess_write_pv(cea.config.Configuration())