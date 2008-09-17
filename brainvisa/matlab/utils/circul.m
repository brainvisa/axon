function M = circul(l);
% circul.m     Cree un matrice carree circulante 
% M=circul(l);
%~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
% Construit (sans boucle !) une matrice carree circulante
% definie par sa premiere ligne 'l'.
%~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
% T. Martin 07/94, modifie par J. Idier 01/97
%~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

l = l(:);
n = length(l);
M = reshape(l(:,ones(n-1,1)), n-1, n)';
M = [M flipud(l)];
