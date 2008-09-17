function y = entrer_ch(commen, def);    
% entrer_ch.m   acquisition d'une chaine de caracteres 
% Syntaxe : function y = entrer_ch(commen, def);    
% Acquisition d'une chaine de caracteres.
% cette foncion ENTRER_CH utilise la fonction input de 
% matlab, repose la question si le reponse tapee au
% clavier par l'utilisateur pose un probleme et renvoie
% la valeur par defaut 'def' si la reponse est '.'
% 'comment' est la question a poser.
disp('L''auteur a-t''il honte de ses creations');
disp('Les fichiers de Seismic doivent mentionner l''auteur et la date...')
 if isempty(def)
       commen = [commen, ' =>'];
     else
     commen = [commen, ' [', def, '] =>'];
     end
     while 1
       y = input(commen,'s');
       if y == '.'
        y = def;
       end   
       if isempty(y);
       else
        break;
       end
     end
