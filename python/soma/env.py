# -*- coding: iso-8859-1 -*-

#  This software and supporting documentation are distributed by
#      Institut Federatif de Recherche 49
#      CEA/NeuroSpin, Batiment 145,
#      91191 Gif-sur-Yvette cedex
#      France
#
# This software is governed by the CeCILL-B license under
# French law and abiding by the rules of distribution of free software.
# You can  use, modify and/or redistribute the software under the
# terms of the CeCILL-B license as circulated by CEA, CNRS
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
# knowledge of the CeCILL-B license and that you accept its terms.

'''

- author: Dominique Geffroy
- organization: `NeuroSpin <http://www.neurospin.org>`_ and
  `IFR 49 <http://www.ifr49.org>\\_
- license: `CeCILL version 2 <http://www.cecill.info/licences/Licence_CeCILL_V2-en.html>`_
'''
from __future__ import absolute_import
__docformat__ = 'restructuredtext en'

from soma.singleton import Singleton
import os


class BrainvisaSystemEnv(Singleton):

    """
    This class gets the value of the variables ``BRAINVISA_UNENV_``... if they are defined. These variables store the value of system environment variables that have been modified in brainvisa context.
    The method getVariables returns a map of variable -> value to restore the system value of these environment variables.
    """

    def __singleton_init__(self):
        """
        Define system environment variables that have to be passed to external command to restore environment if it have been modified at brainvisa startup
        """
        super(BrainvisaSystemEnv, self).__singleton_init__()
        # this map will contain {variable : old value} for all varialbes
        # modified at startup
        self.variables = {}
        unenvVars = [
            i for i in os.environ if i.startswith('BRAINVISA_UNENV_')]
        if unenvVars:
            # the old value of these variables was stored in variables
            # BRAINVISA_UNENV_VARIABLE
            for bvSysVar in unenvVars:
                sysVar = bvSysVar[16:]
                self.variables[sysVar] = os.getenv(bvSysVar)

    def getVariables(self):
        '''
        Returns the dictionary of BRAINVISA_UNENV_* variables
        '''
        return self.variables
