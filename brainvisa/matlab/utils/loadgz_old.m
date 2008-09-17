function loadgz(fich,v1,v2,v3,v4,v5,v6,v7,v8,v9,v10,v11,v12,v13,v14,v15,v16,v17,v18,v19,v20,v21,v22,v23,v24,v25)
% LOADGZ Charge des variables a partir d'un fichier eventuellement compresse
%
%   LOADGZ FICH charge les variables du fichier 'fich.mat' ou 'fich.mat.gz'
% 
%   LOADGZ charge les variables du fichier 'matlab.mat' ou 'matlab.mat.gz'
%
%   LOADGZ FICH X Y Z ... charge uniquement les variables specifiees.
%   le joker '*' peut etre utilise pour charger les variables 
%   correspondant a un certain format.
%
%   LOADGZ FICH -ASCII peut etre utilise pour charger un fichier ascii
%
% Herve CARFANTAN le 13 aout 1997
% Modifs des chemins Philippe CIUCIU

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

% Recuperation du nom du fichier
% Suppression eventuelle du '.gz'
  if strcmp(fich(length(fich)-2:length(fich)),'.gz'),
     fich = fich(1:length(fich)-3);
  end
%  Ajout eventuel du .mat
  if (~ASCII & ~strcmp(fich(length(fich)-3:length(fich)),'.mat')),
     fich = [fich '.mat'];
  end
% fich contient le nom du fichier avec '.mat' sauf si option '-ascii'


% ajout du path au nom du fichier et recherche du fichier
  longfich =''; longfichgz ='';
% Flag de fichier compresse ou non compresse
  compressed = 0;
  uncompressed = 0;

% recherche du fichier et du nom complet
  longfich = which(fich);
  if strcmp(longfich,'')
     longfichgz = which([ fich '.gz']);
     if ~strcmp(longfichgz,'');			% fichier compresse trouve
        compressed = 1;
        longfich = longfichgz(1:length(longfichgz)-3);
     end
  else 						% fichier non compresse trouve
     uncompressed = 1;
     longfichgz = [ longfich '.gz'];
  end
  if ( strcmp(longfich,'') & strcmp(longfichgz,'') )
     longfichgz = ls([ fich '.gz']);
     if ~strcmp(longfichgz,'')			% fichier compresse trouve
        compressed = 1;
	% suppression du retour chariot du a 'ls'
        longfichgz  = longfichgz(1:length(longfichgz)-1);	
        longfich  = longfichgz(1:length(longfichgz)-3);
     else 
        longfich = ls(fich); 
        if ~strcmp(longfich,'');		% fichier non compresse trouve
           uncompressed = 1;
	   % suppression du retour chariot du a 'ls'
           longfich  = longfich(1:length(longfich)-1);	
           longfichgz = [ longfich '.gz'];
        end
     end
  end

% Traitement
  if uncompressed				% Fichier non compresse
     evalin('caller',['load ', longfich, var ]);
  elseif compressed				% Fichier compresse
     unix(['gunzip -c -q ' longfichgz ' > ' longfich]);
     evalin('caller',['load ', longfich, var ]);
     unix(['rm -f ' longfich]);
  else						% Fichier introuvable
     beep; disp('??? Error using ==> loadgz');
     disp([ fich ' and ' fich '.gz: files not found.']);
  end
