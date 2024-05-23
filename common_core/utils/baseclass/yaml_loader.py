from common_core.utils.yaml import load_yaml


class YAMLLoader:
    def __init__(self, yaml_filepath):
        self._yaml_dct: dict = {}
        if isinstance(yaml_filepath, list):
            for yfp in yaml_filepath:
                if yaml := self._load_yaml_file(yfp):
                    self._yaml_dct.update(yaml)
        elif isinstance(yaml_filepath, str):
            if yaml := self._load_yaml_file(yaml_filepath):
                self._yaml_dct = yaml

    @classmethod
    def _load_yaml_file(cls, filename=None):
        if filename:
            try:
                return load_yaml(filename)
            except FileNotFoundError:
                pass
        return {}

    @property
    def asdict(self):
        return self._yaml_dct
