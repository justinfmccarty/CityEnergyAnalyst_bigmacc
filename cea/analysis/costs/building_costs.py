"""
costs according to hvac and envelope systems
"""

import numpy as np
import pandas as pd
from geopandas import GeoDataFrame as gpdf
import itertools
import cea.config
import cea.inputlocator

import numpy as np
from geopandas import GeoDataFrame as Gdf
import pandas as pd
from cea.analysis.costs.equations import calc_capex_annualized, calc_opex_annualized
from cea.constants import SERVICE_LIFE_OF_BUILDINGS, SERVICE_LIFE_OF_TECHNICAL_SYSTEMS, \
    CONVERSION_AREA_TO_FLOOR_AREA_RATIO, EMISSIONS_EMBODIED_TECHNICAL_SYSTEMS
from cea.utilities.dbf import dbf_to_dataframe



__author__ = "Justin McCarty adjusting Jimeno A. Fonseca"
__copyright__ = "Copyright 2020, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Emanuel Riegelbauer", "Justin McCarty"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = ""
__email__ = "mccarty.justin.f@gmail.com"
__status__ = "Production"




def building_capex(year_to_calculate, locator):
    """
    Calculation of non-supply capital costs.

    The results are

    As part of the algorithm, the following files are read from InputLocator:

    - architecture.shp: shapefile with the architecture of each building
        locator.get_building_architecture()
    - occupancy.shp: shapefile with the occupancy types of each building
        locator.get_building_occupancy()
    - age.shp: shapefile with the age and retrofit date of each building
        locator.get_building_age()
    - zone.shp: shapefile with the geometry of each building in the zone of study
        locator.get_zone_geometry()
    - Archetypes_properties: csv file with the database of archetypes including embodied energy and emissions
        locator.l()

    As a result, the following file is created:

    - Total_building_capex: .csv
        csv file of yearly primary energy and grey emissions per building stored in locator.get_lca_embodied()

    :param year_to_calculate:  year between 1900 and 2100 indicating when embodied energy is evaluated
        to account for emissions already offset from building construction and retrofits more than 60 years ago.
    :type year_to_calculate: int
    :param locator: an instance of InputLocator set to the scenario
    :type locator: InputLocator
    :returns: This function does not return anything
    :rtype: NoneType


    Files read / written from InputLocator:

    get_building_architecture
    get_building_occupancy
    get_building_age
    get_zone_geometry
    get_archetypes_embodied_energy
    get_archetypes_embodied_emissions

    path_LCA_embodied_energy:
        path to database of archetypes embodied energy file
        Archetypes_embodied_energy.csv
    path_LCA_embodied_emissions:
        path to database of archetypes grey emissions file
        Archetypes_embodied_emissions.csv
    path_age_shp: string
        path to building_age.shp
    path_occupancy_shp:
        path to building_occupancyshp
    path_geometry_shp:
        path to building_geometrys.hp
    path_architecture_shp:
        path to building_architecture.shp
    path_results : string
        path to demand results folder emissions
    """
    print('Calculating the Total Annualized costs of building components.')
    # local variables
    age_df = dbf_to_dataframe(locator.get_building_typology())
    architecture_df = dbf_to_dataframe(locator.get_building_architecture())
    hvac_df = dbf_to_dataframe(locator.get_building_supply())
    supply_df = dbf_to_dataframe(locator.get_building_air_conditioning())
    geometry_df = Gdf.from_file(locator.get_zone_geometry())
    geometry_df['footprint'] = geometry_df.area
    geometry_df['perimeter'] = geometry_df.length
    geometry_df = geometry_df.drop('geometry', axis=1)

    # local variables
    surface_database_windows = pd.read_excel(locator.get_database_envelope_systems(), "WINDOW")
    surface_database_roof = pd.read_excel(locator.get_database_envelope_systems(), "ROOF")
    surface_database_walls = pd.read_excel(locator.get_database_envelope_systems(), "WALL")
    surface_database_floors = pd.read_excel(locator.get_database_envelope_systems(), "FLOOR")
    surface_database_cons = pd.read_excel(locator.get_database_envelope_systems(), "CONSTRUCTION")
    surface_database_leak = pd.read_excel(locator.get_database_envelope_systems(), "LEAKAGE")
    hvac_database_cooling = pd.read_excel(locator.get_database_air_conditioning_systems(), "COOLING")
    hvac_database_heating = pd.read_excel(locator.get_database_air_conditioning_systems(), "HEATING")
    hvac_database_vent = pd.read_excel(locator.get_database_air_conditioning_systems(), "VENTILATION")



    # query data
    df = architecture_df.merge(surface_database_windows, left_on='type_win', right_on='code')
    df2 = architecture_df.merge(surface_database_roof, left_on='type_roof', right_on='code')
    df3 = architecture_df.merge(surface_database_walls, left_on='type_wall', right_on='code')
    df4 = architecture_df.merge(surface_database_floors, left_on='type_floor', right_on='code')
    df5 = architecture_df.merge(surface_database_floors, left_on='type_base', right_on='code')
    df5.rename({'capex_FLOOR': 'capex_BASE'}, inplace=True, axis=1)
    df6 = architecture_df.merge(surface_database_walls, left_on='type_part', right_on='code')
    df6.rename({'capex_WALL': 'capex_PART'}, inplace=True, axis=1)
    df7 = architecture_df.merge(surface_database_cons, left_on='type_cons', right_on='code')
    df8 = architecture_df.merge(surface_database_leak, left_on='type_leak', right_on='code')
    df9 = hvac_df.merge(hvac_database_cooling, left_on='type_cs', right_on='code')
    df10 = hvac_df.merge(hvac_database_heating, left_on='type_hs', right_on='code')
    df14 = supply_df.merge(hvac_database_vent, left_on='type_vent', right_on='code')

    fields = ['Name', "capex_WIN"]
    fields2 = ['Name', "capex_ROOF"]
    fields3 = ['Name', "capex_WALL"]
    fields4 = ['Name', "capex_FLOOR"]
    fields5 = ['Name', "capex_BASE"]
    fields6 = ['Name', "capex_PART"]

    # added for bigmacc
    fields7 = ['Name', "capex_CONS"]
    fields8 = ['Name', "capex_LEAK"]
    fields9 = ['Name', "capex_hvacCS"]
    fields10 = ['Name', "capex_hvacHS"]
    fields14 = ['Name', "capex_hvacVENT"]

    surface_properties = df[fields].merge(df2[fields2],
                                                    on='Name').merge(df3[fields3],
                                                    on='Name').merge(df4[fields4],
                                                    on='Name').merge(df5[fields5],
                                                    on='Name').merge(df6[fields6],
                                                    on='Name').merge(df7[fields7],
                                                    on='Name').merge(df8[fields8],
                                                    on='Name').merge(df9[fields9],
                                                    on='Name').merge(df10[fields10],
                                                    on='Name').merge(df14[fields14], on='Name')

    # DataFrame with joined data for all categories
    data_meged_df = geometry_df.merge(age_df, on='Name').merge(surface_properties, on='Name').merge(architecture_df, on='Name').merge(hvac_df, on='Name').merge(supply_df, on='Name')

    # calculate building geometry
    ## total window area
    average_wwr = [np.mean([a, b, c, d]) for a, b, c, d in
                   zip(data_meged_df['wwr_south'], data_meged_df['wwr_north'], data_meged_df['wwr_west'],
                       data_meged_df['wwr_east'])]

    data_meged_df['windows_ag'] = average_wwr * data_meged_df['perimeter'] * data_meged_df['height_ag']

    ## wall area above ground
    data_meged_df['area_walls_ext_ag'] = data_meged_df['perimeter'] * data_meged_df['height_ag'] - data_meged_df['windows_ag']

    # fix according to the void deck
    data_meged_df['empty_envelope_ratio'] = 1 - (
            (data_meged_df['void_deck'] * (data_meged_df['height_ag'] / data_meged_df['floors_ag'])) / (
            data_meged_df['area_walls_ext_ag'] + data_meged_df['windows_ag']))
    data_meged_df['windows_ag'] = data_meged_df['windows_ag'] * data_meged_df['empty_envelope_ratio']
    data_meged_df['area_walls_ext_ag'] = data_meged_df['area_walls_ext_ag'] * data_meged_df['empty_envelope_ratio']

    ## wall area below ground
    data_meged_df['area_walls_ext_bg'] = data_meged_df['perimeter'] * data_meged_df['height_bg']
    ## floor area above ground
    data_meged_df['floor_area_ag'] = data_meged_df['footprint'] * data_meged_df['floors_ag']
    ## floor area below ground
    data_meged_df['floor_area_bg'] = data_meged_df['footprint'] * data_meged_df['floors_bg']
    ## total floor area
    data_meged_df['GFA_m2'] = data_meged_df['floor_area_ag'] + data_meged_df['floor_area_bg']

    result_emissions = calculate_contributions(data_meged_df,
                                               year_to_calculate)

    # export the results for building system costs
    result_emissions.to_csv(locator.get_building_tac_file(),
                            index=False,
                            float_format='%.2f', na_rep='nan')
    print('done!')


