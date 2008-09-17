include( 'base' )

insert( '{protocol}/{subject}',
  'spmt', SetContent(
    '<subject>_funcMask', SetType( 'Functional mask' ),
    'con_{contrast}', SetContent(
      '<subject>_spmt_<contrast>', SetType( 'SPMt map' ),
      '<subject>_spmt_<contrast>_sketch', SetType( 'Primalsketch graph' ),
    ),
  ),
)
