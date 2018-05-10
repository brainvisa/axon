from __future__ import print_function
from soma.singleton import Singleton
from brainvisa.remote.server import BrainVISAServer


class DatabaseServer(Singleton):
    from brainvisa.processes import defaultContext

    def initialize(self):
        server = BrainVISAServer()
        server.initialize()
        self.context = defaultContext()
        obj = Pyro.core.ObjBase()
        obj.delegateTo(self.context)
        uri = server.addObject(obj)
        print('Serving default execution context with URI', uri)

    def serve(self):
        BrainVISAServer().serve()
