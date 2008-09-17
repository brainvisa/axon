function plot2d(X,fac,shd,y0,dy,x0,dx)
% plot2D.m        affichage d'une matrice de sigaux juxtaposes
%~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
% plot2d(X,fac,shd,x0,dx,y0,dy)
%
% Auteurs : J. Idier & T. Martin	Version 1.3	Date : 07/94
%~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
%      Cette fonction permet d'afficher cote a cote un ensemble 
% de signaux juxtaposes en colonne dans une matrice Matlab
% Permet en plus la visualisation d'ombrages de signaux 2D.
%~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
% (X):	Donnees a visualiser, considere comme un ensemble de signaux
%	stocke colonne par colonne.
% (fac): Facteur d'echelle : une valeur positive donne
%	l'empietement maximum d'un signal sur un signal
%	voisin, une valeur negative donne un decalage
%	absolu entre axes des abscisses des signaux
%	consecutifs. Valeur par defaut : 1 (aucun empietement).
% (shd): Ombrage. Si shd=1, l'ombrage remplit les
%	asperites de droite. Par defaut shd=0, pas d'ombrage.
% (y0): Indice a l'origine (0 par defaut) de chaque signal.
% (dy): Pente de l'echelle par rapport a la numerotation 
%	matricielle de X (1 par defaut) pour chaque signal.
% (x0): Indice du premier signal (1 par defaut).
% (dx): Pente de l'echelle entre deux signaux (1 par defaut).
%
% Voir aussi visu2d, geoplot
%~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

%
%	Parameter initialisation
%
	if exist('typ') ~= 1    	% If no type parameter has been set
		typ = 1;		% Set it to default value
	elseif (typ ~= 0) & (typ ~= -1) & (typ ~= 1)
		fprintf('Error. Unknown type parameter\n')
		return     						% Message and exit
	end
	if exist('x0')~=1
		x0 = 1;
	end
	if exist('dx')~=1
		dx = 1;
	end
	dx = abs(dx);
	if exist('y0')~=1
		y0 = 0;
	end
	if exist('dy')~=1
		dy = 1;
	end
	dy = abs(dy);
	[Nl,Nc] = size(X);
	vecc = 1:Nc;
	vecl = 1:Nl;
%
	if typ==0	X = abs(X);
	elseif typ==-1	X = imag(X);
	elseif typ==1	X = real(X);
	end
%
	if exist('fac') ~= 1 		% If no scaling factor has been set
		fac = 1;        	% Set it to default value
	elseif fac == 0      		% Else, test if it is null
		fprintf('Error. The scaling factor must non null\n')
		return            	% Message and exit
	end
	if fac > 0
		M = max(abs(X(:)));	% Maximum of the absolute value of the data
		fac = fac/M;		% for relative scaling
	else
		fac = -1/fac;    	% Negative values of fac give absolute scaling
	end
%
	eps = .05*Nc/65*dx;
	vecc = x0 + dx*(0:Nc-1);	% Scaling of the data points 
	vecl = y0 + dy*(0:Nl-1); 	
	X = vecc(ones(1,Nl),:) + X*fac;	
	xm = min(X(:))-x0;			

	clf
	plot(1,1,'k')
	hold on
	if exist('shd') ~= 1     	% If no type parameter has been set
		shd = 0;		% Set it to default value.
%
	elseif shd==1			% Optional shading
	    for nc = Nc:-1:1,
	        x = vecc(nc);
		set(patch([x-eps;X(:,nc)-eps*(X(:,nc)<=x);x-eps],...
		[vecl(1) vecl vecl(Nl)],'w'),'cdata',[1 1 1],'edgecolor','w')
		fill([xm 0 0 xm]+x-eps, [vecl(1) vecl(1) vecl(Nl) vecl(Nl)], 'k')
	    end
	end
%
	plot(X,vecl,'-w')		% PLOT (solid lines)
	
	xm = min(x0-2*dx, min(X(:))-dx);
	xM = max(x0+(Nc+2)*dx, max(X(:))+dx);
	yM = y0 + (Nl+1)*dy;
	ym = y0 - 2*dy;
	axis([xm xM ym yM])
	
	ymark = get(gca,'YTick');
	yl = length(ymark);
	yspace = ymark(yl)-ymark(1);
	if (vecl(Nl)-ymark(yl))*yl*5<yspace
	    ymark(yl) = vecl(Nl);
	else
	    ymark = [ymark vecl(Nl)];
	end
	if (ymark(1)-vecl(1))*yl*5<yspace
	    ymark(1) = vecl(1);
	else
	    ymark = [vecl(1) ymark];
	end
		
	xmark = get(gca,'XTick');
	xmark = xmark(1:sum(xmark<vecc(Nc)));
	xl = length(xmark);
	xspace = xmark(xl)-xmark(1);
	if (vecc(Nc)-xmark(xl))*xl*3.5<xspace
	    xmark(xl) = vecc(Nc);
	else
	    xmark = [xmark vecc(Nc)];
	end
	if (xmark(1)-vecc(1))*xl*3.5<xspace
	    xmark(1) = vecc(1);
	else
	    xmark = [vecc(1) xmark];
	end

	plot([xmark;xmark],[ym;yM],'w:')
	plot([xm;xM],[ymark;ymark],'w:')
	set(gca,'ydir','reverse','XTick',xmark,'YTick',ymark)
	hold off
return
