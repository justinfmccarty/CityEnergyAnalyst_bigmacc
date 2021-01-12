"""
For copying results at the end of the script before writing over them in a new loop simulation"""




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


def copy_results(locator, destination):
    """
    Copy the results from the scenario folder to the experiment's folder.

    :param cea.inputlocator.InputLocator locator: use the InputLocator to find source path
    :param string destination: path to the results folder
    :return: (this script doesn't return anything)
    """
    import distutils
    from distutils import dir_util


    distutils.dir_util.copy_tree(locator, destination)


def main(locator,destination):
    """
    Assign a new typology file to the input folder.

    :param cea.config.Configuration config: Configuration object for this script
    :return:
    """
    # assert os.path.exists(destination), 'Scenario not found: %s' % destination
    # locator = cea.inputlocator.InputLocator(config.scenario)

    copy_results(locator, destination)


if __name__ == '__main__':
    main(cea.config.Configuration())
