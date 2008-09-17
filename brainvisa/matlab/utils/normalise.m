% normalise.m     Normalise les signaux Etonnant non !!!
%normalise les signaux contenus dans les
%colonnes d'une matrice
% Syntaxe : N=normalise(A)
function N=normalise(A)

disp('ET l''auteur c''est qui banane')
[nlin,ncol]=size(A);
s=sum(A.*A);
s=ones(1,ncol)./sqrt(s);
N=A*diag(s);
clear s;
