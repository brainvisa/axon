function plot2d(Mat,fac,shd,ay,by);
% spec2d2.m      plot2d modifie pour une bonne cause ....
%~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
% plot2d(Mat,fac,shd,ay,by)
%~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
% Auteurs   : J. Idier	Date : 09/93. V. 1.0 plot2d
%           : T. Martin	Date : 11/93. V. 1.1 plot2d
%           : T. Martin Date : 04/94. V. 1.2 plot2d
%~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
%      Cette fonction permet d'afficher cote a cote un ensemble 
% de signaux juxtaposes en colonne dans une matrice Matlab
% Permet en plus la visualisation d'ombrages de signaux 2D.
%~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
% Mat:     Donnees a visualiser.
% (fac):   Facteur d'echelle : une valeur positive donne
%      l'empietement maximum d'un signal sur un signal
%      voisin, une valeur negative donne un decalage
%      absolu entre axes des abscisses des signaux
%      consecutifs.
%      Valeur par defaut : 1 (aucun empietement).
% (shd):   Sens de l'ombrage. Si omb=1, l'ombrage remplit les
%      asperites de droite, si omb=0, pas d'ombrage.
% (ay): Pente de l'echelle verticale par rapport a la numerotation 
%      matricielle de Mat.
% (by): ordonnee a l'origine de l'echelles v.
%~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
% voir aussi dplot2, d2plot, plotd2, geoplot
%~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

%
%	Type selection
%
	if exist('typ') ~= 1    		% If no type parameter has been set
		typ = 1;							% Set it to default value
	elseif (typ ~= 0) & (typ ~= -1) & (typ ~= 1)
		fprintf('Error. Unknown type parameter\n')
		return     						% Message and exit
	end
%
%	Parameter initialisation
%
	[N_l,N_c] = size(Mat);
	vecc = 1:N_c;
	vecl = 1:N_l;
	X = Mat;
	clear Mat
	if exist('by')~=1
		by=0;
	end
	if exist('ay')~=1
		ay=1;
	end
	Torg(1)=by;
	Te=ay;
%
	if(typ==0)	X = abs(X);
	elseif(typ==-1)	X = imag(X);
	elseif(typ==1)	X = real(X);
	end
%
	if exist('fac') ~= 1 			% If no scaling factor has been set
		fac = 1.5;        			% Set it to default value
	elseif fac == 0      			% Else, test if it is null
		fprintf('Error. The scaling factor must non null\n')
		return            			% Message and exit
	end
	if fac > 0
		M = max(max(abs(X)));		% Maximum of the absolute value of the data
		fac = fac/M;					% for relative scaling
	else
		fac = -1/fac;    				% Negative values of fac give absolute scaling
	end
%
	eps = .05/65*N_c;
	xm = min(min(X))*fac;			
	t = Torg(1) + Te(1)*(vecl-1);	% Scaling of the data points 
	X = vecc(ones(1,N_l), :) + X*fac;	
%
%	Optional shading
%
	clf
	plot(1,1,'k')
	hold on
	if exist('shd') ~= 1     		% If no type parameter has been set
		shd = 0;   		        		% Set it to default value
	elseif(shd==1)
		x0 = [xm 0 0 xm];
		y0 = [t(1) t(1) t(N_l) t(N_l)];
		for x=fliplr(vecc)
			set(patch([x-eps;X(:,x)-eps*(X(:,x)<=x);x-eps],...
			[t(1) t t(N_l)],'w'),'cdata',[1 1 1],'edgecolor','w')
			fill(x0+x-eps,y0,'k')
		end
	end
%
%	PLOT (solid lines)
%
	plot(X,t,'-w')
	xm = min(-1,min(min(X))-65/N_l);
	xM = max(N_c+2,max(max(X)));
	yM = Torg(1)+(N_l+1)*Te(1);
	ym = Torg(1)-2*Te(1);
	axis([xm xM ym yM])
	xmark = get(gca,'XTick');
	xmark(1) = 1;
	xmark = [xmark N_c];
	ymark = get(gca,'YTick');
	ymark = [t(1) ymark t(N_l)];
	plot([xmark;xmark],[ym;yM],'w:')
	plot([xm;xM],[ymark;ymark],'w:')
	set(gca,'ydir','reverse','XTick',xmark,'YTick',ymark)
	hold off
return
