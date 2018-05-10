# -*- coding: utf-8 -*-
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

from brainvisa.processes import *
name = 'Mesh smoothing'
userLevel = 3

signature = Signature(
    'mesh', ReadDiskItem('Mesh', ['Mesh Mesh', 'Tri Mesh']),
    'ouput_mesh', WriteDiskItem('Mesh', ['Mesh Mesh', 'Tri Mesh']),
    #'directory', ReadDiskItem( 'Directory', 'Directory' ),
    'algorithm', Choice(
        'Lowpass', 'SimpleSpring', 'PolygonSpring', 'Laplacian'),
    'iterations', Integer(),
    'rate', Float(),
)


def buildNewSignature(self, algo):
    paramSignature = ['mesh', ReadDiskItem('Mesh', ['Mesh Mesh', 'Tri Mesh']),
                      'ouput_mesh', WriteDiskItem('Mesh', ['Mesh Mesh', 'Tri Mesh'])]
    # paramSignature += ['directory', ReadDiskItem( 'Directory', 'Directory' )]
    paramSignature += [
        'algorithm', Choice(
            'Lowpass', 'SimpleSpring', 'PolygonSpring', 'Laplacian'),
                       'iterations', Integer(),
                       'rate', Float()]
    if algo == 'Laplacian':
        paramSignature += ['angle', Integer()]
    elif algo == 'SimpleSpring' or algo == 'PolygonSpring':
        paramSignature += ['restoringForce', Float()]

    signature = Signature(*paramSignature)
    self.changeSignature(signature)


def initialization(self):
    self.addLink(None, 'algorithm', self.buildNewSignature)
    # self.setOptional( 'directory' )
    self.algorithm = 'Lowpass'
    self.iterations = 30
    self.rate = 0.2
    self.angle = 180
    self.restoringForce = 0.2


def execution(self, context):
    # files = []
    # if self.mesh is None:
        # if not ( self.directory is None ):
            # d = os.listdir( self.directory.fullPath() )
            # p = self.directory.fullPath()
            # for i in d:
                # try:
                    # msh = ReadDiskItem( 'Mesh', [ 'Mesh mesh', 'tri mesh' ] \
                                        #).findValue( os.path.join( p, i ) )
                    # files.append( msh )
                # except:
                    # pass
        # else:
            # context.write( 'error: must specify one of "mesh" or "directory"' )
            # return
    # else:
        # if not ( self.directory is None ):
            # context.write( 'error: must specify only one of "mesh" or \
            #"directory"' )
            # return
        # else:
            # files = [ self.mesh ]
    tri = getFormat('tri mesh')
    # for i in files:
    cmd = ['AimsMeshSmoothing',  '-i',
           self.mesh, '--algoType', self.algorithm]
    if self.mesh.format is tri:
        cmd += ['--tri']
    if self.iterations is not None:
        cmd += ['--nIteration', self.iterations]
    if self.rate is not None:
        cmd += ['--rate', self.rate]
    if self.algorithm == 'Laplacian':
        cmd += ['--featureAngle', self.angle]
    elif self.algorithm == 'SimpleSpring' or self.algorithm == 'PolygonSpring':
        cmd += ['--springForce', self.restoringForce]
    context.system(*cmd)
