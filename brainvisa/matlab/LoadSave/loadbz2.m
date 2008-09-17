function varargout = loadbz2(fich,varargin)
% LOADBZ2 downloads the variables from a possibly bzipped file
%
%   LOADBZ2 FICH downloads the variables from the 'fich.mat' or 'fich.mat.bz2' file
% 
%   LOADBZ2  downloads the variables from the 'matlab.mat' ou 'matlab.mat.bz2' file
%
%   LOADBZ2 FICH X Y Z ... only downloads the specified variables X Y Z ...
%   The wildcard '*' can be used to download a subset of variables matching with a
%   prespecifed string
%
%   LOADBZ2 FICH -ASCII can be used to download an ascii file
%   S= loadbz2(FICH,VAR) sets S to the value of VAR
%
%- Description: This is the first stable release where function-like calling formats of loadbz2 have been implemented  ; Before, loadbz2 was called using a command-line format: 
%- 	loadbz2 (try to load matlab.mat)
%- 	loadbz2 -gz2 (try to load matlab.mat.bz2)
%- 	loadbz2 file.mat
%- 	loadbz2 file.mat.bz2
%- 	loadbz2 file	-gz2
%- 	loadbz2 file.mat -gz2 
%- 	loadbz2 file var1 var2
%- 	loadbz2 file -ascii
%-  where file is either defined with a pathname component, or just relative to the current directory. Straight filenames like toto.mat are also sought in the MATLABPATH using which .  
%-  
%- 	The following calling formats are now available:
%- 	1/
%- 	[test1,test2]=loadbz2(file,var1,var2); where file, var and var2 are 
%- 	known strings
%- 	test1 and test2 are struct arrays that contain var1 anbd var2, respectively
%- 	var1 is loaded in test1.var1
%- 	var2 is loaded in test1.var2 (To date, I don't know any way to directly
%- 	assign test1 to var1 since test1 is unknown when calling loadbz2)
%- 	2/ 
%- 	test1=loadbz2(file,var1,var2);we then get the var1 and var2 values from 
%- 	test1.var1 and	test1.var2
%- 	3/ obviously tes1=loadbz2(file); load all variables (whatever their type)
%- 	saved in file into the test1 structure
%- %___________________________________________________________________
% loadbz2.m		3.0				Philippe Ciuciu					02/07/15
 
