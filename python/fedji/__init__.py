'''
Fedji is a database API for storing documents that are dictionaries whose
values are string, numbers, booleans or list of strings. It is very close
to (a subset of) what MongoDB does but with a few differences :

- If an attribute is a list one can write a query retrieving documents
  having this element in the list but it is also possible to query for
  an exact list value. MongoDB cannot query for exact list value.
- One can efficiently retrieve all the values for a given attribute
  given a filtering query. MongoDB cannot do that.

Moreover, MongoDB is speed efficient but is more complex than SQLite
to deploy and use (e.g. it requires a server) and uses a lot of disk
space (i.e. the Fedji MongoDB backend uses alot more space than the
SQLite backend).

This is why Fedji API exists. It is very close to MongoDB API but it
adds the missing features and can be used with several backends. To date,
two backends are supported : SQLite and MongoDB (however queriying on exact
list value is not implemented yet on MongoDB backend). A catidb backend
is planned.
'''