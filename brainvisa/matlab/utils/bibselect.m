function bibselect(bib,ydeb,yfin,coauteur)
% bibselect.m        filtrage de la base gpipubli.m
%
% Auteur : J. Idier	Date : 06/97
%~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
%      Cette fonction permet de filtrer gpipubli.bib pour un coauteur ou pour
%	tout le GPI, en exploitant lssref pour faire le tri.
%	exemple : bibselect('select.bib',1994,2050,'Nguyen')
%~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
% (bib): Nom du fichier .bib a fabriquer. 
% (ydeb): Annee de debut.
% (yfin): Annee de fin.
% (coauteur): Nom du coauteur concerne (optionnel).
%~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

ch = loadb('/home/seismic/TeX/biblio/gpipubli.bib')';
ch1 = ['%{\bf Publications dans des revues avec comit\''e de lecture}' 10 10];
ch2 = ['%{\bf Articles dans des actes de congr\`es \''edit\''es ou publi\''es}' 10 10];
ch3 = ['%{\bf Publications complŠ\`etes lors de colloques avec actes}' 10 10];
ch4 = ['%{\bf Colloques sans actes}' 10 10];
ch5 = ['%{\bf Rapports internes}' 10 10];
ch6 = ['%{\bf Rapports de contrat}' 10 10];
ch7 = ['%{\bf Rapports de stage}' 10 10];
ch8 = ['%{\bf Theses}' 10 10];

L = length(ch);
II = [find(ch=='@') L+1];
for i=1:length(II)-1,
  fiche = ch(II(i):II(i+1)-1);
%  fprintf('%s\n',fiche);

% Extraction du code et de l'annee dans lssref (merci str1find)
  [k,l,k1,l1,k2,l2,k3,l3] = str1find(fiche,['lssref' 302 '{' 302 '.' 302 '.']);
  if k3>0
    year = sscanf(sprintf('%s',fiche(k3:l3)),'%d');
    if (year>75)
      year = year + 1900;	% A revoir apres 2075...
    else
      year = year + 2000;
    end  
  end  

if exist('coauteur') ~= 1
  coauteur = [];
end
  
% Extraction de l'auteur dans author (merci str1find)
k4 = 1;
if isempty(coauteur) ~= 1
  [k,l,k1,l1,k4,l4] = str1find(fiche,['author' 302 coauteur 302 '}']);
end

  code = [];
  if (k2>0)&(k4>0)&(year>=ydeb)&(year<=yfin)
    code = fiche(k2:l2);
  end  
  if strcmp(code,'A')
    ch1 = [ch1 fiche];
  elseif strcmp(code,'L5')
    ch2 = [ch2 fiche];
  elseif strcmp(code,'C')
    ch3 = [ch3 fiche];
  elseif strcmp(code,'CS')
    ch4 = [ch4 fiche];
  elseif strcmp(code,'RI')
    ch5 = [ch5 fiche];
  elseif strcmp(code,'RC')
    ch6 = [ch6 fiche];
  elseif strcmp(code,'RS')
    ch7 = [ch7 fiche];
  elseif strcmp(code,'T')
    ch8 = [ch8 fiche];
  end  
end

saveb([ch1 ch2 ch3 ch4 ch5 ch6 ch7 ch8], bib)
end