def calculate_contributions(df, year_to_calculate):
    """
    Calculate the embodied energy/emissions for each building based on their construction year, and the area and
    renovation year of each building component.

    :param archetype: String that defines whether the 'EMBODIED_ENERGY' or 'EMBODIED_EMISSIONS' are being calculated.
    :type archetype: str
    :param df: DataFrame with joined data of all categories for each building, that is: occupancy, age, geometry,
        architecture, building component area, construction category and renovation category for each building component
    :type df: DataFrame
    :param locator: an InputLocator instance set to the scenario to work on
    :type locator: InputLocator
    :param year_to_calculate: year in which the calculation is done; since the embodied energy and emissions are
        calculated over 60 years, if the year of calculation is more than 60 years after construction, the results
        will be 0
    :type year_to_calculate: int
    :param total_column: label for the column with the total results (e.g., 'GEN_GJ')
    :type total_column: str
    :param specific_column: label for the column with the results per square meter (e.g., 'GEN_MJm2')
    :type specific_column: str

    :return result: DataFrame with the calculation results (i.e., the total and specific embodied energy or emisisons
        for each building)
    :rtype result: DataFrame
    """

    # calculate the embodied energy/emissions due to construction
    total_column = 'saver'
    ## calculate how many years before the calculation year the building was built in
    df['delta_year'] = year_to_calculate - df['YEAR']
    ## if it was built more than 60 years before, the embodied energy/emissions have been "paid off" and are set to 0
    df['confirm'] = df.apply(lambda x: calc_if_existing(x['delta_year'], SERVICE_LIFE_OF_BUILDINGS), axis=1)
    ## if it was built less than 60 years before, the contribution from each building component is calculated
    df[total_column] = ((df['capex_WALL'] * (df['area_walls_ext_ag'] + df['area_walls_ext_bg']) +
                         df['capex_WIN'] * df['windows_ag'] +
                         df['capex_FLOOR'] * df['floor_area_ag'] +
                         df['capex_CONS'] * (df['floor_area_bg'] +df['floor_area_ag'])  +
                         df['capex_LEAK'] * (df['area_walls_ext_ag'] + df['area_walls_ext_bg']) +
                         df['capex_hvacCS'] * df['floor_area_ag'] +
                         df['capex_hvacHS'] * df['floor_area_ag'] +
                         df['capex_hvacVENT'] * df['floor_area_ag'] +
                         df['capex_BASE'] * df['floor_area_bg'] +
                         df['capex_PART'] * (df['floor_area_ag']+df['floor_area_bg']) * CONVERSION_AREA_TO_FLOOR_AREA_RATIO +
                         df['capex_ROOF'] * df['footprint']) / SERVICE_LIFE_OF_TECHNICAL_SYSTEMS) * df['confirm']

    # df[total_column] += (((df['floor_area_ag'] + df['floor_area_bg']) * EMISSIONS_EMBODIED_TECHNICAL_SYSTEMS) / SERVICE_LIFE_OF_TECHNICAL_SYSTEMS) * df['confirm']

    # the total cost intensity
    df['capex_total_cost_m2'] = df[total_column] / df['GFA_m2']

    # the total and specific embodied energy/emissions are returned
    # result = df[['Name', 'GHG_sys_embodied_tonCO2', 'GHG_sys_embodied_kgCO2m2', 'GFA_m2']]

    df['capex_building_systems'] = df[total_column]
    df['opex_building_systems'] = df['capex_building_systems'] * (.05)
    df['capex_ann_building_systems'] = df['capex_building_systems'].apply(lambda x: calc_capex_annualized(x, 5, 30),axis=1)
    df['opex_ann_building_systems'] = df['opex_building_systems'].apply(lambda x: calc_opex_annualized(x, 5, 30),axis=1)
    df['TAC_building_systems'] = df['capex_ann_building_systems'] + df['opex_ann_building_systems']

    return df