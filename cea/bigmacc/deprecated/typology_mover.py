"""
The typology-mover script takes the typology file stored in the keylist directory and places it in the scenario folder.
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

def copy_typology_file(source_typology_file, locator):
    """
    Copy the typology file to the scenario's inputs from the experiment's folder.

    :param string source_typology_file: path to a typology file (``*.dbf``)
    :param cea.inputlocator.InputLocator locator: use the InputLocator to find output path
    :return: (this script doesn't return anything)
    """
    from shutil import copy
    assert os.path.exists(source_typology_file), "Could not find new typology file: {source_typology_file}".format(
        source_typology_file=source_typology_file
    )
    copy(source_typology_file, locator.get_building_typology())
    print("Set typology for scenario <{scenario}> to {source_typology_file}".format(
        scenario=os.path.basename(locator.scenario),
        source_typology_file=source_typology_file
    ))


def main(path,config):
    """
    Assign a new typology file to the input folder.

    :param cea.config.Configuration config: Configuration object for this script
    :return:
    """
    assert os.path.exists(config.scenario), 'Scenario not found: %s' % config.scenario
    locator = cea.inputlocator.InputLocator(config.scenario)

    copy_typology_file(path, locator)


if __name__ == '__main__':
    main(cea.config.Configuration())
