% toupper.m       minuscule ---> majuscule
%Fonction tranformant toutes les minuscules d'un
% tableau de chaines Matlab en majuscules
% et ne touchant pas aux autres caracteres
% forme d'appel :
%               texte_maj = toupper(texte_min)
%
% Version 1.0		08/93		F. Champagnat
%
function maj = toupper(min)

if isstr(min) == 0,
    disp('Erreur : l''argument d''entree n''est pas une variable chaine');
else
    maj = min;
    ind = find((min <= 'z') & (min >= 'a'));
    maj(ind) = min(ind) + ('A'-'a');
    maj=setstr(maj);         
end
