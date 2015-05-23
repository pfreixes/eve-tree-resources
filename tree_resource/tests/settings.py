DOMAIN = {
    'locations': {
        'schema': {
            'name': {'type': 'string'}
        }
    }
}

MONGO_QUERY_BLACKLIST = ['$where']
RESOURCE_METHODS = ['GET', 'POST']
ITEM_METHODS = ['GET', 'PATCH', 'DELETE']
MONGO_DBNAME = 'test_eve_tree_resources'
MONGO_HOST = 'localhost'
MONGO_PORT = 27017
DEBUG = True
