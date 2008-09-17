function chaine2 = strcut(chaine1,n)
% strcut.m	extrait la n-ieme chaine dans une suite separee par des
%		<RETURN>, cad eg ['A' 10 'bomber,' 10 'Nine']	
% Permet de manipuler un faux tableau de chaine de caracteres de
% longueur variable.
%~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
% chaine2=strcut(chaine1,nb)
%
% Auteur : J. Idier				Date : 09/96
%
% Voir aussi findstr et strsubst
%~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

ind = find(chaine1==10);
ind = [0 ind length(chaine1)+1];
chaine2 = chaine1(ind(n)+1:ind(n+1)-1);
