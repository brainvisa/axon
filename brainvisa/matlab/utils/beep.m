function beep(N)

% beep.m fonction qui fait des beeps
%
% Entree : nombre de beep (1 par defaut)
%
% Sortie : rien 
%
% Auteur : Giovannelli Jean-Francois 
%	   (avec l'aide precieuse de M. Brette Stephane)
%	   (sous le regard attendri de M. Bercher Jean-Francois)
%
% Date : le 13 septembre 1995
%
% Version 1.0
%

% Initialisation des variables
	if nargin==0
		N=1;
	end

% Construction de la chaine de caracteres qui font beep
	chaine = ones(N*100,1) * 7;

% Affichage des caracteres (cad des beep)
	disp(sprintf('%s',chaine))

