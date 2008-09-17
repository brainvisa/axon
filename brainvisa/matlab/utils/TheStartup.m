% FICHIER A NE PAS EFFACER : INDISPENSABLE AU RESTART
%
% Script de rafraichissement de Matlab
% Deuxieme partie : Recuperation des donnees sauvees par restart
%
% H. Carfantan
% 17 janvier 1995

  disp('Rafraichissement en cours')

% Recuperation des donnees
  load TheSession.mat

% Actualisation du path
  path(ThePath) 
  eval(['cd ' TheDirectory])

% Effacement des variables intermediaires
  clear TheDirectory ThePath

% Effacement des fichiers intermediaires
  if exist('TheStartup.bak')==2
     !mv TheStartup.bak startup.m
  else
     !rm startup.m
  end
  !rm TheSession.mat

% Affichage des graphiques
  exist('TheNumFig');
  for TheFig = 1:TheNumFig,
      TheFile = ['tmp' num2str(TheFig)];
      eval(TheFile);
      eval(['!rm ' TheFile '.m ' TheFile '.mat'])
  end
  clear TheFig TheNumFig TheFile

% Affichage des variables
  who
  disp('Rafraichissement execute')

