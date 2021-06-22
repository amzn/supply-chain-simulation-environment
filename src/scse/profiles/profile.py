"""
Manages the loading of profiles and instantiation of modules from configuration
"""

import logging
from os.path import join, dirname
import json
import importlib

logger = logging.getLogger(__name__)

# Helpful for testing.
def _minimal_profile_location():
    module_path = dirname(__file__)
    return join(module_path, 'minimal.json')


def load_profile(profile_configuration):
    module_path = dirname(__file__)

    try:
        fpath = join(module_path, profile_configuration + '.json')
        logger.debug("Open profile file = {}.".format(fpath))

        with open(fpath) as f:
            profile = json.load(f)

    except FileNotFoundError:
        fpath = profile_configuration
        logger.debug("Open profile file = {}.".format(fpath))

        with open(fpath) as f:
            profile = json.load(f)

    return profile


def instantiate_class(full_class_name, **parameters):
    last_dot = full_class_name.rindex('.')
    module_name = full_class_name[:last_dot]
    #logger.debug("module_name is {}".format(module_name))
    class_name = full_class_name[last_dot + 1:]

    module = importlib.import_module(module_name)
    agent_class = getattr(module, class_name)
    agent_instance = agent_class(parameters)

    return agent_instance
