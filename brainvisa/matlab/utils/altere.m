% altere.m    Fonction speciale de manipulation de chaines de caracteres
%
% fonction Matlab permettant de remplacer les
% occurrences d'une chaine ch1 par une chaine ch2
% dans un ensemble de fichiers source dont la liste
% est contenue dans le fichier 'liste', issu par
% exemple d'un find.
% forme d'appel : altere(liste, ch1, ch2)

function altere(liste, ch1, ch2)

disp(' Et l''auteur alors , il a honte de ses creations');
chaine = loadb(liste);
ind = [0; find(chaine == 10)];	% 10 = retour chariot !

for n = 2:size(ind),
  fich = setstr(chaine(ind(n-1)+1:ind(n)-1)');
  substitue(fich,ch1,ch2,fich);
end
