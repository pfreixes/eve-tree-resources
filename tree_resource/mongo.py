# -*- coding: utf-8 -*-
"""
This funciton has been get from the Python-Eve master branch to overcome
the issue that versions lower than 0.6 has not support to declare and create
indexes along with the schema.

This module is not used if the create_index function is already present
in the `eve.io.mongo.mongo` module.
"""
import pymongo

from copy import copy


def create_index(app, resource, name, list_of_keys, index_options):
    """ Create a specific index composed of the `list_of_keys` for the
    mongo collection behind the `resource` using the `app.config`
    to retrieve all data needed to find out the mongodb configuration.
    The index is also configured by the `index_options`.

    Index are a list of tuples setting for each one the name of the
    fields and the kind of order used, 1 for ascending and -1 for
    descending.

    For example:
        [('field_name', 1), ('other_field', -1)]

    Other indexes such as "hash", "2d", "text" can be used.

    Index options are a dictionary to set specific behaviour of the
    index.

    For example:
        {"sparse": True}

    .. versionadded:: 0.6
    """
    # it doesn't work as a typical mongodb method run in the request
    # life cicle, it is just called when the app start and it uses
    # pymongo directly.
    collection = app.config['SOURCES'][resource]['source']
    config_prefix = app.config['DOMAIN'][resource].get('mongo_prefix', 'MONGO')

    def key(suffix):
        return '%s_%s' % (config_prefix, suffix)

    db_name = app.config[key('DBNAME')]

    # just reproduced the same behaviour for username
    # and password, the other fields come set by Eve by
    # default.
    username = app.config[key('USERNAME')]\
        if key('USERNAME') in app.config else None
    password = app.config[key('PASSWORD')]\
        if key('PASSWORD') in app.config else None
    host = app.config[key('HOST')]
    port = app.config[key('PORT')]
    auth = (username, password)
    host_and_port = '%s:%s' % (host, port)
    conn = pymongo.MongoClient(host_and_port)
    db = conn[db_name]

    if any(auth):
        db.authenticate(username, password)

    coll = db[collection]

    kw = copy(index_options)
    kw['name'] = name

    try:
        return coll.create_index(list_of_keys, **kw)
    except pymongo.errors.OperationFailure as e:
        if e.code == 85:
            # This error is raised when the definition of the index has
            # been changed, we didn't found any spec out there but we
            # think tat this error is not going to change and we can trust.

            # by default, drop the old index with old configuration and
            # create the index againt with the new configuration
            coll.drop_index(name)
            return coll.create_index(list_of_keys, **kw)
        else:
            raise
