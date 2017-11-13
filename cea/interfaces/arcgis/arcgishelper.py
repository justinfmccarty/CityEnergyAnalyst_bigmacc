"""
A library module with helper functions for creating the City Energy Analyst python toolbox for ArcGIS.
"""
import os
import subprocess
import tempfile

import cea.config
import cea.inputlocator
from cea.interfaces.arcgis.modules import arcpy

LOCATOR = cea.inputlocator.InputLocator(None)
CONFIG = cea.config.Configuration(cea.config.DEFAULT_CONFIG)

def add_message(msg, **kwargs):
    """Log to arcpy.AddMessage() instead of print to STDOUT"""
    if len(kwargs):
        msg %= kwargs
    arcpy.AddMessage(msg)
    log_file = os.path.join(tempfile.gettempdir(), 'cea.log')
    with open(log_file, 'a') as log:
        log.write(str(msg))


def is_db_weather(weather_path):
    """True, if the ``weather_path`` is one of the pre-installed weather files that came with the CEA"""
    weather_name = get_db_weather_name(weather_path)
    if weather_name in LOCATOR.get_weather_names():
        # could still be a custom weather file...
        db_weather_path = LOCATOR.get_weather(weather_name)
        db_weather_path = os.path.normpath(db_weather_path)
        db_weather_path = os.path.normcase(db_weather_path)

        weather_path = LOCATOR.get_weather(weather_path)
        weather_path = os.path.normpath(weather_path)
        weather_path = os.path.normcase(weather_path)

        if os.path.dirname(db_weather_path) == os.path.dirname(weather_path):
            return True
    return False


def get_db_weather_name(weather_path):
    weather_name = os.path.splitext(os.path.basename(weather_path))[0]
    return weather_name


def get_python_exe():
    """Return the path to the python interpreter that was used to install CEA"""
    try:
        with open(os.path.expanduser('~/cea_python.pth'), 'r') as f:
            python_exe = f.read().strip()
            return python_exe
    except:
        raise AssertionError("Could not find 'cea_python.pth' in home directory.")


def get_environment():
    """Return the system environment to use for the execution - this is based on the location of the python
    interpreter in ``get_python_exe``"""
    root_dir = os.path.dirname(get_python_exe())
    scripts_dir = os.path.join(root_dir, 'Scripts')
    env = os.environ.copy()
    env['PATH'] = ';'.join((root_dir, scripts_dir, os.environ['PATH']))
    return os.environ


def _cli_output(scenario=None, *args):
    """Run the CLI in a subprocess without showing windows and return the output as a string, whitespace
    is stripped from the output"""
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    command = [get_python_exe(), '-m', 'cea.interfaces.cli.cli']
    if scenario:
        command.append('--scenario')
        command.append(scenario)
    command.extend(args)

    result = subprocess.check_output(command, startupinfo=startupinfo, env=get_environment())
    return result.strip()


def write_config_string(scenario, section, key, value):
    """Write a string value to the configuration file"""
    run_cli(scenario, 'write-config', '--section', section, '--key', key, '--value', value)


def write_config_boolean(scenario, section, key, value):
    """Write a boolean value to the configuration file"""
    value = 'true' if value else 'false'
    run_cli(scenario, 'write-config', '--section', section, '--key', key, '--value', value)


def run_cli(script_name, **parameters):
    """Run the CLI in a subprocess without showing windows"""
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    command = [get_python_exe(), '-u', '-m', 'cea.interfaces.cli.cli', script_name]
    for parameter_name, parameter_value in parameters.items():
        parameter_name = parameter_name.replace('_', '-')
        command.append('--' + parameter_name)
        command.append(str(parameter_value))
    add_message('Executing: ' + ' '.join(command))
    process = subprocess.Popen(command, startupinfo=startupinfo, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               env=get_environment(), cwd=tempfile.gettempdir())
    while True:
        next_line = process.stdout.readline()
        if next_line == '' and process.poll() is not None:
            break
        add_message(next_line.rstrip())
    stdout, stderr = process.communicate()
    add_message(stdout)
    add_message(stderr)
    if process.returncode != 0:
        raise Exception('Tool did not run successfully')


def parse_boolean(s):
    """Return True or False, depending on the value of ``s`` as defined by the ConfigParser library."""
    boolean_states = {'0': False,
                      '1': True,
                      'false': False,
                      'no': False,
                      'off': False,
                      'on': True,
                      'true': True,
                      'yes': True}
    if s.lower() in boolean_states:
        return boolean_states[s.lower()]
    return False


def is_builtin_weather_path(weather_path):
    """Return True, if the weather path resolves to one of the builtin weather files shipped with the CEA."""
    if weather_path is None:
        return False
    return os.path.dirname(weather_path) == os.path.dirname(LOCATOR.get_weather('Zug'))


