# -*- coding: utf-8 -*-

import os
import pytest

from json import dumps
from pymongo import MongoClient
from collections import namedtuple

from eve_tree_resources import treeify
from eve_tree_resources.tests.settings import MONGO_HOST,
    MONGO_PORT, MONGO_DBNNAME

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
  
    # treeify the resource
    treeify("locations", concatenation='name')

    # create a minimal tree node
    # World
    #  + Europe
    #     +  Andorra
    world = app.test_client.post(url, {'name': 'World'}).json()
    europe = {
        'name': 'Europe',
        'parent' : world["_id"]
    }
    europe.update(app.test_client.post(app.url, europe).json())
    location = {
        'name': 'Andorra',
        'parent' : europe["_id"]
    }
    andorra.update(app.test_client.post(url, andorra).json())

    # return all that we need
    return namedtuple("Fixture", "app api url world europe andorra")\
        (app=app, api=app.test_client, url=url,
         world=world, europe=europe, andorra=andorra)


class TestLocations(object):
    """ Test all features using treeify using only the keyword concatenation
    to use the name as a field to build the path. All tests use a eve app
    fixture that has already a root node named `World`.
    """
    def test_insert(self, app):
        # test the root node
        assert app.world['path'] == None
        assert app.world['leaf'] == False

        # test the europe node
        assert app.europe['path'] == 'World'
        assert app.europe['leaf'] == False

        # test the andorra node
        assert app.andorra['path'] == 'World.Europe'
        assert app.andorra['leaf'] == True


     def test_insert_invalid_parent(self, app):
        # then insert a child using a invalid parent
        location = {
            'name': 'Europe',
            'parent' : 'invalid'
        }

        result = app.api.post(app.url, location)
        assert result.status_code == 400

    def test_update(self, app):
        # Update the Europe and then check that the
        # children have changed
        location = {
            'name' : "Europess"
        }

        result = app.api.post(app.url, location)
        assert result.status_code == 200

        # get the andorra children
        andorra = app.api.get(
            "{}/{}".format(app.url, app.andorra["_id"])).json()

        assert andorra["path"] == "World.Europess"

    def test_delete(self, app):
        # Delete the Europe and then check that the
        # children have deleted
        result = app.api.delete("{}/{}".format(app.url, app.europe["_id"]))
        assert result.status_code == 200

        # try to get the andorra children
        result = app.api.get(
            "{}/{}".format(app.url, app.andorra["_id"]))

        assert result.status_code == 404

    def test_query_children(self, app_fixture):
        query = {"path": "World.*"}
        result = app.api.get("{}?where={}".format(app.url, dumps(query)))
        assert result.status_code = 200
        
        items = result.json()["_items"]
        assert len(items) == 2
        assert items[0]['name'] == "Europe"
        assert items[1]['name'] == "Andorra"

    def test_query_children_and_leafs(self, app_fixture):
        query = {"$and": [{"path": "World.*"}, {"leaf": True}]}
        result = app.api.get("{}?where={}".format(app.url, dumps(query)))
        assert result.status_code = 200
        
        items = result.json()["_items"]
        assert len(items) == 2
        assert items[0]['name'] == "Europe"
        assert items[1]['name'] == "Andorra"



