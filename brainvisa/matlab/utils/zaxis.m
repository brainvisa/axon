% zaxis([zmin zmax]);
%~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
% Cette fonction permet de
% modifier l'echelle des z
% du graphique courant (3D), en
% CONSERVANT l'echelle des x et des y.
%~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ 

function zaxis(vecz);

	vx=get(gca,'xtick');
	vy=get(gca,'ytick');
	vecx=[min(vx),max(vx)];
	vecy=[min(vy),max(vy)];
	vecz=[vecz(1),vecz(2)];
	axis([vecx vecy vecz])
