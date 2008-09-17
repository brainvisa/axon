function savegz(fich,v1,v2,v3,v4,v5,v6,v7,v8,v9,v10,v11,v12,v13,v14,v15,v16,v17,v18,v19,v20,v21,v22,v23,v24,v25)
% SAVEGZ Charge des variables a partir d'un fichier eventuellement compresse
%
%   SAVEGZ FICH sauve toutes les variables de l'espace de travail
%   dans le fichier 'fich.mat.gz'
%
%   SAVEGZ sauve les variables dans le fichier 'matlab.mat.gz'
%
%   SAVEGZ FICH X Y Z ... sauve uniquement les variables specifiees.
%   le joker '*' peut etre utilise pour sauver les variables 
%   correspondant a un certain format.
%
%   SAVEGZ FICH -ASCII peut etre utilise pour sauver un fichier au format ascii
%
%   SAVEGZ FICH -v4 peut etre utilise pour sauver un fichier au format matlab 4
%
% Herve CARFANTAN le 13 aout 1997
%
%
% Modifie par Chuck le 19 Aout 1999 -> rajout du cas dans lequel le fichier s'appelle
%                                      toto.mat.gz (avant, savegz creait toto.mat.gz.mat.gz)
%

% Recuperation des noms des variables
  var = ' '; 		% Nom des variables a sauver
  ASCII=0;		% Flag pour sauver en ascii
  if nargin <1
     fich = 'matlab.mat';
  else
     nbvar = nargin-1;
     for i=1:nbvar
         vari = eval(['v' int2str(i)]);
	 if strcmp(vari,'-ascii'); ASCII=1; end
         var = [var  vari ' '];
     end
  end

% Recuperation du nom du fichier (ajout eventuel du .mat)
  if (strcmp(fich(length(fich)-6:length(fich)),'.mat.gz'))
     fich = fich(1:length(fich)-3);		% On enleve .gz
  elseif (~ASCII & ~strcmp(fich(length(fich)-3:length(fich)),'.mat')),
     fich = [fich '.mat'];
  end

% Construction de la chaine de caractere
  str = ['save ', fich, var];

% Traitement
  evalin('caller',str);				% Sauvegarde
  rep = unix(['gzip -9 -q -f ' fich]);		% Compression
  if rep,     
     beep; disp('??? Error using ==> savegz');
     disp([ ' Probleme lors de la compression du fichier ' fich']);
  end
