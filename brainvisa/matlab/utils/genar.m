function [x, r2] = genar(N, a, r1)
% genar.m   Generation d'un AR gausien
% Cette fonction permet de generer une realisation AR gaussienne
% de taille N suivant un vecteur de parametres AR a. L'AR est genere  
% a la puissance theorique r1 si ce parametre est specifie, sinon il 
% est genere pour un bruit gaussien normalise en entree et sa
% puissance theorique est fournie dans r2.
% La forme d'appel est la suivante:
%
% [x, r2] = genar(n, a, r1)
%
% N:	  taille de l'AR a generer.
%
% a:	  Vecteur des parametres AR.
%
% r1:	  Variance theorique de l'AR genere (optionnel).
%	 
% x:      Nom de la variable MATLAB (vecteur colonne)
%         contenant la realisation AR.
%
% r2:     Variance theorique de l'AR genere (optionnel).
disp('L''auteur a-t''il honte de ses creations');
disp('Les fichiers de Seismic doivent mentionner l''auteur et la date...')
 
a = a(:);
p=length(a);

A = levin_desc(a); 
rand('normal');
fact = flipud(cumprod(ones(p,1)-flipud(diag(A).^2)));

% bruit generateur
   u = rand(N,1);

% x : sequence initialisee correctement
   x = zeros(N,1);
   x(1) = u(1)/sqrt(fact(1));
   for n=2:p
       x(n)=u(n)/sqrt(fact(n))+A(1:n-1,n-1)'*x(n-1:-1:1);
   end
   for n = p+1:N
	x(n) = u(n)+a'*x(n-1:-1:n-p);
   end 

[r, k] = levin_descmex(a); 

if exist('r1') == 1	% Sequence normalisee
   x = x*sqrt(r1/r(1));
else
   r1 = r(1);
end

if nargout == 2
   r2 = r1;
end
return


