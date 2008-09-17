% flip.m = FLIPLR + FLIPUD... pratique pour les vecteurs !
%  
%                Auteur: J. Idier    Date: 11/94.
%	See also FLIPUD, FLIPLR, ROT90.

function y = flip(x)
y = fliplr(flipud(x));
