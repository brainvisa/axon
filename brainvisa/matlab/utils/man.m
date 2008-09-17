function man(fich)
% man.m generalisation du help Matlab pour trouver le
% commentaire d'un fichier MEX en tete du source fich.c
% (par exemple, dans ~seismic/matlab/mex)	J.I., mars 1997

l = length(fich);
if(fich(l-1)=='.')&(fich(l)=='c') % fichier .c
  S = loadbs(fich);
elseif exist(fich)==3	% fich is a MEX-file on MATLAB's search path
  S = eval(['loadbs(''' fich '.c'')']);
  fich = [fich '.c'];
end
if exist('S')
  if isempty(S)
    fprintf('Probleme avec %s\n', fich);
  else
    k = str1find(S,'/*');	% 1ere occurrence de '/*'
    l = str1find(S,'*/');	% 1ere occurrence de '*/'
      if k+2<l-1
        fprintf('%s\n',S(k+2:l-1));
      end
  end
else
  eval(['help ' fich])
end       
