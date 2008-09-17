%  lsmat.m        liste les fichiers .mat en virant le .mat
%  forme d'appel : lsmat(nb)
%
%	Auteur:	J. Idier			06/94
%
%	Cette fonction fait un 'ls *.mat' sur nb colonnes,
% en virant le radical '.mat'. Developpee pour la session.
% Par defaut, nb = 4.
%

function lsmat(nb)

chaine = ls('*.mat');
if (chaine == '')
return
else
if exist('nb') ~= 1     % If no type parameter has been set
	nb = 4;         % Set it to default value
end
nb = max(nb,1);

L = length(chaine);
v = (chaine == 10);			% Detecte les 'return'
w = [v(2:L) 0] | [v(3:L) 0 0] | [v(4:L) 0 0 0] | [v(5:L) 0 0 0 0];
					% Fabrique un masque sur les 4 caracteres
					% precedents (donc sur '.mat')
if nb>1
  l = sum(v);				% Nombre de 'return'
  tab = ones(1,l);
  tab(nb:nb:l) = zeros(1,floor(l/nb));
  tab(l) = 0;				% On finit par un 'return'
  neuf = 9;
  pos = find(v);
  len = [pos(1) diff(pos)];		% Longueurs des mots

  chaine(pos(tab)) = neuf(tab(tab));	% tout les nb-1 sur nb 'return',
					% on remplace par un 'tab'.

  chaine(pos-4) = neuf(ones(1,l));	% les '.' sont d'abord remplaces par 'tab'.
  w(pos-4) = (len > 8+4);		% Ce 'tab' supplementaire saute si
					% la longueur depasse 8.	
end

chaine = chaine(~w);	% Applique l'inverse du masque

fprintf('%s',chaine)	% Affichage
end
