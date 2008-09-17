% batch matlab permettant de remplacer les
% occurrences d'une chaine ch1 par une chaine ch2
% dans un ensemble de fichiers source dont la liste
% est contenue dans un fichier 'temp', issu par
% exemple d'un find.

%ch = '%INCLUDE ''/sys/ins/dialog.ftn'''; 
%ch1 = [10, ch];
%ch2 = [10, '/*', ch, '*/'];
%ch2 = [10, 'c', ch];
 
ch1 = 'status_$t Status';
ch2 = 'int Status';

chaine = loadb('tempc');
ind = [0; find(chaine == 10)];	% 10 = retour chariot !

for n = 2:size(ind),
  fich = setstr(chaine(ind(n-1)+1:ind(n)-1)');
%  indf = find(fich == '/');
%  nomf = fich(indf(length(indf)-1)+1:indf(length(indf))-1);
%  ch = [' $(NODE)$(EDIR)/',nomf,'.dpd'];
%  ch1 = [10, ch];
%  ch2 = [10, '#', ch];
  substitue(fich,ch1,ch2,fich);
end
