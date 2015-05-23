# -*- coding: utf-8 -*-

from functools import partial
from flask import current_app
from flask import abort
from json import dumps

from eve.utils import ParsedRequest
from eve.methods.patch import patch_internal

from tree_resource.config import get_config


def register_hooks(app, resource):
    """ Registere all hooks needed for all CRUD operations to make
    sure that the tree fields are handled rightly and each operation
    leave the mongodb collection consistent.
    """
    hooks = {
        'on_insert_{resource}': hook_on_insert,
        'on_inserted_{resource}': hook_on_inserted,
        'on_updated_{resource}': hook_on_updated,
        'on_deleted_item_{resource}': hook_on_deleted
    }

    for eve_hook, func in hooks.items():
        resourcered_hook = eve_hook.format(resource=resource)
        resourcered_function = partial(func, resource)
        f = getattr(app, resourcered_hook)
        f += resourcered_function


def hook_on_insert(resource, items):
    """ Called before to run one insert operation for a list of items.

    It checks for each parent that this exists otherwise an 400 error is
    returned.

    For each item fills the `path` field with the `path` value of its
    parents plus the `path_field_from` field of the parent separeted by
    one dot.
    """
    config = get_config(resource)
    for item in items:
        if not item[config['PARENT']]:
            # special case for root Node
            item[config['PATH']] = None
            item[config['LEAF']] = True
            continue

        parent = current_app.data.find_one_raw(
            resource,
            item[config['PARENT']])
        if not parent:
            error = "Item `{}` has one invalid parent `{}`".format(
                item[config['PATH_BUILD_FROM']],
                item[config['PARENT']]
            )
            abort(400, description=str(error))

        item[config['LEAF']] = True
        build_path_field(config, item, parent)


def hook_on_inserted(resource, items):
    """ Called after run one insert operation for a list of items.
    It sets for each parent the leaf as False.
    """
    config = get_config(resource)
    processed = []
    for item in items:
        parent_id = item[config['PARENT']]

        # root node
        if not parent_id:
            continue

        # for bulk operations with the children that belong to the
        # same parent
        if parent_id in processed:
            continue

        patch_internal(
            resource, {config['LEAF']: False},
            concurrency_check=False,
            skip_validation=True,
            **{current_app.config['ID_FIELD']: parent_id}
        )

        processed.append(parent_id)


def hook_on_updated(resource, updates, original):
    """ called after to run on update operation """
    config = get_config(resource)

    # couple of situations where we have to do nothing because
    # `PATH_BUILD_FROM` field has not changed
    if config['PATH_BUILD_FROM'] not in updates:
        return

    if updates[config['PATH_BUILD_FROM']] ==\
            original[config['PATH_BUILD_FROM']]:
        return

    # get all children that belong to the path of the document
    path = original[config['PATH']] +\
        original[config['PATH_BUILD_FROM']] +\
        config['SEPARATOR']

    r = ParsedRequest()
    r.where = dumps({config['PATH']: {'$regex': "^{}".format(path)}})
    r.max_resuls = 0
    children = current_app.data.find(resource, r, None)

    # Then update each child, where the old path has to be updated
    # with the right one.
    path_build_from = updates[config['PATH_BUILD_FROM']]
    level_path_parent = len(original[config['PATH']].split(".")) - 1\
        if original[config['PATH']] else 0

    for child in children:
        # build the new path using the old path as a first part
        # and the last part, only replacement of the field value changed
        old_path = child[config['PATH']].split(config['SEPARATOR']) or []
        new_path = config['SEPARATOR'].join(
            old_path[:level_path_parent] +
            [path_build_from] +
            old_path[level_path_parent+1:])

        # finally udpate the document
        current_app.data.update(
            resource,
            child[current_app.config['ID_FIELD']],
            {config['PATH']: new_path},
            child
        )


def hook_on_deleted(resource, item):
    """ called after to run one delete operation """
    config = get_config(resource)

    # remove all children belonging to the item deleted
    if item[config['LEAF']]:
        return

    path = item[config['PATH']] +\
        item[config['PATH_BUILD_FROM']] + config['SEPARATOR']

    current_app.data.remove(
        resource,
        {config['PATH']: {'$regex': "^{}".format(path)}})


def build_path_field(config, child, parent):
    # build the path field as x.y.z.<path_build_from> getting
    # the x.y.z from the parent and concatening the .<path_build_from>

    # All paths have the SEPARATOR as the last character to avoid
    # wrong results.
    if not parent[config['PATH']]:
        # root parent has not path field filled
        child[config['PATH']] =\
            parent[config['PATH_BUILD_FROM']] + config['SEPARATOR']
    else:
        child[config['PATH']] =\
            parent[config['PATH']] + parent[config['PATH_BUILD_FROM']] +\
            config['SEPARATOR']
