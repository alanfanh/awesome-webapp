# -*- coding:utf-8 -*-
import config_default


class Dict(dict):
    """
    Simple dict but support access as x.y style.
    """

    def __init__(self, names=(), values=(), **kw):
        super(Dict, self).__init__(**kw)
        for k, v in zip(names, values):
            self[k] = v

    def __getattribute__(self, key) -> None:
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Dict' object has no attribute '%s'" % key)

    def __setattr__(self, key, value) -> None:
        self[key] = value


def merge(defaults, override):
    # 合并两个配置文件中的配置信息
    r = {}
    for k, v in defaults.items():
        if k in override:
            if isinstance(v, dict):
                r[k] = merge(v, override[k])
            else:
                r[k] = override[k]
        else:
            r[k] = v
    return r


def to_dict(d):
    config_dict = Dict()
    for k, v in d.items():
        config_dict[k] = to_dict(v) if isinstance(v, dict) else v
    return config_dict


configs = config_default.configs

try:
    import config_override

    configs = merge(configs, config_override.configs)
except ImportError:
    pass

configs = to_dict(configs)
