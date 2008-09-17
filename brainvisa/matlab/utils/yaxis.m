% yaxis([ymin ymax]);
%~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
% Cette fonction permet de
% modifier l'echelle des y
% (ordonnee) du graphique courant,
% en CONSERVANT l'echelle des x.
%~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ 

function yaxis(vecy);

	vx=get(gca,'xtick');
	vecx=[min(vx),max(vx)];
	vecy=[vecy(1),vecy(2)];
	axis([vecx vecy])
