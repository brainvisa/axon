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

from brainvisa.configuration.neuroConfig import findInPath
import os
import six

def findEncoders():
  enc = []
  if findInPath( 'ffmpeg' ):
    enc.append( 'ffmpeg' )
  if findInPath( 'avconv' ):
    enc.append( 'avconv' )
  if findInPath( 'mencoder' ):
    enc.append( 'mencoder' )
  if findInPath( 'transcode' ):
    enc.append( 'transcode' )
  if findInPath( 'recmpeg' ):
    enc.append( 'recmpeg' )
  return enc


def findMpegFormats():
  form = [ 'MPEG film' ]
  enc = findEncoders()
  if 'transcode' in enc or 'mencoder' in enc or 'ffmpeg' in enc \
      or 'avconv' in enc:
    form.append( 'AVI film' )
  if 'mencoder' in enc or 'ffmpeg' in enc:
    form.append( 'QuickTime film' )
  if 'ffmpeg' in enc or 'avconv' in enc:
      form += ['MP4 film', 'OGG film']
  return form


def findCodec( encoder ):
  if encoder == 'recmpeg':
    return [ 'mpeg1', 'mpeg4' ]
  elif encoder == 'transcode':
    return [ 'divx5', 'ffmpeg4', 'af6', 'divx4',
             'divx4raw', 'fame', 'im',
             'mjpeg', 'im', 'net', 'opendivx',
             'pcm', 'raw', 'toolame', 'xvid',
             'xvidcvs', 'xvidraw' ]
  elif encoder == 'mencoder':
    return [ 'mpeg4', 'mjpeg', 'ljpeg', 'h263', 'h263p', 'msmpeg4',
             'msmpeg4v2', 'wmv1', 'wmv2', 'rv10', 'mpeg1video',
             'mpeg2video', 'huffyuv', 'asv1', 'asv2', 'ffv1' ]
    #( h, f, g ) = os.popen3( 'mencoder -ovc help' )
    #l = f.readlines()
    #f.close()
    #r = 0
    #import re
    #reg = re.compile( '^\s+([^ ]+)\s+' )
    #cx = []
    #for x in l:
      #if x == 'Available codecs:\n':
        #r = 1
      #elif r == 1:
        #m = reg.match( x )
        #if m:
          #cx.append( m.group(1) )
    #return cx
  elif encoder in ('ffmpeg', 'avconv'):
    #return [ 'asv1', 'asv2', 'dvvideo', 'ffv1', 'h263', 'huffyuv', 'h263p',
    #         'ljpeg', 'mjpeg', 'mpeg4', 'mpeg1video', 'mpeg2video', 'msmpeg4',
    #         'msmpeg4v1', 'msmpeg4v2', 'rv10', 'rv20', 'wmv1', 'wmv2', 'wmv3' ]
    try:
      # Valid only since Python 2.4
      import subprocess
      sproc = subprocess.Popen( ( encoder, '-codecs' ),
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE )
      out, err = sproc.communicate()
      if sproc.returncode != 0:
        # maybe the older ffmpeg using -formats argument
        sproc = subprocess.Popen( ( encoder, '-formats' ),
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE )
        out, err = sproc.communicate()
    except ImportError:
      # Work with earlier Python version but generates the following error at exit:
      # Exception exceptions.TypeError: TypeError("'NoneType' object is not callable",) in <bound method Popen3.__del__ of <popen2.Popen3 instance at 0xb7303c2c>> ignored
      stdin, stdout, stderr = os.popen3( encoder + ' -codecs' )
      stdin.close()
      err = stderr.read()
      out = stdout.read()
      stdout.close()
      stderr.close()
      del stdout, stderr, stdin
    
    codecs = []
    lines = out.split(six.b('\n'))
    codecsFound = False
    while lines:
      if lines.pop( 0 ) == 'Codecs:':
        codecsFound = True
        break
    if codecsFound:
      while lines:
        l = lines.pop( 0 ).strip()
        if not l: break
        lsplit = l.split()
        for x in lsplit:
          if x != x.upper():
            codecs.append( x )
            break
    return codecs
  return []


def findCodecs():
  c = {}
  for x in findEncoders():
    c[ x ] = findCodec( x )
  return c


encoders = findEncoders()
mpegFormats = findMpegFormats()
codecs = findCodecs()
