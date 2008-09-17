function B = Jury(b)
% Jury(b) = Toeplitz(b,v) + Hankel(b,v) - b*v', avec v' = [1 0...]
% Permet de faire du Levinson descendant par inversion de matrice :
%
% r = [1.5; -.05; .2; .05]; v = [1; zeros(length(r)-1,1)];	% Exemple
% b = toeplitz(r)\v;						% (Levinson)
% egalr = Jury(b)\v;						% Levinson descendant
%
% (version sans le message pour les conflits)
% Auteur : J. Idier		Version 1.1	Date : 02/96

b = b(:);
p = length(b);
o = zeros(p,1);
B = Toeplitz(b,o) + Hankel(b,o);
B(:,1) = b;
