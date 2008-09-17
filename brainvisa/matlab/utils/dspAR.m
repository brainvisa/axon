% dspAR.m   calcul la dsp AR d'ordre L d'un signal
%      Programme dspAR					Version 1.0
%      Auteur : J. Idier				Date: 07/93.
%		J.F. Giovannelli 			Date: 07/94
%    
%	Objet:
%	-----
%	Calcul de P points (equirepartis en frequence normalisee) 
%	de la dsp AR d'ordre L instantanee d'un signal etant donne
%	la suite des vecteurs de regression sous la forme d'une 
%	matrice de N lignes et de L colonnes. Le resultat est donne
%	sous la forme d'un matrice P*N.
%		                                                                                
%       Forme d'appel:
%       -------------
%	dsp = dspAR(a, s, P);
%               
%   E	a :	Jeux de coefficients AR, sous la forme d'une
%		matrice de L lignes et de N colonnes
%		(N : nombre spectres a calculer ; L : ordre des l'AR).
%   E	P :	P est le nombre de points des DSP a calculer. 
%		Valeur par defaut : P = 128. Quand P est une puissance de 2 
%		le calcul est plus rapide (voir fft). Dans le cas reel, 
%		seule la premiere moitie des points des dsp calculees est retournee.
%               Lorsque P est impair la 1ere ligne donne la frequence 0, 
%               la derniere la frequence normalisee 1/2.
%               Lorsque P est pair la 1ere ligne donne la frequence 0, 
%               la derniere la frequence normalisee [1/2-(1/2P)].
%   E	s :	vecteur ligne contenant N sigma^2
%
%	
%   S	dsp : 	Resultat sous la forme d'une matrice P*N.
%

function dsp = dspAR(a ,s , P)

[L,N] = size(a);

% Tests et verifications
	if exist('P') ~= 1	    		% Si P n'est pas specifie,
	    P = 128;        	 		% valeur par defaut.
	end


	if exist('s') ~= 1	    		% Si s n'est pas specifie,
	   s = ones(1,N);        	 	% valeur par defaut.	
	end

	if all( size(s) == [1 1] )	    	% Si s est un scalaire,
	   s = s*ones(1,N);        	 	% meme valeur partout.	
	end

% Calcul des DSP
	dsp = (abs (fft( [ones(1,N); -a], P ) ) ).^(-2);

% Mise a l echelle des sDSP par les sigma.^2
	dsp = dsp .* s( ones(P,1),: );

% Si aucun des coef AR est complexe on ne renvoit que la moitie des spectres
	if(~any(imag(a)))
	    dsp = dsp(1:P/2,:);
	end


return;

