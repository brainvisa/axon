% tolower.m         majuscule ---> minuscule
% Fonction tranformant toutes les Majuscules d'un
% tableau de chaines Matlab en minuscules
% et ne touchant pas aux autres caracteres
% forme d'appel :
%               texte_min = tolower(texte_maj)
%
% Version 1.0		10/92		F. Champagnat
%
function min = tolower(maj)

if isstr(maj) == 0,
    disp('Erreur : l''argument d''entree n''est pas une variable chaine');
else
    flags = (maj <= 'Z') & (maj >= 'A');
    min = maj + ('a'-'A')*flags;
    min=setstr(min);         
end
