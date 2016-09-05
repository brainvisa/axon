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

import re, types

#------------------------------------------------------------------------------
class DictPattern:
  '''A DictPattern contains a pattern that is matched against a string and a
  set of attributes contained in a dictionary. When the match succeed, it
  returns a dictionary containing attributes values extracted from the input
  string.

  Such patterns are used to define Brainvisa ontology rules which associate filenames and data types. 
  
  The input pattern is a string that is splitted in three kinds of tokens:
    
    * An attribute name enclosed in ``<`` and ``>``
    * A named regular expression enclosed in ``{`` and ``}``
    * A string literal which is everything not enclosed neither in braces nor with ``<`` and ``>``.

  When ``DictPattern.match( s, dict )`` is called, all attribute names from the
  pattern are replaced by the corresponding value in dict. If the dict does not
  contain the attribute, the match fails. Then, the string is matched against the
  pattern. If the pattern contains named regular expressions, the values
  corresponding to each expression is put in the resulting dictionary. If the
  match succeed, a dictionary (possibly empty) is returned. Otherwise, ``None`` is
  returned.
  
  In the string literal of the pattern, special characters can be found:
    
    * ``*`` matches any string and the matched value is associated to a ``filename_variable`` key in the results dictionary.
    * ``#`` matches any number and the matches value is associated to a ``name_serie`` key in the results dictionary.
  
  :Match examples:
  
  ::
  
    p = DictPattern( '<subject>_t1' )
    p.match( 's_t1', { 'subject': 's' } ) == {}
    p.match( 's_t1', { 'subject': 'x' } ) == None
    p.match( 's_t2', { 'subject': 's' } ) == None
    
    p = DictPattern( '{subject}_t1' )
    p.match( 's_t1', { 'subject': 's' } ) == {'subject': 's'}
    p.match( 'tutu_t1', { 'subject': 's' } ) == {'subject': 'tutu'}
    p.match( 's_t2', { 'subject': 's' } ) == None
      
    p = DictPattern( '*_#' )
    p.match( 'toto_titi', {} ) == None
    p.match( 'toto_42', {} ) == {'name_serie':'42', 'filename_variable':'toto'}
    
    p = DictPattern( 'begin*_<subject>_*end' )
    p.match( 'beginxxx_anatole_yyyend', { 'subject': 'anatole' } ) == None
    p.match( 'beginxxx_anatole_xxxend', { 'subject': 'anatole' } ) ==
      { 'filename_variable': 'xxx' }
    p.match( 'beginxxx_anatole_xxxend', { 'subject': 'raymond' } ) == None
    
    p = DictPattern( 'begin#_<subject>_#end': (
    p.match( 'beginxxx_anatole_xxxend', { 'subject': 'anatole' } ) == None
    p.match( 'begin123_anatole_456end', { 'subject': 'anatole' } ) == None
    p.match( 'begin123_anatole_123end', { 'subject': 'anatole' } ) ==
        { 'name_serie': '123' }
    p.match( 'begin123_anatole_123end', { 'subject': 'raymond' } ) == None
  
  
  :Unmatch example:
  
  >>> DictPattern.unmatch( matchResult, dict ) 
  
  This allows to build the string that would produce matchResult if ``DictPattern.match( s, dict )`` is succesfully used. 
  The unmatch always succeed if matchResult is not None, in this case, we have :
    
  >>> DictPattern.match( DictPattern.match( s, dict ), dict ) == s
  
  '''
  class Constant:
    pass

    def __repr__( self ):
      return str( self )

    
  class Litteral( Constant ):
    def __init__( self, s ):
      self.__litteral = s
    
    def __call__( self, dict={}, matchResult=None ):
      return self.__litteral

    def escaped( self ):
      return DictPattern.EscapedLitteral( self.__litteral )

    def __str__( self ):
      return repr(self.__litteral)
      

  class Attribute( Constant ):
    def __init__( self, s ):
      self.__key = s
    
    def __call__( self, dict, matchResult=None ):
      try:
        return dict[ self.__key ]
      except KeyError as ke:
        splitted = self.__key.split( '.' )
        if len( splitted ) > 1:
          stack = splitted[:]
          try:
            result = dict
            while stack:
              result = result[ stack.pop( 0 ) ]
            return result
          except KeyError:
            if not matchResult: raise ke
            try:
              result = matchResult
              while splitted:
                result = result[ splitted.pop( 0 ) ]
              if not result: raise ke
              return result
            except:
              raise ke
        else:
          if not matchResult: raise ke
          try:
            result = matchResult[ self.__key ]
            if not result: raise ke
            return result
          except KeyError:
            raise ke

    def escaped( self ):
      return DictPattern.EscapedAttribute( self.__key )
    
    def __str__( self ):
      return '<Attribute ' + repr(self.__key) + '>'
      

  class EscapedLitteral( Litteral ):
    def __init__( self, s ):
      DictPattern.Litteral.__init__( self, re.escape( s ) )


  class EscapedAttribute( Attribute ):
    def __call__( self, dict ):
      return re.escape( DictPattern.Attribute.__call__( self, dict ) )

    def __str__( self ):
      return '<EscapedAttribute ' + repr(self._Attribute__key) + '>'
    
  class MatchResult( Constant ):
    def __init__( self, s ):
      self.__key = s
      self.__splittedKey = s.split( '.' )
    
    def __call__( self, dict, matchResult ):
      if matchResult is None:
        raise KeyError( self.__key )
  
      # search for matchResult["att1.att2..."]
      result=matchResult.get(self.__key, None)
      if type(result) is list and result: # case of name_serie
        result=result[0]
      if result: return result
      # if not found, search for matchResult["att1"][att2]...
      try:
        stack = self.__splittedKey[:]
        result = matchResult
        while stack:
          result = result[ stack.pop( 0 ) ]
        if result: return result
      except KeyError:
        pass
      # if not found, search in dict
      result=dict.get(self.__key, None)
      if result: return result
      try:
        stack = self.__splittedKey[:]
        result = dict
        while stack:
          result = result[ stack.pop( 0 ) ]
          if not result:
            raise KeyError( self.__key )
        if result: return result
        raise KeyError( self.__key )
      except KeyError:
        raise KeyError( self.__key )

    def __str__( self ):
      return '<MatchResult ' + repr(self.__key) + '>'

  class RegexpMatch:
    def __init__( self, matchList ):
      precompile = True
      for i in matchList:
        if isinstance( i, DictPattern.Attribute ):
          precompile = False
          break
      if precompile:
        # Regex is constant and can be precompiled
        attributeToGroupname = {}
        self.groupnameToAttributes = {}
        matchRegexp = ''
        for i in matchList:
          if type( i ) is tuple:
            attribute, regexp = i
            groupname = attributeToGroupname.get( attribute )
            if groupname:
              matchRegexp += '(?P=' + groupname + ')'
            else:
              if attribute.find( '.' ) == -1:
                groupname = attribute
                attributeToGroupname[ attribute ] = groupname
                self.groupnameToAttributes[ groupname ] = ( attribute, )
              else:
                s = attribute.split( '.' )
                groupname = '__dict_' + '_'.join( s ) + '__'
                attributeToGroupname[ attribute ] = groupname
                self.groupnameToAttributes[ groupname ] = s
              matchRegexp += '(?P<' + groupname + '>' + regexp + ')'
          else:
            matchRegexp += re.escape( i() )
        self.__regexp = matchRegexp
        self.__match = re.compile( matchRegexp )
      else:
        self.__regexp = None
        attributeToGroupname = {}
        self.groupnameToAttributes = {}
        self.__match = []
        for i in matchList:
          if type( i ) is tuple:
            attribute, regexp = i
            groupname = attributeToGroupname.get( attribute )
            if groupname:
              self.__match.append(
                DictPattern.Litteral( '(?P=' + groupname + ')' ) )
            else:
              if attribute.find( '.' ) == -1:
                groupname = attribute
                attributeToGroupname[ attribute ] = groupname
                self.groupnameToAttributes[ groupname ] = ( attribute, )
              else:
                s = attribute.split( '.' )
                groupname = '__dict_' + '_'.join( s ) + '__'
                attributeToGroupname[ attribute ] = groupname
                self.groupnameToAttributes[ groupname ] = s
              self.__match.append( 
                DictPattern.Litteral( '(?P<' + groupname + '>' + regexp + ')' ) )
          else:
            self.__match.append( i.escaped() )

    def match( self, s, dict ):
      if self.__regexp is None:
        m = re.compile( ''.join( [i( dict) for i in self.__match] ) ).match( s )
      else:
        m = self.__match.match( s )
      if m:
        result = {}
        for groupname, value in m.groupdict().iteritems():
          attributes = self.groupnameToAttributes[ groupname ]
          d = result
          for k in attributes[ :-1 ]:
            d = d.setdefault( k, {} )
          d[ attributes[ -1 ] ] = value
        return result
      return None

    def __str__( self ):
      if self.__regexp is None:
        return '<RegexpMatch ' + repr( self.__match ) + '>'
      else:
        return '<RegexpMatch ' + repr( self.__regexp ) + '>'

    def __repr__( self ):
      return str( self )
  

  def __init__( self, pattern ):
    self.pattern = pattern
    splitNamedPattern = re.compile( r'([^<>{]*){([^{}<>]*)}(.*)' )
    splitAttribute = re.compile( r'([^{}<]*)<([^{}<>]*)>(.*)' )
    check = re.compile( r'.*[{}<>].*' )
    matchList = []
    unmatchList = []
    while pattern:
      m = splitAttribute.match( pattern )
      if m:
        litteral = m.group( 1 )
        if litteral:
          if check.match( litteral ):
            raise ValueError( 'Invalid pattern' )
          ma, un = DictPattern._replaceStarAndSharp( litteral )
          matchList += ma
          unmatchList += un
        attribute = m.group(2)
        r = DictPattern.Attribute( attribute )
        matchList.append( r )
        unmatchList.append( r )
        pattern = m.group( 3 )
        continue
      m = splitNamedPattern.match( pattern )
      if m:
        litteral = m.group( 1 )
        if litteral:
          if check.match( litteral ):
            raise ValueError( 'Invalid pattern' )
          ma, un = DictPattern._replaceStarAndSharp( litteral )
          matchList += ma
          unmatchList += un
        patternName = m.group(2)
        i = patternName.find( '|' )
        if i >= 0:
          pattern = n[ i+1: ]
          patternName = patternName[ :i ]
        else:
          pattern = '.+'
        matchList.append( ( patternName, pattern ) )
        unmatchList.append( DictPattern.MatchResult( patternName ) )
        pattern = m.group( 3 )
        continue
      if check.match( pattern ):
        raise ValueError( 'Invalid pattern' )
      ma, un = DictPattern._replaceStarAndSharp( pattern )
      matchList += ma
      unmatchList += un
      break

    self.unmatchList = unmatchList
        
    onlyLitteral = True
    self.matchPrefix = []
    while matchList and isinstance( matchList[0], DictPattern.Constant ):
      i = matchList.pop(0)
      self.matchPrefix.append( i )
      if not isinstance( i, DictPattern.Litteral ):
        onlyLitteral = False
    if onlyLitteral:
      self.matchPrefix = ''.join( [i({}) for i in self.matchPrefix] )

    onlyLitteral = True
    self.matchSufix = []
    while matchList and isinstance( matchList[-1], DictPattern.Constant ):
      i = matchList.pop()
      self.matchSufix.insert( 0, i )
      if not isinstance( i, DictPattern.Litteral ):
        onlyLitteral = False
    if onlyLitteral:
      self.matchSufix = ''.join( [i({}) for i in self.matchSufix] )
    
    if matchList:
      self.matchInfix = DictPattern.RegexpMatch( matchList )
    else:
      self.matchInfix = None

  def _replaceSharp( s ):
    l = s.split( '#' )
    match = [ DictPattern.Litteral( l[0] ) ]
    unmatch = [ DictPattern.Litteral( l[0] ) ]
    l.pop( 0 )
    while l:
      i = l.pop( 0 )
      litteral = DictPattern.Litteral( i )
      match += [ ( 'name_serie', '[0-9]+' ), litteral ]
      unmatch += [ DictPattern.MatchResult( 'name_serie' ), litteral ]
    return match, unmatch
  _replaceSharp = staticmethod( _replaceSharp )
  
  def _replaceStarAndSharp( s ):
    l = s.split( '*' )
    match, unmatch = DictPattern._replaceSharp( l[0] )
    l.pop( 0 )
    while l:
      i = l.pop( 0 )
      match.append( ( 'filename_variable', '.+' ) )
      unmatch.append( DictPattern.MatchResult( 'filename_variable' ) )
      m, u =  DictPattern._replaceSharp( i )
      match += m
      unmatch += u
    return match, unmatch
  _replaceStarAndSharp = staticmethod( _replaceStarAndSharp )
  
  def __getstate__( self ):
    return self.pattern
  
  def __setstate__( self, state ):
    self.__init__( state )

  def match( self, s, dict ):
    """
    Checks if the given string matches the pattern. 
    
    :param string s: the string which should match the pattern
    :param dict: a dictionary containing the values to set to the attributes named in the pattern.
    :returns: a dictionary containing the value of each named expression of the pattern found in the string, None if the string doesn't match the pattern.
    """
    try:
      if self.matchPrefix:
        if isinstance( self.matchPrefix, list ):
          prefix = ''.join( [i( dict ) for i in self.matchPrefix] )
        else:
          prefix = self.matchPrefix
        if not s.startswith( prefix ):
          return None
        s = s[ len( prefix ): ]
      if self.matchSufix:
        if isinstance( self.matchSufix, list ):
          sufix = ''.join( [i( dict ) for i in self.matchSufix] )
        else:
          sufix = self.matchSufix
        if not s.endswith( sufix ):
          return None
        s = s[ :-len( sufix ) ]
      if self.matchInfix is not None:
        return self.matchInfix.match( s, dict )
      if s:
        return None
      return {}
    except KeyError:
      return None
  
  def unmatch( self, matchResult, dict ):
    """
    The opposite of :py:meth:`match` method:  the matching string is found from a match result and a dictionary of attributes values. 
    
    :param matchResult: dictionary which associates a value to each named expression of the pattern.
    :param dict: dictionary which associates a value to each attribute name of the pattern.
    :rtype: string
    :returns: the rebuilt matching string.
    """
    try:
      return ''.join( [i( dict, matchResult ) for i in self.unmatchList] )
    except KeyError as e:
      #print '!unmatch!', e
      return None
  
  def multipleUnmatch( self, dict ):
    #print '!multipleUnmatch!', self, dict
    # Retrieve attributes() and namedRegex()
    attributes = []
    for i in self.unmatchList:
      if isinstance( i, DictPattern.Attribute ):
        if i._Attribute__key not in attributes:
          attributes.append( i._Attribute__key )
      elif isinstance( i, DictPattern.MatchResult ):
        if i._MatchResult__key not in attributes:
          attributes.append( i._MatchResult__key )
    #print '!multipleUnmatch! attributes =', attributes
    # Check attributes values that are list
    multipleValues = []
    for a in attributes:
      if a == 'name_serie':
        continue
      v = dict.get( a )
      if isinstance( v, list ):
        if multipleValues:
          newMultipleValues = []
          for d in multipleValues:
            l = [ {a: i} for i in v ]
            for d2 in l:
              d2.update( d )
            newMultipleValues.extend( l )
          multipleValues = newMultipleValues
        else:
          multipleValues = [ {a: i} for i in v ]
    #print '!multipleUnmatch! multipleValues =', multipleValues
    if multipleValues:
      result = []
      d = dict.copy()
      for d2 in multipleValues:
        d.update( d2 )
        r = self.unmatch( d, d )
        #print '!multipleUnmatch! call unmatch', d, '-->', r
        if r:
          result.append( ( r, d2 ) )
      #print '!multipleUnmatch! -->', result
      return result
    else:
      r = self.unmatch( dict, dict )
      if r:
        #print '!multipleUnmatch! -->', [ ( r, {} ) ]
        return [ ( r, {} ) ]
    #print '!multipleUnmatch! -->', []
    return []
        
      
  def attributes( self ):
    sent = []
    for i in self.unmatchList:
      if isinstance( i, DictPattern.Attribute ):
        if i._Attribute__key not in sent:
          sent.append( i._Attribute__key )
          yield i._Attribute__key
    
  def namedRegex( self ):
    sent = []
    for i in self.unmatchList:
      if isinstance( i, DictPattern.MatchResult ):
        if i._MatchResult__key not in sent:
          sent.append( i._MatchResult__key )
          yield i._MatchResult__key
    

  def __str__( self ):
    # return '<DictPattern ' + repr(self.matchPrefix) + ', ' + repr(self.matchInfix) + ', ' + repr(self.matchSufix) + '>'
    return '<DictPattern ' + repr(self.pattern) + '>'


  def __repr__( self ):
    return self.__str__()


  def __eq__( self, other ):
    return self.pattern == getattr( other, 'pattern', other )


  def __ne__( self, other ):
    return self.pattern != getattr( other, 'pattern', other )


  def __hash__( self ):
    return hash( self.pattern )
  
