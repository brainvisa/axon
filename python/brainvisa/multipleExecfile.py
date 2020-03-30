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
"""
This module defines the class :py:class:`MultipleExecfile` that is used to read Brainvisa ontology files.
"""
from __future__ import print_function
from __future__ import absolute_import
import sys
import os
from traceback import format_exc
import six

class MultipleExecfile(object):

    """
    This object enables to execute several python files that can have dependencies between us.
    One file can include another to indicate that it needs something defined in this other file.

    :Attributes:

    .. py:attribute:: fileExtensions

      list of string indicating the possible file extensions for the files that can be executed via this object.

    .. py:attribute:: includePath

      Set of paths where the files to execute are searched.

    .. py:attribute:: globalDict

      Global dictionary that will be used to execute the files.

    .. py:attribute:: localDict

      Local dictionary that will be used to execute the files.

    :Methods:

    """

    def __init__(self, localDict=None, globalDict=None):
        if localDict is None:
            localDict = {}
        if globalDict is None:
            # Get the global dictionary of the caller. Using globals() would
            # return the namespace of this module.
            globalDict = sys._getframe(1).f_globals
        self.localDict = localDict
        self.localDict['include'] = self._include
        self.globalDict = globalDict
        self.includePath = set()
        self.fileExtensions = ['']
        self._executedFiles = {}
        self._includeStack = []
        self._last_line = 0

    def findFile(self, localFileName):
        """
        Finds the file in :py:attr:`includePath` trying to append the :py:attr:`fileExtensions` to its name.

        :param string localFileName: name of the searched file, possibly wihtout extension, relative to the include path.
        :rtype: string
        :returns: absolute path to the found file, else None.
        """
        result = None
        if self._includeStack:
            path = [os.path.dirname(self._includeStack[-1][0])] + \
                list(self.includePath)
        else:
            path = list(self.includePath) + ['']
        for e in self.fileExtensions:
            for p in path:
                if p is None:
                    continue
                f = os.path.join(p, localFileName + e)
                if os.path.exists(f):
                    result = os.path.abspath(os.path.normpath(f))
                    break
            if result is not None:
                break
        return result

    def execute(self, *args, **kwargs):
        """
        Executes the files listed in *args* if they are found in the :py:attr:`includePath`
        passing :py:attr:`globalDict` and :py:attr:`localDict` as global and local namespaces.

        *kwargs* may contain a parameter *continue_on_error*. If it is True, the execution won't be stopped by the first exception,
        the exceptions will be stored in a list and returned at the end of the method.

        :returns: The list of exception that occured during files execution.
        """
        class IncludeError(RuntimeError):
            pass

        exc = []
        for f in args:
            file = None
            try:
                do_pop = False
                file = self.findFile(f)
                if file is None:
                    if self._includeStack:
                        raise RuntimeError(
                            _t_('Include file %s not found (in %s:%d)')
                            % (f, self._includeStack[-1][0],
                               self._includeStack[-1][1]))
                    else:
                        raise RuntimeError(
                            _t_('File %s does not exist') % (f, ))
    # dbg#      print('!MultipleExecfile!', f, '-->', file)
                status = self._executedFiles.get(file)
                if status is None:
    # dbg#        print('!MultipleExecfile! execute', file)
                    self._executedFiles[file] = False
                    self._includeStack.append([file, self._last_line])
                    do_pop = True
                    self.localDict['__name__'] = file
                    with open(file, 'rb') as ff:
                        code = compile(ff.read(), ff.name, 'exec')
                    six.exec_(code, self.globalDict, self.localDict)
                    self._includeStack.pop()
                    do_pop = False
                    if self._includeStack:
                        self.localDict['__name__'] = self._includeStack[-1][0]
                    else:
                        self.localDict['__name__'] = None
                    self._executedFiles[file] = True
                elif status == False:
                    self._executedFiles[file] = True
                    raise IncludeError(
                        _t_('Circular dependencies in included files. Inclusion order:')
                        + ', '.join(['%s:%d' % (x[0], x[1])
                                     for x in self._includeStack
                                        + [(file, 0)]]))
            except IncludeError as e:
                six.reraise(*sys.exc_info())
            except Exception as e:
                einfo = sys.exc_info()
                tb = einfo[2]
                lineno = tb.tb_lineno  # tb_frame.f_lineno
                while tb.tb_next \
                        and os.path.basename(tb.tb_frame.f_code.co_filename) \
                            in ('multipleExecfile.py', 'multipleExecfile.pyc',
                                'six.py', 'six.pyc'):
                    # skip frames of thie file and six.exec_()
                    tb = tb.tb_next
                    lineno = tb.tb_lineno  # tb_frame.f_lineno
                if six.PY2 and tb.tb_next:
                    # one frame up because there is one more in python2.
                    tb = tb.tb_next
                    lineno = tb.tb_lineno  # tb_frame.f_lineno
                msg = six.text_type('while executing file ' + f
                              + ':%d' % lineno + ' ')
                #import traceback
                #msg += traceback.format_exc()
                if file:
                    msg += u'(' + six.text_type(file) + u'): '
                    self._executedFiles[file] = True

                if len(self._includeStack) > 1:
                    msg += 'include stack:\n'
                    for x in self._includeStack:
                        msg += '%s:%d.\n' % (x[0], x[1])

                if do_pop:
                    self._includeStack.pop()
                    do_pop = False

                if hasattr(e, 'message'):
                    msg = msg + '%s: %s' % (e.__class__.__name__, six.text_type(e))
                    e.message = msg
                else:
                    msg = msg + format_exc()
                e.args = (msg, ) + e.args[1:]
                print(msg)
                import traceback
                traceback.print_exc()
                if not kwargs.get('continue_on_error', False):
                    six.reraise(*einfo)
                exc.append(einfo)
        if exc:
            return exc

    def _include(self, *args):
        import traceback
        self._last_line = traceback.extract_stack()[-2][1]
        if self._includeStack:
            self._includeStack[-1][1] = self._last_line
        #for f in args:
            #print('!MultipleExecfile! include', f, 'in', self._includeStack[-1], ':', traceback.extract_stack()[-2][1])
# dbg#      self.execute( f )
        self.execute(*args)

    def executedFiles(self):
        """
        Returns the list of executed files.
        """
        return six.iterkeys(self._executedFiles)
