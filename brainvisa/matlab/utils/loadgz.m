function loadgz(fich,varargin)
% LOADGZ downloads the variables from a possibly gzipped file
%
%   LOADGZ FICH downloads the variables from the 'fich.mat' or 'fich.mat.gz' file
% 
%   LOADGZ  downloads the variables from the 'matlab.mat' ou 'matlab.mat.gz' file
%
%   LOADGZ FICH X Y Z ... only downloads the specified variables X Y Z ...
%   The wildcard '*' can be used to download a subset of variables matching with a
%   prespecifed string
%
%   LOADGZ FICH -ASCII can be used to download an ascii file
%
% Herve CARFANTAN le 13 aout 1997
% Modifs : Extension a un nb de variable qq : Philippe CIUCIU dec 2000

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
