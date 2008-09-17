function savegz(fich,varargin)
% SAVEGZ saves variables in a possibly gzipped file
%
%   SAVEGZ FICH saves all the variables belonging to the current workspace
%   in the 'fich.mat' file
%   SAVEGZ FICH -GZ saves all the variables belonging to the current workspace
%   in the 'fich.mat.gz' file
%
%   SAVEGZ saves all the variables in the 'matlab.mat' file
%   SAVEGZ -GZ saves all the variables in the 'matlab.mat.gz' file
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

	str = ['save ', fich, var]; % sauvegarde
   evalin('caller',str);				% Sauvegarde
	unix(['chmod 755 ' fich]); % MAJ des droits

% Traitement
  if GZ
  		rep = unix(['gzip -9 -q -f ' fich]);% Compress -q:quiet,-9=--best,-f:force la comp/decompress
  		if rep,
     		beep; disp('??? Error using ==> savegz');
     		disp([ ' Probleme lors de la compression du fichier ' fich']);
		end
  end
