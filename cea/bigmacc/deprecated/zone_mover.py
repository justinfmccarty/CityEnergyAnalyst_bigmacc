"""
The zone-mover script takes the zone file stored in the keylist directory and places it in the scenario folder.
"""




import os
import cea.config
import cea.inputlocator

__author__ = "Justin McCarty"
__copyright__ = ""
__credits__ = ["Justin McCarty"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = ""
__email__ = ""
__status__ = ""

def copy_zone_file(source_zone_file, locator):
    """
    Copy the typology file to the scenario's inputs from the experiment's folder.

    :param string source_zone_file: path to a typology file (``*.dbf``)
    :param cea.inputlocator.InputLocator locator: use the InputLocator to find output path
    :return: (this script doesn't return anything)
    """

    zone_output_path = locator.get_building_geometry_folder()

    from shutil import copy
    assert os.path.exists(source_zone_file), "Could not find new zone file: {source_zone_file}".format(
        source_zone_file=source_zone_file
    )
    copy(source_zone_file, zone_output_path)
    # print("Set new zone for scenario <{scenario}> to {source_zone_file}".format(
    #     scenario=os.path.basename(locator.scenario),
    #     source_zone_file=source_zone_file
    # ))


def main(path,config):
    """
    Assign a new zone file to the input folder.

    :param cea.config.Configuration config: Configuration object for this script
    :return:
    """
    assert os.path.exists(config.scenario), 'Scenario not found: %s' % config.scenario
    locator = cea.inputlocator.InputLocator(config.scenario)

    copy_zone_file(path, locator)


if __name__ == '__main__':
    main(cea.config.Configuration())
