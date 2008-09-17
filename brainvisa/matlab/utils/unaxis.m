% unaxis.m supprime les axes sur une figure

% EQUIVAUT A 'AXIS OFF' ??? (JI)

function  enf = unaxis(indt)

if (nargin >1) error('too much parameter');end;
if (nargin ==0) indt = gcf;end
enf = get(indt,'Children');
set(enf,'Ytick',[]);
set(enf,'Xtick',[]);
set(enf,'Ycolor',[0 0 0 ]);
set(enf,'Xcolor',[0 0 0 ]);
