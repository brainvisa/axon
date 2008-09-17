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
% Modifie par  Philippe CIUCIU : Extension a un nb de variable qq : dec 2000
% Modifie par  Philippe CIUCIU : version a option + noms ficheirs courts Fev 2001

% Recuperation des noms des variables
  var = ' '; 		% Nom des variables a sauver
  ASCII=0;		% Flag pour sauver en ascii
  GZ=0;		% Flag pour sauver en .mat.gz
  if (nargin <1)
     fich = 'matlab.mat';
  elseif (nargin==1 & strcmpi(fich,'-gz'))
     fich = 'matlab.mat';
	  GZ=1;
  else
     nbvar = nargin-1;
     for i=1:nbvar
%         vari = eval(['v' int2str(i)]);
         vari = varargin{i};
	 		if ~strcmpi(vari,'-gz')
				if strcmpi(vari,'-ascii'); ASCII=1; end
	         var = [var  vari ' '];
			else
				GZ=1;
			end
     end
  end

	% Recuperation du nom du fichier
	fichbis=fliplr(fich);
	% pour permettre des noms de fichiers (sans extension) de 6 lettres et -
	% si terminaison en .mat.gz
	if (strncmp(fichbis,fliplr('.mat.gz'),7)) % strncmp ne hurle pas si 1 des args a - de 7 lettres
		GZ=1;	% il suffit de mettre une extension .gz au fichier de svgd sans passer par l'option -gz
   	fich = fliplr(fichbis(4:end));	% On enleve .gz
  	% si pas ascii et pas terminaison en .mat (fichier sans extension)
	elseif (~ASCII &~strncmp(fichbis,fliplr('.mat'),4)),% strncmp ne hurle pas si 1 des args a - de 4 lettres
		fich = [fich '.mat']; %  Ajout eventuel du .mat
	end
% fich contient le nom du fichier avec '.mat' sauf si option '-ascii'

% ajout du path au nom du fichier et recherche du fichier
  longfich =''; longfichgz ='';
% Flag de fichier compresse ou non compresse
  compressed = 0;
  uncompressed = 0;

  	longfich = which(fich);
	if ~GZ  %pas d'option -gz, ni de nom de fichier passe avec extension .mat.gz
		if ~strcmp(longfich,'') % fichier non compresse trouve
     		uncompressed = 1;
		else	% chemin passe en ligne
      	longfich = ls(fich); 
      	if ~strcmp(longfich,'');		% fichier non compresse trouve
          	uncompressed = 1;
	   		% suppression du retour chariot du a 'ls'
         	longfich  = longfich(1:length(longfich)-1);
			end
		end	
	else
		% recherche du fichier et du nom complet
  		longfich = which(fich);
		if strcmp(longfich,'') % .mat non trouve
   		longfichgz = which([ fich '.gz']); % recherche .mat.gz
   		if ~strcmp(longfichgz,'');			% fichier compresse trouve
        		compressed = 1;
        		longfich = longfichgz(1:length(longfichgz)-3);  %avec chemin + nom fichier
    		end
  		else 						% fichier non compresse trouve
   	  	uncompressed = 1;
   	  	longfichgz = [longfich '.gz'];
  		end
  		if ( strcmp(longfich,'') & strcmp(longfichgz,'') ) %si ni .mat.gz ni .mat trouves mais chemin passe en ligne
			longfichgz = ls([ fich '.gz']);
     		if ~strcmp(longfichgz,'')			% fichier compresse trouve
        		compressed = 1;
				% suppression du retour chariot du a 'ls'
        		longfichgz  = longfichgz(1:length(longfichgz)-1);	
        		longfich  = longfichgz(1:length(longfichgz)-3); % on enleve .gz
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
	end
% Traitement
  if uncompressed				% Fichier non compresse
     evalin('caller',['load ', longfich, var ]);
  elseif compressed				% Fichier compresse
     unix(['gunzip -c -q ' longfichgz ' > ' longfich]);%-c = ecrit s/ sortie standard, garde fichiers originaux inchanges, -q=quiet
     evalin('caller',['load ', longfich, var ]);
     unix(['rm -f ' longfich]);
  else						% Fichier introuvable
     beep; disp('??? Error using ==> loadgz');
     disp([ fich ' and ' fich '.gz: files not found.']);
  end
