==================
Eve-tree-resources
==================

Sometimes we have to make some kind of queries against our collections where
the most optimized data structure is a tree. Eve tree resource is an attempt
to write a Eve app to cover your resources with a set of functionalities to 
get a tree shape, so make queries such as get the children of some document
using the properly indexes.

Cover your resource as a tree structure can be done using the 
`eve_tree_resource.treeify` function. It takes the initizlized Eve app the name
of the resource that you want to cover, and the field used to build
the Mongodb index.

.. code-block:: python

    from eve_tree_reresource import treeify
    from eve import Eve

    app = Eve()
    treeify(app, "resource", "field")
    app.run()
    
The `treeify` function will add thee new fields in you resource: `parent`, `path`
and `leaf`.

When a new document is inserted the user has to give the parent of the document,
using for that the `parent` field together with the other fields of your resource. 
As you can see into the next example:

.. code-block:: bash

    $ curl -i http://localhost/resource/ -d '{"parent": "521d6840c437dc0002d1203c"}'

Document will be inserted in the data base with the fields `parent`, `path` 
and `leaf` filled with the properly values to be used further to query you
resource as a tree.

The third param of `treeify` function has to be a field with one constraint, it has
to be unique than the other values that are in the same tree level, otherwise the consitence
of the data can't be secured.

For example, if your resource is a tree of geographical zones and you have a
field called `name` and it is used as a third field of the `treeify` fuction,
the `path` field will get values such as `Mejico.Barcelona.`,
`Spain.Catalunya.Barcelona.`, where equal names do not collision.

Considering the previous example, the `path` field is the concatenation of the `name`
field values of his parents separated by dots. It gets help of the monngodb
index implementation that uses BTrees [1]_, therefore we can get all children
of a specific document using the `path` field.

Next `curl` command shows how the query looks like:

.. code-block::bash

    $ curl http://localhost/locations/?where={"path": {"$regex": {"^Europe.France."}}

To get only the leafs we can expand the query with the properly condition as you
can see into the next example:

.. code-block::bash

    $ curl http://localhost/locations/?where={"$and":[{"path":" {"$regex": {^Europe.France/"}}},{"leaf":true}]}

The leaf attribute is handled automaticly, that means that the new documents
inserted are always set as leafs until it becomes parent of a child.

The previous queries only work if the mongo operator `regex` has not banned on use by the
`MONGO_QUERY_BLACKLIST` Eve config variable, otherwise `treeify` will raise an error.

The default fields names used by `parent`, `path` and `leaf` can be override by those ones
that you want to use. Next snippet shows that:

.. code-block:: python

    treeify(app, "locations", "name",
            parent="yourfield",
            leaf="yourleaffield",
            path="yourpathfield")

The separator char used to concatenate the diferent values for the `path` field can
be configured also as a keyword of the `treeify` function.
 

.. [1] http://zhangliyong.github.io/posts/2014/02/19/mongodb-index-internals.html