% Recuperation des noms des variables
  var = ' '; 		% Nom des variables a sauver
  varfunc = []; 		% Nom des variables a sauver
  varsepar = [];			% svgd verticale des variables
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
				if strcmpi(vari,'-ascii'); ASCII=1; else varsepar=strvcat(varsepar,vari); end
	         var = [var  vari ' '];	varfunc=[varfunc '''' vari '''' ','];
			else
				GZ=1;
			end
     end
  end
  if ~isempty(varfunc), varfunc=varfunc(1:end-1);end
    % save fich
	fichter=fich;
	% Recuperation du nom du fichier
	fichbis=fliplr(fich);
	% pour permettre des noms de fichiers (sans extension) de 6 lettres et -
	% si terminaison en .mat.bz2
	if (strncmp(fichbis,fliplr('.mat.bz2'),8)) % strncmp ne hurle pas si 1 des args a - de 7 lettres
		GZ=1;	% il suffit de mettre une extension .bz2 au fichier de svgd sans passer par l'option -bz2
   	    fich = fliplr(fichbis(5:end));	% On enleve .bz2
  	% si pas ascii et pas terminaison en .mat (fichier sans extension)
	elseif (~GZ & ~ASCII &~strncmp(fichbis,fliplr('.mat'),4)),% strncmp ne hurle pas si 1 des args a - de 4 lettres
		fich = [fich '.mat']; %  Ajout eventuel du .mat
    elseif GZ & strncmp(fichbis,fliplr('.mat'),4)
        fichter = [fichter '.bz2'];
    elseif GZ & isempty(findstr(fich,'.'))
        fichter = [fichter '.mat.bz2'];
    end
    
    % fich contient le nom du fichier avec '.mat' sauf si option '-ascii'
  longfich =''; longfichgz ='';
% Flag de fichier compresse ou non compresse
  compressed = 0;
  uncompressed = 0;

%	MAT53=0;MAT61=0;	% and so on if the `dir' function has been modified if future releases
%	ver=version;	% check for R11 (Matlab53) or R12 (Matlab61)
%	if ~isempty(findstr(ver,'5.3'))
%		MAT53=1;
%	elseif ~isempty(findstr(ver,'6.1'))
%		MAT61=1;
%	end
	if ~GZ  %ni d'option -bz2, ni de nom de fichier passe avec extension .mat.bz2
		if exist(fich)==2 % fichier non compresse trouve ds repertoire courant 
								% ou ds repertoire correspondant	au PATH donne en ligne
     		uncompressed = 1;
			longfich=fich;
		else
			Index_str = findstr(fich,filesep);
			if isempty(Index_str)	% nom de fichier sans PATH
				longfich = which(fich);	% rechercher du PATH ds MATLABPATH
				% fichier non compresse trouve ds MATLABPATH
				if ~strcmp(longfich,''),uncompressed = 1;end
			else	% chemin passe en ligne
%                longfich = dir(fich);
                 if exist(fich)==2
                    longfich=fich;%recup nom de fichier avec PATH
				    % fichier non compresse trouve ds rep passe en ligne
%				if exist(longfich)==2, 
                    uncompressed = 1;
                end
    		end
		end
	else	% GZ=1
		% recherche du fichier et du nom complet
		Index_str = findstr(fichter,filesep);
		if isempty(Index_str)
			longfich = which(fichter);	%recup fichier ds MATLABPATH
		else % chemin passe en ligne
            %longfich=dir(fichter);
            if exist(fichter),
                longfich=fichter;
			%if length(longfich)
			%    longfich=longfich.name;	%recup nom de fichier avec PATH
            end
		end
		if ~strcmp(longfich,'') & exist(longfich)==2    %length(longfich)
            compressed=1;
		    longfichgz=longfich;					% fichier .mat.bz2
		    longfich=longfich(1:end-4);		%longfich devient fichier .mat
        end    
	end
%	if nargout
%		EnvVar=evalin('caller','whos');VarNb=length(EnvVar);
%	end

	% Traitement
	if uncompressed				% Fichier non compresse
		if ~nargout, evalin('caller',['load ', longfich, var ]);
		else
			if strcmpi(var,'-ascii')
				eval(['varargout{1}=load(''' longfich ''',''',var,''');']);
			else 
				VarNb = size(varsepar,1);
				if nargout==VarNb
					for gg=1:VarNb, 
						eval(['varargout{' num2str(gg) '}=load(''' longfich ''',''',deblank(varsepar(gg,:)),''');']);
					end
				else
								eval(['varargout{1}=load(''' longfich ''',',varfunc,');']);
				end
			end
		end
	elseif compressed				% Fichier compresse
		try,
			%status = system('bzip2 --help');
    		if strcmp(computer,'LNX86')|strcmp(computer,'GLNX86'),
%				system(['bunzip2 -q -c ' longfichgz ' > ' longfich]);%-c = ecrit s/ sortie standard, garde fichiers originaux inchanges, -q=quiet
				[status,w]=unix(['bunzip2 -q -c ' longfichgz ' > ' longfich]);%-c = ecrit s/ sortie standard, garde fichiers originaux inchanges, -q=quiet
				if ~nargout, evalin('caller',['load ', longfich, var ]);
				else
					if isempty(varsepar)
%						eval(['varargout{1}=load(''' longfich ''',''',var,''');']);
						eval(['varargout{1}=load(''' longfich ''');']);
					else 
						VarNb = size(varsepar,1);
						if nargout==VarNb
							for gg=1:VarNb, 
								eval(['varargout{' num2str(gg) '}=load(''' longfich ''',''',deblank(varsepar(gg,:)),''');']);
							end
						else
								eval(['varargout{1}=load(''' longfich ''',',varfunc,');']);
						end
					end
				end
%				system(['rm -f ' longfich]);
				[status,w]=unix(['rm -f ' longfich]);
			elseif strcmp(computer,'SOL2'),
%				system(['bunzip2 -c ' longfichgz ' > ' longfich]);%-c = ecrit s/ sortie standard, garde fichiers originaux inchanges, -q=quiet
				[status,w]=unix(['bunzip2 -c ' longfichgz ' > ' longfich]);%-c = ecrit s/ sortie standard, garde fichiers originaux inchanges, -q=quiet
				if ~nargout, evalin('caller',['load ', longfich, var ]);
				else
					if isempty(varsepar)
%						eval(['varargout{1}=load(''' longfich ''',''',var,''');']);
						eval(['varargout{1}=load(''' longfich ''');']);
					else 
						VarNb = size(varsepar,1);
						if nargout==VarNb
							for gg=1:VarNb, 
								eval(['varargout{' num2str(gg) '}=load(''' longfich ''',''',deblank(varsepar(gg,:)),''');']);
							end
						else
								eval(['varargout{1}=load(''' longfich ''',''',varfunc,''');']);
						end
					end
				end
				[status,w]=unix(['\rm ' longfich]);
			elseif strcmp(computer,'PCWIN'),
				[status,w]=system(['c:\bzip2 -d -q ' longfichgz]);
				if ~nargout, evalin('caller',['load ', longfich, var ]);
				else
					if isempty(varsepar)
%						eval(['varargout{1}=load(''' longfich ''',''',var,''');']);
						eval(['varargout{1}=load(''' longfich ''');']);
					else 
						VarNb = size(varsepar,1);
						if nargout==VarNb
							for gg=1:VarNb, 
								eval(['varargout{' num2str(gg) '}=load(''' longfich ''',''',deblank(varsepar(gg,:)),''');']);
							end
						else
								eval(['varargout{1}=load(''' longfich ''',',varfunc,');']);
						end
					end
				end
				[status,w]=system(['c:\bzip2 -9 -q -f -z ' longfich]);
			end
		catch,
			warning('bzip2 is not installed on your machine !');
			warning('see http://sources.redhat.com/bzip2/');return;
		end
  else						% Fichier introuvable
     beep; %disp('??? Error using ==> loadbz2');
     if GZ, fprintf([fich '.bz2: file not found.\n']);error(' ');
     else, fprintf([fich ' and ' fich '.bz2' ': files not found.\n']);error(' ');
     end    
	end
%	if nargout
%		NewEnvVar=evalin('caller','whos');
%		if length(NewEnvVar)~=VarNb
%	end
