function b = base(a, n, lmin)
% base.m     decomposition en base n 
% base(a, n) est la decomposition en base n de floor(abs(a)), sous
% forme d'un vecteur ligne. Si a est un vecteur, le resultat
% est une matrice. lmin impose un format minimum (n = 2 par defaut).
%	Auteur :	J. Idier	Date : 06/92	v.2 : 04/95

if exist('n') ~= 1		% If no n has been set,
  n = 2;			% Set it to default value
end

ln = log(n);
a = a(:);
a = floor(abs(a));
L = floor(log(max(a+eps))/ln);	% Fournit la plus grande puissance
				% de n contenue dans a
if exist('lmin') == 1
  L = max(L,lmin-1);
end

l = round(exp(ln*(L:-1:0)));
b = rem(floor(a*(1./l)),n);
