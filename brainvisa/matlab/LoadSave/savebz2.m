function savebz2(fich,varargin)
% SAVEBZ2 saves variables in a possibly gzipped file
%
%   SAVEBZ2 FICH saves all the variables belonging to the current workspace
%   in the 'fich.mat' file
%   SAVEBZ2 FICH -BZ2 saves all the variables belonging to the current workspace
%   in the 'fich.mat.bz2' file
%
%   SAVEBZ2 saves all the variables in the 'matlab.mat' file
%   SAVEBZ2 -BZ2 saves all the variables in the 'matlab.mat.bz2' file
%
%   SAVEBZ2 FICH X Y Z ... only saves the specified variables
%   The wildcard '*' can be used to save the variables matching with
%   a prespecifed string
%
%   SAVEBZ2 FICH -ASCII can be used to save an ascii file
%
%   SAVEBZ2 FICH -v4 can be used to save matlab 4 file
%
% 	From Herve CARFANTAN's SAVEGZ done in 97/08/13
%
%
% Modifief by P. Ciuciu 00/12/06 : 
%		extension to more 25 variables
% Modifief by P. Ciuciu 01/31/01 : 
%		filename of length <=6 without extension are allowed
%________________________________________________________________
% savebz2.m	2.0				Philippe Ciuciu			02/05/30


% Recuperation des noms des variables
  var = ' '; 		% Nom des variables a sauver
  ASCII=0;		% Flag pour sauver en ascii
  GZ=0;		% Flag pour sauver en .mat.bz2
  if (nargin <1)
     fich = 'matlab.mat';
  elseif (nargin==1 & strcmpi(fich,'-bz2'))
     fich = 'matlab.mat';
	  GZ=1;
  else
     nbvar = nargin-1;
     for i=1:nbvar
%         vari = eval(['v' int2str(i)]);
         vari = varargin{i};
	 		if ~strcmpi(vari,'-bz2')
				if strcmpi(vari,'-ascii'); ASCII=1; end
	         var = [var  vari ' '];
			else
				GZ=1;
			end
     end
  end
	fichbis=fliplr(fich);
	% pour permettre des noms de fichiers (sans extension) de 6 lettres et -
	% si terminaison en .mat.bz2
	if (strncmp(fichbis,fliplr('.mat.bz2'),8)) % strncmp ne hurle pas si 1 des args a - de 7 lettres
		GZ=1;	% il suffit de mettre une extension .bz2 au fichier de svgd sans passer par l'option -bz2
   	fich = fliplr(fichbis(5:end));	% On enleve .bz2
  	% si pas ascii et pas terminaison en .mat (fichier sans extension)
	elseif (~ASCII &~strncmp(fichbis,fliplr('.mat'),4)),% strncmp ne hurle pas si 1 des args a - de 4 lettres
		fich = [fich '.mat']; %  Ajout eventuel du .mat
	end

	str = ['save ', fich, var]; % sauvegarde
   evalin('caller',str);				% Sauvegarde

	OS = strcmp(computer,'PCWIN');
	if ~OS
		[s,w]=unix(['chmod 755 ' fich]); % update file properties and redirect stdout message yielded by the unix call
	end
% Traitement
  if GZ
%		if ~OS
%  			rep = unix(['bzip2 -9 -q -f ' fich]);% Compress -q:quiet,-9=--best,-f:force la comp/decompress
%		else
%  			rep = dos(['bzip2 -9 -q -f ' fich]);% Compress -q:quiet,-9=--best,-f:force la comp/decompress
%		end
		if strcmp(computer,'LNX86') | strcmp(computer,'GLNX86');    %LNX86 under matlab5.3 or GLNX86 under matlab6.1
			[rep,w] = unix(['bzip2 -9 -q -f -z ' fich]);
%			rep = system(['bzip2 -9 -q -f -z ' fich]);
		elseif strcmp(computer,'SOL2');
			[rep,w] = unix(['bzip2 -9 -f -z ' fich]);
%			rep = system(['bzip2 -9 -f -z ' fich]);
		elseif strcmp(computer,'PCWIN'),
			[rep,w]=system(['c:\bzip2 -9 -q ' fich]);
		end
  		if rep,
     		beep; disp('??? Error using ==> savegz2');
     		disp([ ' Problem to compress ' fich]);
		end
  end
