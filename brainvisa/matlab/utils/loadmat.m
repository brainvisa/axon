% loadmat.m      Chargement de matrices speciales
% forme d'appel : [x, name] = loadmat(fid)
%
%	Auteur:	F. Champagnat		08/93
%
%	Cette fonction est l'equivalent Matlab de la fonction C
% loadmat(); elle permet de charger successivement des matrices
% Matlab dans un flot prealablemt ouvert avec un fopen().
%	En cas d'erreur renvoie des matrices vides.
%
%	Attention : les valeurs prises par la variable type
% sont valables pour les stations de type HP/Apollo. Pour 
% d'autres machines consulter 'MATLAB 4.0 External Interface Guide'
% au chapitre 'Reading and Writing Data Files', paragraphe
%  'MAT-File Structure' p.29
%

function [x, name] = loadmat(fid)

x=[];
name=[];
					% Sur HP/Apollo :
[type, nbok] = fread(fid, 1, 'long');	% type = 1000 -> MATRICE
if(nbok ~= 1) return; end		%        1001 -> TEXTE

[nlin, nbok] = fread(fid, 1, 'long');	% Nombre de lignes
if(nbok ~= 1) return; end

[ncol, nbok] = fread(fid, 1, 'long');	% Nombre de colonnes
if(nbok ~= 1) return; end

[imagf, nbok] = fread(fid, 1, 'long');	% Flag indiquant la presence
if(nbok ~= 1) return; end		% d'une partie imaginaire

[lnom, nbok] = fread(fid, 1, 'long');	% Longueur de la chaine contenant
if(nbok ~= 1) return; end		% le nom de la matrice 
					% (y compris le '\0' final)

[name, nbok] = fread(fid, [1, lnom], 'char');
if(nbok ~= lnom) 
  name = [];
  return; 
end

name = name(1:lnom-1);			% Supression du '\0'
name = setstr(name);			% Specifie que c'est une chaine

% Charge la partie reelle de la matrice

[x, nbok] = fread(fid, [nlin, ncol], 'double');
if(nbok ~= nlin*ncol)
  x = []; 
  return;
end

if(type == 1001)		% Contient du texte
  x = setstr(x);
  return;
end

if(imagf ~= 0)			% Partie imaginaire presente

  [y, nbok] = fread(fid, [nlin, ncol], 'double');
  if(nbok ~= nlin*ncol)
    disp('Erreur : impossible de lire partie imaginaire')
    x = [];
  end
  x = x + (j*y);
end
