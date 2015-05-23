# -*- coding: utf-8 -*-
from flask import current_app

DEFAULT_PARENT_FIELD = "parent"
DEFAULT_LEAF_FIELD = "leaf"
DEFAULT_PATH_FIELD = "path"
DEFAULT_SEPARATOR = '.'


class TreeResourceConfigError(Exception):
    """ Exception used to raise errors because of config
    of the tree resource is invalid due invalid name fields"""
    pass


def build_config(app, resource, path_build_from,
                 parent=None, leaf=None, path=None, separator=None):
    """
    Return a config dictionary using the default values overriden by
    these ones that are present in keyword argument
    """
    # check that the resource exists
    if not resource in app.config['DOMAIN']:
        raise TreeResourceConfigError(
            "Invalid resource" +
            " `{}` it doesn't exist".format(resource)
        )

    # check that the path_build_from exists
    if not path_build_from in app.config['DOMAIN'][resource]['schema']:
        raise TreeResourceConfigError(
            "Invalid value" +
            " `{}` as path_build_from, invalid field".format(path_build_from)
        )

    # build the config for this resource
    config = {
        'PATH_BUILD_FROM': path_build_from,
        'PARENT': parent or DEFAULT_PARENT_FIELD,
        'LEAF': leaf or DEFAULT_LEAF_FIELD,
        'PATH': path or DEFAULT_PATH_FIELD,
        'SEPARATOR': separator or DEFAULT_SEPARATOR
    }

    # save the config of this resource to be used further in the
    # hooks or others code paths.
    app.config['DOMAIN'][resource]['APP-TREE-CONFIG'] = config
    return config


def get_config(resource):
    # return the config using the context app
    return current_app.config['DOMAIN'][resource]['APP-TREE-CONFIG']
