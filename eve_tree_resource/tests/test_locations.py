# -*- coding: utf-8 -*-

import os
import pytest
import json

from eve import Eve
from bson import ObjectId
from pymongo import MongoClient
from collections import namedtuple

from eve_tree_resource import treeify
from eve_tree_resource.tests.settings import (
    MONGO_HOST,
    MONGO_PORT,
    MONGO_DBNAME)


def parse_response(r):
    try:
        v = json.loads(r.get_data())
    except:
        v = None
    return v, r.status_code


def get(client, url):
    r = client.get(url)
    return parse_response(r)


def patch(client, url, data, headers=None):
    if headers is None:
        headers = []
    headers.append(('Content-Type', 'application/json'))
    r = client.patch(url, data=json.dumps(data), headers=headers)
    return parse_response(r)


def post(client, url, data, headers=None, content_type='application/json'):
    if headers is None:
        headers = []
    headers.append(('Content-Type', content_type))
    r = client.post(url, data=json.dumps(data), headers=headers)
    return parse_response(r)


def delete(client, url, headers=None):
    if headers is None:
        headers = []
    r = client.delete(url, headers=headers)
    return parse_response(r)


@pytest.fixture
def app():
    # preapre the mongodb database
    connection = MongoClient(MONGO_HOST, MONGO_PORT)
    connection.drop_database(MONGO_DBNAME)

    # build the Eve App using the settings where the locations
    # schema is configured
    directory = os.path.dirname(os.path.realpath(__file__))
    settings_file = os.path.join(directory, 'settings.py')
    app = Eve(settings=settings_file)

    # save the url
    url = app.config['DOMAIN']['locations']['url']

    # save a instance of test_client
    app.client = app.test_client()

    # treeify the resource
    treeify(app, "locations", 'name')

    # create a minimal tree node
    # World
    #  + Europe
    #     +  Andorra

    world, status_code = post(
        app.client, url,
        {'name': 'World', 'parent': None})

    europe = {
        'name': 'Europe',
        'parent': world["_id"]
    }
    response, _ = post(app.client, url, europe)
    europe.update(response)

    andorra = {
        'name': 'Andorra',
        'parent': europe["_id"]
    }
    response, _ = post(app.client, url, andorra)
    andorra.update(response)

    # return all that we need
    Fixture = namedtuple("Fixture", "app client url world europe andorra")
    return Fixture(
        app=app, client=app.client, url=url,
        world=world, europe=europe, andorra=andorra)


class TestLocations(object):
    """ Test all features using treeify using only the keyword concatenation
    to use the name as a field to build the path. All tests use a eve app
    fixture that has already a root node named `World`.
    """
    def test_insert(self, app):
        # test the root node
        world, status_code = get(
            app.client,
            "{}/{}".format(app.url, app.world["_id"]))

        assert not world['path']
        assert not world['leaf']

        # test the europe node
        europe, status_code = get(
            app.client,
            "{}/{}".format(app.url, app.europe["_id"]))

        assert europe['path'] == 'World.'
        assert not europe['leaf']

        # test the andorra node
        andorra, status_code = get(
            app.client,
            "{}/{}".format(app.url, app.andorra["_id"]))

        assert andorra['path'] == 'World.Europe.'
        assert andorra['leaf']

    def test_insert_invalid_parent(self, app):
        # then insert a child using a invalid parent
        location = {
            'name': 'America',
            'parent': str(ObjectId())
        }

        body, status_code = post(app.client, app.url, location)
        assert status_code == 400

    def test_update(self, app):
        # Update the Europe and then check that the
        # children have changed
        location = {
            'name': "Europess"
        }

        # get the whole register because etag has changed
        document, _ = get(
            app.client,
            "{}/{}".format(app.url, app.europe["_id"])
        )

        body, status_code = patch(
            app.client,
            "{}/{}".format(app.url, document["_id"]),
            location,
            headers=[('If-Match', document['_etag'])]
        )
        assert status_code == 200

        # get the andorra children
        andorra, status_code = get(
            app.client,
            "{}/{}".format(app.url, app.andorra["_id"]))

        assert andorra["path"] == "World.Europess."

    def test_delete(self, app):
        # Delete the Europe and then check that the
        # children have deleted

        # get the whole register because etag has changed
        document, _ = get(
            app.client,
            "{}/{}".format(app.url, app.europe["_id"])
        )

        # and delete it
        body, status_code = delete(
            app.client,
            "{}/{}".format(app.url, document["_id"]),
            headers=[('If-Match', document['_etag'])]
        )

        assert status_code == 204

        # try to get the andorra children
        body, status_code = get(
            app.client,
            "{}/{}".format(app.url, app.andorra["_id"]))

        assert status_code == 404

    def test_query_children(self, app):
        query = {"path": {'$regex': "^World."}}
        body, status_code = get(
            app.client,
            "{}?where={}".format(app.url, json.dumps(query)))
        assert status_code == 200

        items = body["_items"]
        assert len(items) == 2
        assert items[0]['name'] == "Europe"
        assert items[1]['name'] == "Andorra"

    def test_query_children_and_leafs(self, app):
        query = {"$and": [{"path": {'$regex': "^World."}}, {"leaf": True}]}
        body, status_code = get(
            app.client,
            "{}?where={}".format(app.url, json.dumps(query)))
        assert status_code == 200

        items = body["_items"]
        assert len(items) == 1
        assert items[0]['name'] == "Andorra"
