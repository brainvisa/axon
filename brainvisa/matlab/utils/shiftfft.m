% shiftfft.m     fftshift colonne par colonne
% Programme fftshift_mat.m				Version 1.0
%      Auteurs : J.F. Giovannelli 			Date: 07/94
%    		 F. Champagnat				Ruse: 10/94
%	Objet:
%	-----
%	'fftshift' des colonnes d'une matrice 
%	colonne par colonne. Utile typiquement si on travaille 
%	avec une matrice contenant plusieurs spectres en colonne
% 
%	le fftshift de matlab sur des matrices ne traite pas colonne 
%	par colonne mais traite globalement la matrice ce qui est 
%	utile typiquement si on travaille une fft 2D. ( Ca inverse 
%	les cadrans etc...)
%
%%	Ceci est une version pompee modifiee de 
%%	/usr/local/matlab/toolbox/matlab/datafun/fftshift.m
%
%       Forme d'appel:
%       -------------
%	y=shiftfft(x)
%               
%   E	x :	Matrice.
%
%	
%   S	y : 	Resultat sous la forme d'une matrice de meme taille.
%
%

function y=shiftfft(x)

y = x(fftshift(1:size(x,1))',:);

%[m,n] = size(x);
%m1 = 1:ceil(m/2);
%m2 = ceil(m/2)+1:m;
%n = 1:n;
% Note: can remove the first two cases when null handling is fixed.
%if m == 1
%    y = x;			% Modif ici un peu
%elseif n == 1		
%    y = [x(m2); x(m1)];
%else
%    y = [x(m2,n); x(m1,n)];	% La modif est ici surtout
%end
