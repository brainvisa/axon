%
% Cette fonction permet d'obtenir une version sous-echantillonnee
% d'une matrice contenue dans un fichier gpi
% Syntaxe : ssech(name_in, name_out, txl, txc)


function ssech(name_in, name_out, txl, txc)

while isempty(name_out),  
   name_out = input('Nom du fichier =>','s');  
end

eval(['load ', name_in])
Matemp = Mat(1:txl:Taille(1),1:txc:Taille(2));
Te(1)=txl*Te(1);
Te(2)=txc*Te(2);
Taille = size(Matemp)';
clear Mat
Mat=Matemp;
clear Matemp

% remplissage de la variable Texte
Texte = setstr(' '*ones(5,80));
ligne = ['Fichier cree a partir du fichier ', name_in, '.mat'];
Texte(1,1:min(80,length(ligne)))=ligne(1:min(80,length(ligne)));
ligne = ['dont on a extrait les lignes 1:', num2str(txl), ':',  num2str(Taille(1)), ' et les colonnes 1:', num2str(txc), ':', num2str(Taille(2))];
Texte(2,1:min(80,length(ligne)))=ligne(1:min(80,length(ligne)));

if ((exist('Type') == 1) & (exist('Taille') == 1) & (exist('Mat') == 1)),
  if Type(2) == 'C',
    if Taille' == size(Mat),
      eval(['save ', name_out,' Type Date Taille Te Torg Texte Mat']);
    else
      disp('Erreur : ''Taille'' et dimensions reelles de ''Mat'' incompatibles')
    end
  else
    disp('Erreur : ''Type'' incompatible avec un fichier continu')
  end
else
  disp('Erreur : ''Type'', ''Taille'' ou ''Mat'' inexistant')
end
clear

