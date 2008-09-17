% levinsonmatlab.m Algorithme de Levinson en MATLAB : Une aberration 
%       Programme levinson		Version 1.0
%
%       Auteur : J.F.Giovannelli	Date : 08/93.
%    		 F. Champagnat
%		 Monsieur Marple
%
%	Objet :
%	-----
%	Cette fonction met en oeuvre le fameux algorithme  
%	propose par Monsieur Levinson et qui porte son nom.
%	Tu lui donnes une correlation, elle te rend les 
%	coefficients AR successifs (a tous les ordres),
%	et les puissances des bruits generateurs.
%		                                                                                
%       Forme d'appel:
%       -------------
%       [A P]=levinson(t);
%               
%       Variables d'entree et de sortie :
%       -------------------------------
%
%	E	t	Sequence de correlation.
%			t=[t0 t1 ... tN]
%
%	S	A	Matrice des coefficients AR.
%			A= 1        0          0     0      0
%			   Am(1)    1          0     0      0
%			   Am(2)    Am-1(1)    1     0      0
%			   
%			    			     1
%			   Am(m)    Am-1(m-1)        a1(1)  1
%			   
%	S	P	Vecteur des puissances des bruits generateurs.
%			P=[ Pm Pm-1 ... P1 P0]
%
% 	Remarque
%       ----------
%	Avec ces notations, pour etre precis, on a:
%
%       	inv( toeplitz( t, t' )) = A inv( diag( P )) A'
%

% 	Remarque
%       ----------
%       Ce programme fait appel a levinsonmex.mexhp7, qui est une version 
%	compilee de levinsonmex.c. Ce levinsonmex.c fait lui meme appel 
%	a levinson.f, qui est une version modifiee de levinson.f fournie 
%	dans le pas tres remarquable bouquin de Marple.


function [A, P] = levinson(t)

	[A P]=levinsonmex(t);
