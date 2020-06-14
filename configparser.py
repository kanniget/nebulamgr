import yaml


##
#
# Copied from   https://pypi.org/project/yaml-config-parser/  which has not been maintained in years
#
# Fixed the Loader warnings.add()
#
##


class ConfigParser(object):
    @classmethod
    def __init__(cls, config_file):
        cls.config_file = config_file
        try:
            cls.configs = yaml.load(open(cls.config_file, "r"), Loader=yaml.FullLoader)
        except AttributeError:
            cls.configs = yaml.load(open(cls.config_file, "r"))

    @classmethod
    def get_config(cls, section=None, key=None):
        if not cls.configs:
            cls.configs = yaml.load(open(cls.config_file, "r"))
        section_configs = cls.configs.get(section, None)
        if section_configs is None:
            raise NotImplementedError

        if not key:
            return section_configs
        else:
            value = section_configs.get(key, None)
        if value is None:
            raise NotImplementedError
        return value
