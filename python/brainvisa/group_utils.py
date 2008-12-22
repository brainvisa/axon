

class Subject(object):
    
    def __init__(self, ReadDiskItem=None, protocol=None, subject=None, database=None, acquisition=None, session=None, model=None):
        self.protocol = protocol
        self.subject = subject
        self.database = database
        self.acquisition = acquisition
        self.model = model
        self.session = session
        if ReadDiskItem:
            self.protocol = ReadDiskItem.get('protocol',None)
            self.subject = ReadDiskItem.get('subject',None)
            self.database = ReadDiskItem.get('database',None)
            self.acquisition = ReadDiskItem.get('acquisition',None)
            self.model = ReadDiskItem.get('model',None)
            self.session = ReadDiskItem.get('session',None)

    def __getinitkwargs__( self ):
        kwargs = {}
        if self.protocol is not None:
            kwargs[ 'protocol' ] = self.protocol
        if self.subject is not None:
            kwargs[ 'subject' ] = self.subject
        if self.database is not None:
            kwargs[ 'database' ] = self.database
        if self.acquisition is not None:
            kwargs[ 'acquisition' ] = self.acquisition
        if self.session is not None:
            kwargs[ 'session' ] = self.session
        if self.model is not None:
            kwargs[ 'model' ] = self.model
        return ( (), kwargs )
    
    def __repr__( self ):
        args, kwargs = self.__getinitkwargs__()
        result = 'Subject('
        if args or kwargs:
            result += ' ' + \
                ', '.join( ( ', '.join( (repr(i) for i in args) ),
                            ', '.join( (n+'='+repr(v) for n,v in kwargs.iteritems()) ) ) ) + \
                ' '
            result += ')'
        return result

    def attributes(self, database=False):
        kwargs = self.__getinitkwargs__()[1]
        if not database and self.database is not None:
            del kwargs['database']
        return kwargs
    
