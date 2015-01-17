import logging
import os
import yaml
import glob
from yaml.parser import ParserError

log = logging.getLogger(__name__)


def load_config(path, main_conf='main'):

    all_config = []

    def add_yaml(yaml_file):
        with open('{}/{}.yaml'.format(path, file_name), 'r') as yf:
            try:
                yaml_load = yaml.load(yf)
                all_config.append(yaml_load)
                for include_name in yaml_load['includes']:
                    add_yaml(include_name)
            except ParserError:
                log.exception("Error parsing {}", yaml_file)

    add_yaml(path, main_conf)
    return all_config


if __name__ == '__main__':

    load_config('../../conf')
