

#  This software and supporting documentation are distributed by
#      Institut Federatif de Recherche 49
#      CEA/NeuroSpin, Batiment 145,
#      91191 Gif-sur-Yvette cedex
#      France
#
# This software is governed by the CeCILL license version 2 under
# French law and abiding by the rules of distribution of free software.
# You can  use, modify and/or redistribute the software under the
# terms of the CeCILL license version 2 as circulated by CEA, CNRS
# and INRIA at the following URL "http://www.cecill.info".
#
# As a counterpart to the access to the source code and  rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty  and the software's author,  the holder of the
# economic rights,  and the successive licensors  have only  limited
# liability.
#
# In this respect, the user's attention is drawn to the risks associated
# with loading,  using,  modifying and/or developing or reproducing the
# software by the user in light of its specific status of free software,
# that may mean  that it is complicated to manipulate,  and  that  also
# therefore means  that it is reserved for developers  and  experienced
# professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their
# requirements in conditions enabling the security of their systems and/or
# data to be ensured and,  more generally, to use and operate it in the
# same conditions as regards security.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL license version 2 and that you accept its terms.

import six


class Subject(object):

    def __init__(self, ReadDiskItem=None, center=None, protocol=None, subject=None, database=None, acquisition=None, session=None, model=None):
        '''center replaces protocol since brainvisa hierarchies 3.2.0 (BV 4.4)
        but for older FSO, protocol should still be supported. So we store both
        attributes in Subject (normally only one of them is used).
        '''
        self.center = center
        self.protocol = protocol
        self.subject = subject
        self.database = database
        self.acquisition = acquisition
        self.model = model
        self.session = session
        if ReadDiskItem:
            self.center = ReadDiskItem.get('center', None)
            self.protocol = ReadDiskItem.get('protocol', None)
            self.subject = ReadDiskItem.get('subject', None)
            self.database = ReadDiskItem.get('database', None)
            self.acquisition = ReadDiskItem.get('acquisition', None)
            self.model = ReadDiskItem.get('model', None)
            self.session = ReadDiskItem.get('session', None)

    def __getinitkwargs__(self):
        kwargs = {}
        if self.center is not None:
            kwargs['center'] = self.center
        if self.protocol is not None:
            kwargs['protocol'] = self.protocol
        if self.subject is not None:
            kwargs['subject'] = self.subject
        if self.database is not None:
            kwargs['database'] = self.database
        if self.acquisition is not None:
            kwargs['acquisition'] = self.acquisition
        if self.session is not None:
            kwargs['session'] = self.session
        if self.model is not None:
            kwargs['model'] = self.model
        return ((), kwargs)

    def __repr__(self):
        args, kwargs = self.__getinitkwargs__()
        result = 'Subject('
        if args or kwargs:
            result += ' ' + \
                ', '.join((', '.join((repr(i) for i in args)),
                           ', '.join((n + '=' + repr(v)
                                      for n, v in six.iteritems(kwargs)) ) ) ) + \
                ' '
            result += ')'
        return result

    def attributes(self, database=False):
        kwargs = self.__getinitkwargs__()[1]
        if not database and self.database is not None:
            del kwargs['database']
        return kwargs
