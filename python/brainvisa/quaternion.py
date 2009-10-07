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

import types, math

# Quaternion class
# API (and internals) is a copy of the C++ class of Anatomist
# (just translated to python)
class Quaternion:

    def __init__( self, quat = None ):
        if type( quat ) in ( types.TupleType, types.ListType ) \
           and len( quat ) == 4:
            # vector of 4 figures (axis + angle)
            self._vector = [ quat[0], quat[1], quat[2], quat[3] ]
            pass
        elif type( quat ) is type( self ):
            # copy constructor (from quaternion)
            self_.vector = [ quat._vector[0], quat._vector[1],
                             quat._vector[2], quat._vector[3] ]
        else:
            self._vector = [ 1, 0, 0, 0 ]

    def vector( self ):
        return self._vector	# should maybe be a deep copy

    def setVector( self, vec ):
        self._vector = [ vec[0], vec[1], vec[2], vec[3] ]

    def rotationMatrix( self ):
        r = []
        s = 2 / ( self._vector[0] * self._vector[0] \
                  + self._vector[1] * self._vector[1] \
                  + self._vector[2] * self._vector[2] \
                  + self._vector[3] * self._vector[3] )
        xs = self._vector[0] * s;
        ys = self._vector[1] * s;
        zs = self._vector[2] * s;
        wx = self._vector[3] * xs;
        wy = self._vector[3] * ys;
        wz = self._vector[3] * zs;
        xx = self._vector[0] * xs;
        xy = self._vector[0] * ys;
        xz = self._vector[0] * zs;
        yy = self._vector[1] * ys;
        yz = self._vector[1] * zs;
        zz = self._vector[2] * zs;
       
        r.append( 1 - ( yy + zz ) )
        r.append( xy - wz )
        r.append( xz + wy )
        r.append( 0 )

        r.append( xy + wz )
        r.append( 1 - ( xx + zz ) )
        r.append( yz - wx )
        r.append( 0 )

        r.append( xz - wy )
        r.append( yz + wx )
        r.append( 1 - ( xx + yy ) )
        r.append( 0 )

        r.append( 0 )
        r.append( 0 )
        r.append( 0 )
        r.append( 1 )

        return r

    #def inverseRotationMatrix( self ):
    #    pass

    def buildFromMatrix( self, matrix ):
        tr = matrix[0] + matrix[5] + matrix[10];
        if tr > 0:
            s = math.sqrt( tr + 1 )
            self._vector[3] = s * 0.5
            s = 0.5 / s
            self._vector[0] = ( matrix[6] - matrix[9] ) * s
            self._vector[1] = ( matrix[8] - matrix[2] ) * s
            self._vector[2] = ( matrix[1] - matrix[4] ) * s
        else:
            i = 0
            if m[5] > m[0]:
                i = 1
            if m[10] > m[i+i*4]:
                i = 2
            j = (i+1) % 3
            k = (j+1) % 3
            s = math.sqrt( m[i+i*4] - ( m[j+j*4] + m[k+k*4] ) + 1 )
            self._vector[i] = s * 0.5
            s = 0.5 / s
            self._vector[3] = ( m[j*4+k] - m[k*4+j] ) * s
            self._vector[j] = ( m[i*4+j] - m[j*4+i] ) * s
            self._vector[k] = ( m[i*4+k] - m[k*4+i] ) * s

    def transform( self, p ):
        r = self.rotationMatrix()
        return [ r[0] * p[0] + r[1] * p[1] + r[2] * p[2], 
                 r[4] * p[0] + r[5] * p[1] + r[6] * p[2], 
                 r[8] * p[0] + r[9] * p[1] + r[10] * p[2] ]

    def transformInverse( self, p ):
        r = self.rotationMatrix()
        return [ r[0] * p[0] + r[4] * p[1] + r[8] * p[2], 
                 r[1] * p[0] + r[5] * p[1] + r[9] * p[2], 
                 r[2] * p[0] + r[6] * p[1] + r[10] * p[2] ]

    def norm( self, x ):
        if x is None:	# quaternion norm
            n = 1 / math.sqrt( self._vector[0] * self._vector[0] \
                               + self._vector[1] * self._vector[1] \
                               + self._vector[1] * self._vector[2] \
                               + self._vector[1] * self._vector[3] )
            self._vector[0] *= n
            self._vector[1] *= n
            self._vector[2] *= n
            self._vector[3] *= n
        else:	# vector norm
            n = 1 / math.sqrt( x[0] * x[0] + x[1] * x[1] + x[2] * x[2] )
            return ( x[0] * n, x[1] * n, x[2] * n )

    def normalized( self ):
        n = 1 / math.sqrt( self._vector[0] * self._vector[0] \
                           + self._vector[1] * self._vector[1] \
                           + self._vector[2] * self._vector[2] \
                           + self._vector[3] * self._vector[3] )
        return Quaternion( ( self._vector[0] * n, self._vector[1] * n,
                             self._vector[2] * n, self._vector[3] * n ) )

    def fromAxis( self, direction, angle ):
        ndir = self.norm( direction )
        a = math.sin( angle * 0.5 )
        self._vector[0] = ndir[0] * a
        self._vector[1] = ndir[1] * a
        self._vector[2] = ndir[2] * a
        self._vector[3] = math.cos( angle * 0.5 )

    def inverse( self ):
        return Quaternion( ( -self._vector[0], -self._vector[1],
                             -self._vector[2], self._vector[3] ) )

    def axis( self ):
        n = math.sqrt( self._vector[0] * self._vector[0] \
                       + self._vector[1] * self._vector[1] \
                       + self._vector[2] * self._vector[2] )
        if n == 0:
            return ( 0, 0, 1 )
        n = 1. / n
        if self._vector[3] < 0:	# negative angle
            n *= -1;
        return ( self._vector[0] * n, self._vector[1] * n,
                 self._vector[2] * n )

    def angle( self ):
        return math.acos( self._vector[3] ) * 2

    def vectmultscal( self, v1, scale ):
        return map( lambda x: x * scale, v1 )

    def cross( self, v1, v2 ):
        return [ v1[1] * v2[2] - v1[2] * v2[1], 
                 v1[2] * v2[0] - v1[0] * v2[2], 
                 v1[0] * v2[1] - v1[1] * v2[0], 
                 0 ]

    def dot( self, a, b ):
        return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]

    # operators

    def compose( self, other ):
        c = self.vectmultscal( self._vector , other._vector[3] )
        d = self.vectmultscal( other._vector, self._vector[3] )
        e = self.cross( other._vector, self._vector )
        q = Quaternion()
        for i in xrange( 3 ):
            q._vector[i] = c[i] + d[i] + e[i]
        q._vector[3] = self._vector[3] * other._vector[3] \
                       - self.dot( self._vector, other._vector )
        q = q.normalized();
        return q

