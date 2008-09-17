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
		% svgd en .gz et  fich.mat existe deja :
		fich = ['_new_' fich]
  	% si pas ascii et pas terminaison en .mat (fichier sans extension)
	elseif (~ASCII &~strncmp(fichbis,fliplr('.mat'),4)),% strncmp ne hurle pas si 1 des args a - de 4 lettres
		if ~GZ
			fich = [fich '.mat'];
		else
			% on passe par un nom temporaire pour ne pas ecraser fich.mat, s'il existe deja,
			% et si la svgd est avec meme nom mais en -gz : fich.mat.gz <> gzip fich.mat
 	   	fich = ['_new_' fich '.mat'];
		end
	end

% Construction de la chaine de caractere du noms de fichier
% test si fich.mat exite deja dans repertoire courant
%	if GZ
%		Temp=dir;
%		Verif=struct2cell(Temp(find(~(cat(Temp.isdir)))+1)); % +1 : bug de cat ; il oublie le rep courant '.'
%		NbFichRep=length(Verif);
%		[NomFichs{1:NbFichRep}]=deal(Verif{1:4:4*NbFichRep});
%		while (i<=NbFichRep & ~strcmp(NomFichs{i},fich))
%			i=i+1;
%	  	end
%		% on passe par un nom temporaire pour ne pas ecraser fich.mat, s'il existe deja,
%		% et si la svgd est avec meme nom mais en -gz : fich.mat.gz <> gzip fich.mat
%		if (i<NbFichRep)
%			fich=strcat('_new_',fich); 
%	  	end
%	end
%keyboard;
	str = ['save ', fich, var] % sauvegarde
   evalin('caller',str);				% Sauvegarde
	unix(['chmod 755 ' fich]); % MAJ des droits

% Traitement
  if GZ
  		rep = unix(['gzip -9 -q -f ' fich]);% Compression -q : quiet, -9=--best, -f : force la comp/decompression
		unix(['mv -f ' fich '.gz ' fich(6:end) '.gz']); % on vire _new_
  		if rep,
     		beep; disp('??? Error using ==> savegz');
     		disp([ ' Probleme lors de la compression du fichier ' fich']);
		end
  end
