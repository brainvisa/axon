% goptions.m      Positionne les options de descente pour gpavXX.m
%
% Ce programme est l'analogue pour gpavXX du programme foptions associe a fminu 
%
% OPTIONS = goptions
%
% options presentes :
%
% OPTIONS(1)	: 	1 affichage lors de l'optimisation
% OPTIONS(2)	: 	critere d'arret :tolerance sur x (1e-4 par defaut)
% OPTIONS(3)	: 	critere d'arret :tolerance sur f (1e-4 par defaut)
% OPTIONS(5)	: 	strategie: 
%              0: GPA, gradient a pas adaptatif
%              1: GPAV, GPA+correction de Vignes
%              2: GPAB, GPA+correction bissectrice
%              3: GPC, gradient pseudo-conjugue a la Polak-Ribiere (par defaut)
%              Avant chaque correction, un test d'angle est effectue
%              pour determiner si la direction corrigee descend.
% OPTIONS(6)	: 	Test d'arret utilise sur f:
%              0: norme initiale sur f
%              1: norme infinie sur f
%              2: norme 2 sur f
% OPTIONS(8)	: 	valeur finale de f
% OPTIONS(9)	: 	verification initiale du gradient si 1
% OPTIONS(10)	: 	nombre d'evaluation de FUN
% OPTIONS(11)	: 	nombre d'evaluation de grad(FUN)
% OPTIONS(14)	: 	nombre maxi d'iterations de l'algorithme
% OPTIONS(15)	: 	pas minimum ( ancien mu_eps 1e-18) (gpavXX.m)
%               	amplitude de la perturbation       (gradchk.m)
% OPTIONS(18)	: 	pas initial de l'algorithme (1e-5 par defaut) 
% OPTIONS(19)	: 	si existe et differente de 0, alors sauvegarde du x 
%                 courant dans gpav.mat toutes les OPTIONS(19) evaluations 
%                 du gradient.
% OPTIONS(20)	:  Les parametres du critere et du gradient differents si >0;
%              OPTIONS(20) : nombres de parametres du critere P1,...,Pn,
%              les parametres Pn+1,...,Pq restant etant ceux du gradient.
%              Par consequent, si un parametre est commun au critere et 
%              au gradient, il faut le passer 2 fois. Dans les 2 cas, le 
%              premier argument doit toujours etre la variable de 
%              minimisation 'x'.
%
% remarque  : syntaxe identique a fminu si moins de 18 options
% --------    options(>18) inexistantes dans les routines de l'opt. toolbox
%
% remarque  : Si le mu est toujours diminue il faut reduire OPTIONS(15)
% --------        (c est une question d ordre de grandeur du critere)
%



function  options = goptions(a)                      

options = [0 1e-4 1e-4 1e-6 3 0 0 0 0 0 0 0 0 0 1e-18 1e-8 0.1 0 ];

return;