def demand_graph_fields(scenario):
    """Lists the available fields for the demand graphs - these are fields that are present in both the
    building demand results files as well as the totals file (albeit with different units)."""
    import pandas as pd
    locator = cea.inputlocator.InputLocator(scenario)
    df_total_demand = pd.read_csv(locator.get_total_demand())
    total_fields = set(df_total_demand.columns.tolist())
    first_building = df_total_demand['Name'][0]
    df_building = pd.read_csv(locator.get_demand_results_file(first_building))
    fields = set(df_building.columns.tolist())
    fields.remove('DATE')
    fields.remove('Name')
    # remove fields in demand results files that do not have a corresponding field in the totals file
    bad_fields = set(field for field in fields if not field.split('_')[0] + "_MWhyr" in total_fields)
    fields = fields - bad_fields
    return list(fields)


def create_weather_parameters(config):
    """Create the ``weather_name`` and ``weather_path`` parameters used for choosing the weatherfile."""
    weather_name = arcpy.Parameter(
        displayName="Weather file (choose from list or enter full path to .epw file)",
        name="weather_name",
        datatype="String",
        parameterType="Required",
        direction="Input")
    weather_name.filter.list = LOCATOR.get_weather_names() + ['<custom>']
    weather_name.value = get_db_weather_name(config.weather) if is_db_weather(config.weather) else '<custom>'
    weather_path = arcpy.Parameter(
        displayName="Path to .epw file",
        name="weather_path",
        datatype="DEFile",
        parameterType="Optional",
        direction="Input")
    weather_path.filter.list = ['epw']
    weather_path.value = config.weather
    weather_path.enabled = not is_db_weather(config.weather)
    return weather_name, weather_path


def check_senario_exists(parameters):
    """Makes sure the scenario exists. Create a dictionary of the parameters at the same time"""
    parameters = {p.name: p for p in parameters}
    scenario_parameter = parameters['general:scenario']
    scenario = scenario_parameter.valueAsText
    if scenario is None:
        config = cea.config.Configuration()
        scenario_parameter.value = config.scenario
    else:
        scenario_parameter.value = scenario
    #if not os.path.exists(scenario):
    #    scenario_parameter.setErrorMessage('Scenario folder not found: %s' % scenario)
    return scenario, parameters


def check_radiation_exists(parameters, scenario):
    """Make sure the radiation files exist."""
    locator = cea.inputlocator.InputLocator(scenario)
    radiation_csv = locator.get_radiation()
    if not os.path.exists(radiation_csv):
        parameters['scenario'].setErrorMessage("No radiation file found - please run radiation tool first")
    if not os.path.exists(locator.get_surface_properties()):
        parameters['scenario'].setErrorMessage("No radiation data found for scenario. Run radiation script first.")


def update_weather_parameters(parameters):
    """Update the weather_name and weather_path parameters"""
    parameters['weather_path'].enabled = parameters['weather_name'].value == '<custom>'
    weather_path = parameters['weather_path'].valueAsText
    if is_builtin_weather_path(weather_path):
        parameters['weather_path'].enabled = False
        parameters['weather_name'].value = get_db_weather_name(weather_path)
    if parameters['weather_name'].value != '<custom>':
        parameters['weather_path'].value = LOCATOR.get_weather(parameters['weather_name'].value)


def get_weather_path_from_parameters(parameters):
    """Return the path to the weather file to use depending on wether weather_name or weather_path is set by user"""
    if parameters['weather_name'].value == '<custom>':
        return parameters['weather_path'].valueAsText
    else:
        return LOCATOR.get_weather(parameters['weather_name'].value)


def get_parameter_object(section_name, parameter_name):
    """Create an arcpy Parameter object based on the configuration in the Default-config.
    The name is set to "section_name:parameter_name" so parameters created with this function are
    easily identified (```':' in parameter.name``)"""
    cea_parameter = CONFIG.parameter(section_name, parameter_name)
    data_type_map = {
        cea.config.PathParameter: 'DEFolder',
        cea.config.StringParameter: 'String',
        cea.config.BooleanParameter: 'GPBoolean',
        cea.config.RealParameter: 'GPDouble',
        cea.config.IntegerParameter: 'GPInteger'
    }
    data_type = data_type_map[type(cea_parameter)]
    return arcpy.Parameter(
        displayName="Path to the scenario",
        name="%(section_name)s:%(parameter_name)s" % locals(),
        datatype=data_type,
        parameterType="Required",
        direction="Input")


def dict_parameters(parameters):
    return {p.name: p for p in parameters}


def initialize_parameters(parameters):
    parameters = dict_parameters(parameters)
    config = cea.config.Configuration()
    for parameter in parameters.values():
        if ':' in parameter:
            section_name, parameter_name = parameter.split(':')
            # parameter was created by get_parameter_object
            if parameter.value is None:
                parameter.value = getattr(getattr(config, section_name), parameter_name)

    return parameters