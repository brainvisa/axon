% renomme.m      Change le nom d'un ensemble de fichiers
%
% batch matlab permettant de changer le nom
% d'un ensemble de fichiers dont la liste
% est contenue dans un fichier 'temp', issu par
% exemple d'un find.

chaine = loadb('templ');
ind = [0; find(chaine == 10)];	% 10 = retour chariot !
for n = 2:size(ind),
  fich = setstr(chaine(ind(n-1)+1:ind(n)-1)');
  fich2 = fich;
  fich2(length(fich2)) = 'h';
  eval(['!mv ',fich,' ',fich2])
end    
