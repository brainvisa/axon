def fedji_connect(url):
    '''
    Create a FEDJI database connection according to the given URL. The
    URL has the following form : <backend>:[<protocol>:]//<path> where
    <backend> can be one of the following:
    sqlite : An implementation for a single client (not thread safe) using
             sqlite. For this backend, <protocol> must be empty and path
             must be either a non existing directory that will be created
             or a directory previously created by a FEDJI SQLite backend.
    mongodb : Not finished yet, raises an error if used. An implementation
              based on MongoDB.
    catidb : Not implemented yet. A read-only implementation based on
             Cubicweb with catidb schema.
    '''
    backend, protocol_path = url.split(':', 1)
    if backend == 'sqlite':
        from .sqlite_backend import FedjiSqlite
        if not protocol_path.startswith('//'):
            raise ValueError('Invalid FEDJI urL for sqlite backend: %s' % url)
        path = protocol_path[2:]
        return FedjiSqlite(path)
    elif backend == 'mongodb':
        raise NotImplementedError()
    elif backend == 'catidb':
        raise NotImplementedError()
