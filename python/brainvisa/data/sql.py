_mangleSQL = (
  ( '_', '__' ),
  ( ' ', '_s' ),
  ( '.', '_d' ),
  ( '+', '_p' ),
  ( '-', '_m' ),
  ( '/', '_l' ),
)

_reservedNames = {
  'to': '__to__',
  'from': '__from__',
}

_reservedNamesReversed = dict( (j , i) for i, j in _reservedNames.iteritems() )

def mangleSQL( sql ):
  global _mangleSQL, _reservedNames
  
  checkReserved = _reservedNames.get( sql )
  if checkReserved is not None:
    return checkReserved
  mangled = sql
  for f, r in _mangleSQL:
    mangled = mangled.replace( f, r )
  return mangled


def unmangleSQL( mangled ):
  global _reservedNamesReversed
  
  checkReserved = _reservedNamesReversed.get( mangled )
  if checkReserved is not None:
    return checkReserved
  sql = mangled
  for r, f in _mangleSQL:
    sql = sql.replace( f, r )
  return sql
