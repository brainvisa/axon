function [a, innov] = predic(x, p, typ, mu)
%
% Cette fonction permet de faire la prediction
% d'ordre p d'un signal contenu dans le vecteur colonne x.
%
% La forme d'appel est la suivante:
% [a,innov] = predic(x, p, typ, param) 
% x :	Nom de la variable MATLAB (vecteur colonne)
%	contenant le signal a deconvoluer
% p :	Ordre du predicteur
% typ :	Type de methode (0=cov, 1=pre, 2=post, 3=fen,
%	4=pre+FB, 5=cov+N&S, 6=pre+K&G)
% mu :	Parametre supplementaire si necessaire
%
% Auteur : J. Idier		Version 1.0	Date : 02/96

x = x(:);
n = length(x);
if exist('typ') ~= 1    		% If no type parameter has been set
  typ = 3;				% Set it to default value
end

  if typ == 0  				% pas de fenetrage
X = Toeplitz(x(p+1:n),flip(x(1:p+1)));
R = X'*X;
       
  elseif typ == 1		 	% pre-fenetrage
X = Toeplitz(x(1:n),zeros(1,p+1));
R = X'*X;
       
  elseif typ == 2			% post-fenetrage
X = Toeplitz([x(p+1:n); zeros(p,1)],flip(x(1:p+1)));
R = X'*X;
         
  elseif typ == 3		 	% pre et post-fenetrage 
X = Toeplitz([x(1:n); zeros(p,1)],zeros(1,p+1));
R = X'*X;

  elseif typ == 4		 	% pre-fenetrage et aller-retour 
X = Toeplitz(x(1:n),zeros(1,p+1));
R = X'*X;
x = flip(conj(x));
X = Toeplitz(x(1:n),zeros(1,p+1));
R = R + X'*X;

  elseif typ == 5		 	% Nikias et Scott (covariance)
X = Toeplitz(x(p+1:n),flip(x(1:p+1)));
puiss = filter(ones(p,1),1,x.^2);
puiss = puiss(p+1:n);    
R = X'*diag(puiss)*X;

  elseif typ == 6		 	% pre-fenetrage regularise
X = Toeplitz(x(1:n),zeros(1,p+1));	% (K&G douceur 0,5)
R = X'*X + mu*diag(0:p);
% R = X'*X + norm(x(n-p+1:n))^2*diag(0:p);

  end

% Calcul des coefficients du predicteur

Rlr = R(2:p+1,2:p+1);
r = R(2:p+1,1);
a = Rlr\r;

% Calcul de l'erreur de prediction (signal deconvolue).

innov = X*[1;-a];			% Attention : bug probable dans typ = 4 :
					% calcul l'innovation backward !
