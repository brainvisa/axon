% xaxis([xmin xmax]);
%~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
% Cette fonction permet de
% modifier l'echelle des x
% (abscisse) du graphique courant,
% en CONSERVANT l'echelle des y.
%~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ 

function xaxis(vecx);

	vy=get(gca,'ytick');
	vecy=[min(vy),max(vy)];
	vecx=[vecx(1),vecx(2)];
	axis([vecx vecy])
