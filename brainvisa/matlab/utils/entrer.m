function y = entrer(commen, def);
% entrer.m   acquisition d'une valeur numerique
% Syntaxe : function y = entrer(commen, def);
% Acquisition d'une valeur numerique.
% cette foncion ENTRER utilise la fonction input de 
% matlab, repose la question si le reponse tapee au
% clavier par l'utilisateur pose un probleme et renvoie
% la valeur par defaut 'def' si la reponse est '.'
% 'comment' est la question a poser.
disp('Et l''auteur il a honte de ses creations')
disp('Les fichiers de SEISMIC doivent mentionner l''auteur et la date')

     if isempty(def)
       commen = [commen, ' =>'];
     else
     commen = [commen, ' [', num2str(def), '] =>'];
     end
     while 1
       str = input(commen,'s');
       if strcmp(str, '.')
        y = def;
       elseif (length(str))
	  y = eval(str);
       end
       if ~(isempty(y))
          break;
       end   
     end
