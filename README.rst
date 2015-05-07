=================
Eve-tree-resource
=================

Sometimes we have to make some kind of queries against our collections where
the most optimized data structure is a tree. Eve tree resource is an attempt
to write a Eve app to cover your resources with a set of functionalityes to 
get tree shape, so make queries such as get the children of some document
using the properly Mongo indexes.

Cover your resource with a tree structure can be done using the 
`eve_treeresource.treeify` function. It takes the name of the resource that 
you want to cover and the initizlized Eve app.

.. code-block:: python

    from eve_treeresource import treeify
    from eve import Eve

    app = Eve()
    treeify("resource name", app)
    app.run()
    
To make the properly queries `treeify` will add thee new fields in you resource:
`parent`, `path` and `leaf`.

When a new document is saved, the user can set the parent of this document
setting the `parent` field along with the other fields of your resource, as 
you can see into the next:

.. code-block:: bash

    $ curl -i http://localhost/resource/ -d '{"parent": "521d6840c437dc0002d1203c"}'

Document will be inserted in the data base with the fields `parent`, `path` 
and `leaf` filled with the properly values to be used further to query you
resource as a tree shape.

If you want to use another field to get the relation between
two nodes you can configure it with the keyword `relation_field` in the treeify
function, by defautl it uses the `_id` field. 

Current implemenation do not implement any kind of restriction for the value
of `relation_field`, therefore duplicate values in the same tree level have
to be avoided. 

For example, if your resource is a tree of geographical zones and you have a
unique field called `name` you can use it as you can see in the next example:

.. code-block:: pythony

    treeify("locations", app, relation_field="name")
    
Also the default name of the fields `parent`, `path` and `leaf` can be
override for as you can see into the next example:

.. code-block:: pythony
    treeify("locations", app, relation_field="name",
            parent_field="yourfield",
            leaf_field="yourleaffield",
            path_field="yourpathfield")
    
The path field is always the concatenation of the `relation_field` values of his
parents separated by dots. It gets help of the monngodb index implementation
that uses BTrees [1]_, therefore we can get all children of a specific document using
the `path` field.

For example considering the zones resource where we used the field `name` we
can get all children of location with a query like that:

.. code-block::bash

    $ curl http://localhost/locations/?where={"path":"Europe.France.*"}

To get only the leafs we can expand the query with the properly condition as you
can see into the next example:

.. code-block::bash

    $ curl http://localhost/locations/?where={"$and":[{"path":"Europe.France.*"},{"leaf":true}]}

The leaf attribute is handled automaticly, that means that the new documents
inserted are always set as leafs until it becomes parent of a child. This behaviour
can be disabled with the `handle_leafs` attribute of `treefy` function.


.. code-block:: pythony

    treeify("locations", app, relation_field="name", handle_leafs=False)

In that case the responsability is borrowed to the user or the main application.


.. [1] http://zhangliyong.github.io/posts/2014/02/19/mongodb-index-internals.html