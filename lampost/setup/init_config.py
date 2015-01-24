import logging
import os
import yaml
import glob
from yaml.parser import ParserError

log = logging.getLogger(__name__)


def load_config(path):
    if os.path.isfile(path):
        return parse_yaml([path])

    yaml_file = '{}.yaml'.format(path)
    if os.path.isfile(yaml_file):
        return parse_yaml([yaml_file])

    if os.path.isdir(path):
        yaml_files = glob.glob('{}/*.yaml'.format(path))
        if yaml_files:
            return parse_yaml(yaml_files)


def parse_yaml(yaml_files):
    all_config = []
    for yaml_file in yaml_files:
        with open(yaml_file, 'r') as yf:
            try:
                yaml_load = yaml.load(yf)
                all_config.append(yaml_load)
            except ParserError:
                log.exception("Error parsing {}", yaml_file)

    return all_config




if __name__ == '__main__':

    load_config('../../conf')
