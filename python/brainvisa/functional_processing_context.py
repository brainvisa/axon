# Copyright IFR 49 (1995-2009)
#
#  This software and supporting documentation were developed by
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
import cPickle
from Numeric import array
class Section:
    pass
# This structure is not fixed yet
# in the near future it will be fixed enough to be up-compatible
# idee: peut-etre que je vais plutot faire un truc avec pleins
# de methodes (et qui serialise un dict avant de pickliser)
# afin de permettre la manipulation interactive facilement
class FunctionalProcessingContextManager(object):
    """ This static classes manager the Functional Processing Context data
structure. Use buildContext() to create the new, default-filled context.
Use the read and write methods to dump it and load it from disk."""
    version = 1
    allContext = {1 : {
        "preProcessing" : "Section related to preProcessing (Empty now)",
        "fmriSequence" : "a 4D fMRI Volume",
        "glm" : "General Linear Model estimation related section",
        "contrasts" : "Section containing some design contrasts definition",
        "postEstimation" : "Section containing the output estimated volume",
        "clustering" : "Section related to the optional clustering processing",
    }}
    glmSection = {
            "model" : "The fff.glm model",
            "computedMatrix" : "optionaly, an already-computed design matrix",
            "factorLabels" : "optionaly, a list of column names"
            }
    clusteringSection = {
            "inputMaps" : "The image maps to apply the clustering to",
            "K" : "Number of cluster to put in the model",
            "CPW": "Centroids, Precisions, Weights Kx1-sized arrays",
            "L" : "a K-length vector labelling each cluster" }
    contrastsSection = {
            "CONTRAST_VECTORED" : 0,
            "CONTRAST_NAMED" : 1,
            "list": """
             List containing 0 or more 3-uples (name, type, value)
             name: name of the contrast
             type: definition mode, ie. numerical vector or verbose naming
             value : the contrast value, depend on the type (array or string)
            """
    }
    def newSection(dict):
        # autogenerate docstring from the class dictionary
        c = Section()
        c.__dict__.update(dict)
        c.__doc__ = "\n  Local members are : \n" + \
            "\n".join(["    %s : %s" % i for i in dict.items()])
        return c
    newSection = staticmethod(newSection)
    def buildContext():
        # return a new Functional Processing Context c, with some default values
        manager = FunctionalProcessingContextManager
        # main section
        mainSection = manager.allContext[manager.version] 
        c = manager.newSection(mainSection)
        # glm section
        c.glm = manager.newSection(manager.glmSection)
        c.glm.model = None
        c.glm.computedMatrix = None
        c.glm.factorLabels = None
        # post estimation section
        c.postEstimation = None
        # fmri sequence section
        c.fmriSequence = None
        # preprocessing section
        c.preProcessing = None
        # clustering section
        c.clustering = manager.newSection(manager.clusteringSection)
        c.clustering.CPW = (None, None, None)
        c.clustering.K = 400
        c.clustering.inputMaps = None
        c.clustering.L = None
        # constrasts section
        c.contrasts = manager.newSection(manager.contrastsSection)
        c.contrasts.list = list()
        c.contrasts.list.append((   "Example Contrast",
                                    c.contrasts.CONTRAST_VECTORED,
                                    array([1.0, -1.0]) ))
        return c
    buildContext = staticmethod(buildContext)
    def write( k, filename ):
        # TODO: transforme la classe k en dictionnaire d.
        cPickle.dump(k, open(filename, 'w'), 2)
    write = staticmethod(write)
    def read( filename ):
        return cPickle.load(open(filename))
    read = staticmethod(read)
