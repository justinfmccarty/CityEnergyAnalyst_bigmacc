"""
For the BIGMACC process a dataframe needs to be created and somewhat hardcoded.
"""

import os
import cea.config
import cea.inputlocator
import cea.utilities.dbf
import pandas as pd
import numpy as np
import cea.bigmacc.bigmacc_util as util

__author__ = "Justin McCarty"
__copyright__ = ""
__credits__ = ["Justin McCarty"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = ""
__email__ = ""
__status__ = ""


def nec_cs_rule(nec_cs_value):
    return nec_cs_value


def runrad_rule(key, run_list):  # SETS FOR HEATING REDUCED 1C (20C TO 19C) AND SETS FOR COOLING RAISED 1C (24C TO 25C)
    if key in run_list:
        return True
    else:
        return False


def copy_key(key, run_list):
    config = cea.config.Configuration()
    if key in run_list:
        return os.path.join(config.bigmacc.data, config.general.parent, key, config.general.scenario_name, 'outputs', 'data',
                            'solar-radiation')
    elif util.change_key(key) in run_list:
        return os.path.join(config.bigmacc.data, config.general.parent, util.change_key(key), config.general.scenario_name, 'outputs', 'data',
                            'solar-radiation')
    else:
        return os.path.join(config.bigmacc.data, config.general.parent, key, config.general.scenario_name, 'outputs', 'data',
                            'solar-radiation')


def SP_rule(key, SP_value):  # SET INTEGER FOR HEATING AND COOLING SETPOINT
    keys = [int(d) for d in key]
    if keys[0] == 1:
        return SP_value
    else:
        return np.nan


def GR_rule(key, GR_value):  # ALL BUILDINGS GET GREEN ROOFS
    keys = [int(d) for d in key]
    if keys[1] == 1:
        return GR_value
    else:
        return np.nan


def DR_rule(key, DR_name):  # EXISTING BUILDINGS HAVE DEEP WALL AND WINDOW RETROFIT (WWR REDUCED)
    keys = [int(d) for d in key]
    if keys[2] == 1:
        return DR_name
    else:
        return np.nan


def PH_rule(key, PH_value):  # NEW BUILD REQ PASSIVE
    keys = [int(d) for d in key]
    if keys[3] == 1:
        return PH_value
    else:
        return np.nan


def PH_GR_rule(key, PH_GR_value):  # NEW BUILD REQ PASSIVE AND GREEN ROOF
    keys = [int(d) for d in key]
    if keys[3] == 1:
        if keys[1] == 1:
            return PH_GR_value
        else:
            return np.nan
    else:
        return np.nan


def HP_rule(key,
            HP_value):  # NEW BUILD AND REFURBISHMENT/RETROFITS REQUIRE HEAT PUMP INSTALLATION (NO DISTRICT SERVICES)
    keys = [int(d) for d in key]
    if keys[4] == 1:
        return HP_value
    else:
        return np.nan


def MT_rule(key, MT_value):  # NEW BUILD REQUIRES MASS TIMBER STRUCTURAL SYSTEMS
    keys = [int(d) for d in key]
    if keys[5] == 1:
        return MT_value
    else:
        return np.nan


def SW_rule(key, SW_value):  # DISTRICT COOLING SYSTEM INSTALLED LINKED TO WRECK BEACH
    keys = [int(d) for d in key]
    if keys[6] == 1:
        return SW_value
    else:
        return np.nan


def PV_rule(key, PV_value):  # ALL BUILDINGS HAVE ROOFTOP PV INSTALLED
    keys = [int(d) for d in key]
    if keys[7] == 1:
        return PV_value
    else:
        return np.nan


def PV_GR_rule(key, PV_GR_value):  # ALL BUILDINGS HAVE ROOFTOP PV AND GREEN ROOF INSTALLED
    keys = [int(d) for d in key]
    if keys[7] == 1:
        if keys[1] == 1:
            return PV_GR_value
        else:
            return np.nan
    else:
        return np.nan


def PV_PH_rule(key, PV_PH_value):  # ALL BUILDINGS HAVE ROOFTOP PV AND PASSIVE HOUSE INSTALLED
    keys = [int(d) for d in key]
    if keys[7] == 1:
        if keys[3] == 1:
            return PV_PH_value
        else:
            return np.nan
    else:
        return np.nan


def PV_GR_PH_rule(key, PV_GR_PH_value):  # ALL BUILDINGS HAVE ROOFTOP PV AND GREEN ROOF AND PASSIVE HOUSE INSTALLED
    keys = [int(d) for d in key]
    if keys[7] == 1:
        if keys[1] == 1:
            if keys[3] == 1:
                return PV_GR_PH_value
            else:
                return np.nan
        else:
            return np.nan
    else:
        return np.nan


# noinspection PyTypeChecker
def rule_dataframe(config):
    print('key in dataframe')
    print(config.bigmacc.key)
    key_df = pd.DataFrame()
    key_df['keys'] = pd.Series(config.bigmacc.key)
    key_df['experiments'] = key_df['keys'].apply(lambda x: 'exp_{}'.format(x))

    key_df['NEC_hvac_cs_nat_vent'] = key_df.apply(lambda x: nec_cs_rule('HVAC_COOLING_AS7'), axis=1)
    key_df['NEC_hvac_cs_mech_vent'] = key_df.apply(lambda x: nec_cs_rule('HVAC_COOLING_AS3'), axis=1)
    key_df['NEC_supply_cs'] = key_df.apply(lambda x: nec_cs_rule('SUPPLY_COOLING_AS5'), axis=1)

    key_df['SP_heat'] = key_df.apply(lambda x: SP_rule(x['keys'], -1), axis=1)
    key_df['SP_cool'] = key_df.apply(lambda x: SP_rule(x['keys'], 1), axis=1)

    key_df['GR_roof'] = key_df.apply(lambda x: GR_rule(x['keys'], 'ROOF_AS16'), axis=1)

    key_df['DR_win'] = key_df.apply(lambda x: DR_rule(x['keys'], 'WINDOW_AS6'), axis=1)
    key_df['DR_leak'] = key_df.apply(lambda x: DR_rule(x['keys'], 'TIGHTNESS_AS2'), axis=1)
    key_df['DR_wall'] = key_df.apply(lambda x: DR_rule(x['keys'], 'WALL_AS17'), axis=1)
    key_df['DR_wwr'] = key_df.apply(lambda x: DR_rule(x['keys'], 0.20), axis=1)

    key_df['PH_base'] = key_df.apply(lambda x: PH_rule(x['keys'], 'FLOOR_AS11'), axis=1)
    key_df['PH_leak'] = key_df.apply(lambda x: PH_rule(x['keys'], 'TIGHTNESS_AS1'), axis=1)
    key_df['PH_win'] = key_df.apply(lambda x: PH_rule(x['keys'], 'WINDOW_AS6'), axis=1)
    key_df['PH_roof'] = key_df.apply(lambda x: PH_rule(x['keys'], 'ROOF_AS17'), axis=1)
    key_df['PH_GR_roof'] = key_df.apply(lambda x: PH_GR_rule(x['keys'], 'ROOF_AS18'), axis=1)
    key_df['PH_wall'] = key_df.apply(lambda x: PH_rule(x['keys'], 'WALL_AS18'), axis=1)
    key_df['PH_floor'] = key_df.apply(lambda x: PH_rule(x['keys'], 'FLOOR_AS12'), axis=1)
    key_df['PH_shade'] = key_df.apply(lambda x: PH_rule(x['keys'], 'SHADING_AS4'), axis=1)
    key_df['PH_wwr'] = key_df.apply(lambda x: PH_rule(x['keys'], 0.15), axis=1)
    key_df['PH_part'] = key_df.apply(lambda x: PH_rule(x['keys'], 'WALL_AS19'), axis=1)
    key_df['PH_hvac_cs'] = key_df.apply(lambda x: PH_rule(x['keys'], 'HVAC_COOLING_AS4'), axis=1)

    key_df['HP_hvac_cs'] = key_df.apply(lambda x: HP_rule(x['keys'], 'HVAC_COOLING_AS1'), axis=1)
    key_df['HP_hvac_hs'] = key_df.apply(lambda x: HP_rule(x['keys'], 'HVAC_HEATING_AS4'), axis=1)
    key_df['HP_supply_cs'] = key_df.apply(lambda x: HP_rule(x['keys'], 'SUPPLY_COOLING_AS1'), axis=1)
    key_df['HP_supply_hs'] = key_df.apply(lambda x: HP_rule(x['keys'], 'SUPPLY_HEATING_AS7'), axis=1)
    key_df['HP_supply_dhw'] = key_df.apply(lambda x: HP_rule(x['keys'], 'SUPPLY_HOTWATER_AS7'), axis=1)

    key_df['MT_cons'] = key_df.apply(lambda x: MT_rule(x['keys'], 'CONSTRUCTION_AS2'), axis=1)

    key_df['SW_hvac_cs'] = key_df.apply(lambda x: SW_rule(x['keys'], 'HVAC_COOLING_AS1'), axis=1)
    key_df['SW_supply_cs'] = key_df.apply(lambda x: SW_rule(x['keys'], 'SUPPLY_COOLING_AS3'), axis=1)

    key_df['PV_GR_PH'] = key_df.apply(lambda x: PV_GR_PH_rule(x['keys'], 'ROOF_AS19'), axis=1)
    key_df['PV_PH'] = key_df.apply(lambda x: PV_PH_rule(x['keys'], 'ROOF_AS21'), axis=1)
    key_df['PV_GR'] = key_df.apply(lambda x: PV_GR_rule(x['keys'], 'ROOF_AS20'), axis=1)
    key_df['PV'] = key_df.apply(lambda x: PV_rule(x['keys'], 'ROOF_AS22'), axis=1)

    key_df['PV_GR_PH_hg'] = key_df.apply(lambda x: PV_GR_PH_rule(x['keys'], 0.6), axis=1)
    key_df['PV_PH_hg'] = key_df.apply(lambda x: PV_PH_rule(x['keys'], 0.25), axis=1)
    key_df['PV_GR_hg'] = key_df.apply(lambda x: PV_GR_rule(x['keys'], 0.4), axis=1)
    key_df['PV_hg'] = key_df.apply(lambda x: PV_rule(x['keys'], 0.1), axis=1)

    key_df['run_rad'] = key_df.apply(lambda x: runrad_rule(x['keys'], config.bigmacc.runradiation), axis=1)
    key_df['copy_rad'] = key_df.apply(lambda x: copy_key(x['keys'], config.bigmacc.runradiation), axis=1)
    key_df.to_csv(r"C:\Users\justi\Desktop\test0.csv")
    return key_df


def main(config):
    key_list = util.generate_key_list(config)
    # run_rad = config.bigmacc.runradiation
    # return rule_dataframe(key_list,run_rad)
    return rule_dataframe(config)


if __name__ == '__main__':
    main(cea.config.Configuration())
