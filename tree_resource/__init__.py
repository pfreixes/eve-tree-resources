# -*- coding: utf-8 -*-
"""
Eve tree resource covers your Eve resource with the needed fields and
hooks tho handle this resource as a tree.
"""
from tree_resource.hooks import register_hooks
from tree_resource.config import build_config

try:
    # 0.6 Eve vesion comes with creation index suport
    # along with the schema
    from eve.io.mongo.mongo import create_index
except ImportError:
    from tree_resource.mongo import create_index as create_index_internal
    create_index = None


def treeify(app, resource, path_build_from, parent=None, leaf=None,
            path=None, separator=None):
    """ Cover the `resource` published in `eve_app` with a few fields
    such as `parent`, `leaf` and `path` to get a tree shape.

    The `path` field is build concatenating the `path_build_from` field of all
    parent nodes until reach the root.

    This field has to be unique for the same tree leve, for example it can be
    a field name of a location where duplicate values exist in
    different zones:

        World.Europe.Spain.Catalunya.Barcelona
        World.Mexico.Barcelona

    Use another fields than the default onees settting the `parent`,
    `path` or `leaf` keywords with the name fields that you want to use.

    :raises: TreeResourceConfigError
    """
    if "$regex" in app.config['MONGO_QUERY_BLACKLIST']:
        raise Exception("eve-tree-resource uses regex as a operator to get"
                        " children from one resource, enable it removing from"
                        " MONGO_QUERY_BLACKLIST")

    config = build_config(
        app, resource, path_build_from,
        parent=parent, leaf=leaf, path=path, separator=separator)

    tree_schema = {
        config['LEAF']: {
            'type': 'boolean',
            'readonly': True
        },
        config['PATH']: {
            'type': 'string',
            'readonly': True
        },
        config['PARENT']: {
            'type': 'objectid',
            'required': True,
            'nullable': True  # Root node
        }
    }

    # add the new fields to the schema of resource and
    # if it is possilbe also the index description
    settings = app.config['DOMAIN'][resource]
    settings['schema'].update(tree_schema)

    if create_index:
        index_definition = {config['PATH']: [(config['PATH'], 1)]}
        settings['mongo_indexes'] =\
            settings.get('mongo_indexes', {}).update(index_definition)

    # publish again the resource to Eve, projection is only
    # set back if it is empty, therefore we have to leave it
    # as None to find out this issue.
    # FIXME: because of that projections set along with the
    # config file doesn't work
    settings['datasource']['projection'] = None
    app.register_resource(resource, settings)

    if not create_index:
        # Eve version has no support for create mongodb indexes,
        # create these by `hand`.
        create_index_internal(
            app,
            resource,
            config['PATH'],
            [(config['PATH'], 1)],
            {}
        )

    # update the hooks
    register_hooks(app, resource)
