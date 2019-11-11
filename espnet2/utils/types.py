import argparse
import copy
from distutils.util import strtobool
from typing import Optional

import yaml
from typeguard import typechecked


@typechecked
def str2bool(value: str) -> bool:
    return bool(strtobool(value))


@typechecked
def int_or_none(value: Optional[str]) -> Optional[int]:
    if value is None:
        return value
    if value.lower() in ('none', 'null', 'nil'):
        return None
    return int(value)


@typechecked
def str_or_none(value: Optional[str]) -> Optional[str]:
    if value is None:
        return value
    if value.lower() in ('none', 'null', 'nil'):
        return None
    return value


class NestedDictAction(argparse.Action):
    """

    Examples:
        >>> parser = argparse.ArgumentParser()
        >>> _ = parser.add_argument('--conf', action=NestedDictAction,
        ...                         default={'a': 4})
        >>> parser.parse_args(['--conf', 'a=3', '--conf', 'c=4'])
        Namespace(conf={'a': 3, 'c': 4})
        >>> parser.parse_args(['--conf', 'c.d=4'])
        Namespace(conf={'a': 4, 'c': {'d': 4}})
        >>> parser.parse_args(['--conf', 'c.d=4', '--conf', 'c=2'])
        Namespace(conf={'a': 4, 'c': 2})
        >>> parser.parse_args(['--conf', '{a: 5, c: 9}'])
        Namespace(conf={'a': 5, 'c': 9})
        >>> parser.parse_args(['--conf', 'e.f=[0, 1, 2]'])
        Namespace(conf={'a': 4, 'e': {'f': [0, 1, 2]}})

    """
    def __init__(self,
                 option_strings,
                 dest,
                 nargs=None,
                 default = None,
                 choices=None,
                 required=False,
                 help=None,
                 metavar=None):
        if default is None:
            default = {}
        if not isinstance(default, dict):
            raise TypeError('default must be dict: {}'.format(type(default)))

        super().__init__(
            option_strings=option_strings,
            dest=dest,
            nargs=nargs,
            default=default.copy(),
            choices=choices,
            required=required,
            help=help,
            metavar=metavar,
        )

    def __call__(self, parser, namespace, values, option_strings=None):
        # --{option} a.b=3 -> {'a': {'b': 3}}
        if '=' in values:
            indict = copy.deepcopy(getattr(namespace, self.dest, {}))
            key, value = values.split('=', maxsplit=1)
            if not value.strip() == '':
                value = yaml.load(value, Loader=yaml.Loader)

            keys = key.split('.')
            d = indict
            for idx, k in enumerate(keys):
                if idx == len(keys) - 1:
                    d[k] = value
                else:
                    v = d.setdefault(k, {})
                    if not isinstance(v, dict):
                        # Overwrite
                        d[k] = {}
                    d = d[k]
            # Update the value
            setattr(namespace, self.dest, indict)
        else:
            try:
                # At the first, try eval(), i.e. Python syntax dict,
                # for internal behaviour of configargparse
                # e.g. --{option} "{'a': 3}" -> {'a': 3}
                value = eval(values, {}, {})
                if isinstance(value, dict):
                    raise ValueError
            except Exception:
                # and the second, try yaml.load
                value = yaml.load(values, Loader=yaml.Loader)
                # Must be dict
                if not isinstance(value, dict):
                    raise ValueError
            # Overwrite
            setattr(namespace, self.dest, value)


if __name__ == '__main__':
    import doctest
    doctest.testmod()

