import logging.config
import os
import yaml

import coloredlogs
import verboselogs

from pathlib import Path


def get_logging_dict():
    config_dict = None

    conf_path = Path("../configs/config_logging.yaml")
    if conf_path.exists():
        with open(conf_path, 'rt') as f:
            config_dict = yaml.safe_load(f.read())

    return config_dict


def setup_logging(config_dict, default_level=logging.DEBUG):
    """Setup logging configuration

    """
    verboselogs.install()
    coloredlogs.install()

    if config_dict is not None:
        log_file_path = Path(config_dict["handlers"]["file_handler"]["filename"])
        log_file_path.parent.mkdir(parents=True, exist_ok=True)

        logging.config.dictConfig(config_dict)
    else:
        logging.basicConfig(level=default_level)

    old_factory = logging.getLogRecordFactory()

    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)

        module = os.getcwd().split("/")[-1]
        path_name = record.pathname.split("/")

        if module in path_name:
            id_mod = path_name.index(module)
            record.shortpath = "/".join(path_name[id_mod:])
        else:
            record.shortpath = module + "/" + path_name[-1]

        record.shortpath = ("..."+record.shortpath[-35:]) if len(record.shortpath) > 35 else record.shortpath
        
        return record

    logging.setLogRecordFactory(record_factory)

def set_log_level(log_level_name):
    numeric_level = getattr(logging, log_level_name.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % log_level_name)

    for handler in log.handlers:
        handler.setLevel(numeric_level)
        
# Instantiate the logger
setup_logging(get_logging_dict())
log = logging.getLogger('multipi')  # this is the global logger