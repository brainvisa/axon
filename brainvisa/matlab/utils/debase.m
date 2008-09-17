function b = debase(a, n)
% debase.m         operation inverse de base.m 
% debase(a, n) est l'inverse de base(), valable pour un vecteur n-aire
% ou une matrice interpretee ligne par ligne (n = 2 par defaut).
%	Auteur :	J. Idier	Date : 06/92

if exist('n') ~= 1	% If no n has been set,
  n = 2;		% Set it to default value
end
if(min(size(a)) == 1)
  a = a(:)';
end
l = round(exp(log(n)*(size(a,2)-1:-1:0)'));
b = a*l;
