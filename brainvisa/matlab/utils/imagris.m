function imagris(Q,n,x,y);
%~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
% imagris(Q,n,x,y)
%~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
% Affiche la matrice Q en n niveaux de gris (par defaut, 255).
% L'orientation est celle de la matrice. x et y sont les 
% vecteurs des echelles des abscisses
%~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
% T. Martin, 04/94
%~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

%
	if exist('n') ~= 1	% If no n has been set,
	    n = 255;		% Set it to default value
	end
	
	colormap(gray(n))
	m=min(min(Q));
	M=max(max(Q));	
	if exist('x') & exist('y')
		image(x,y,(Q-m)*n/(M-m))
	else
		image((Q-m)*n/(M-m))
	end
%
