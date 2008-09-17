function savegz(fich,varargin)
% SAVEGZ saves variables in a possibly gzipped file
%
%   SAVEGZ FICH saves all the variables belonging to the current workspace
%   in the 'fich.mat.gz' file
%
%   SAVEGZsaves all the variables in the 'matlab.mat.gz' file
%
%   SAVEGZ FICH X Y Z ... only saves the specified variables
%   The wildcard '*' can be used to save the variables matching with
%   a prespecifed string
%
%   SAVEGZ FICH -ASCII can be used to save an ascii file
%
%   SAVEGZ FICH -v4 can be used to save matlab 4 file
%
% Herve CARFANTAN le 13 aout 1997
%
%
% Modifie par Chuck le 19 Aout 1999 -> rajout du cas dans lequel le fichier s'appelle
%                                      toto.mat.gz (avant, savegz creait toto.mat.gz.mat.gz)
% Modifie par Phil dec 2000 : extension a plus de 25 variables
% Modifie par Phil 31 janvier 2001 : possibilite de noms de fichiers sans extension de 6 lettres et -

% Recuperation des noms des variables
  var = ' '; 		% Nom des variables a sauver
  ASCII=0;		% Flag pour sauver en ascii
  if nargin <1
     fich = 'matlab.mat';
  else
     nbvar = nargin-1;
     for i=1:nbvar
%         vari = eval(['v' int2str(i)]);

         vari = varargin{i};
	 if strcmp(vari,'-ascii'); ASCII=1; end
         var = [var  vari ' '];
     end
  end
% Recuperation du nom du fichier (ajout eventuel du .mat)
%  if (strcmp(fich(length(fich)-6:length(fich)),'.mat.gz'))
%     fich = fich(1:length(fich)-3);		% On enleve .gz
%  elseif (~ASCII & ~strcmp(fich(length(fich)-3:length(fich)),'.mat')),
%     fich = [fich '.mat'];
%  end

  fichbis=fliplr(fich);
	% pour permettre des noms de fichiers (sans extension) de 6 lettres et -
	if (strncmp(fichbis,fliplr('.mat.gz'),7)) % strncmp ne hurle pas si 1 des args a - de 7 lettres
     fich = fliplr(fichbis(4:end));		% On enleve .gz
  elseif (~ASCII & ~strncmp(fichbis,fliplr('.mat'),4)),
     fich = [fich '.mat'];
  end


% Construction de la chaine de caractere
  str = ['save ', fich, var];

% Traitement
  evalin('caller',str);				% Sauvegarde
  rep = unix(['gzip -9 -q -f ' fich]);		% Compression -q : quiet, -9=--best, -f : force la comp/decompress
  unix(['chmod 755 ' fich, '.gz']); % MAJ des droits
  if rep,
     beep; disp('??? Error using ==> savegz');
     disp([ ' Probleme lors de la compression du fichier ' fich']);
  end
