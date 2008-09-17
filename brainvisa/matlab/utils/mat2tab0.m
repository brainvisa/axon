function mat2tab0(A,sformat,nom_fichier,B)
% mat2tab0.m	Conversion d'une matrice au format \tabular LaTeX, sans
%		le filtrage utilisant \V et \e pour la version VF
%~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
% mat2tab0(A,sformat,nom_fichier,B)
%
% Auteur F. Champagnat le 6/9/96	Jejeifie par J. Idier le 16/9/96
%~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
% Le resultat est sauve dans le fichier 'nom_fichier'
% Si nom_fichier = 'stdout' ou non specifie => sortie standard.
% 'sformat' est une chaine au format fprintf ou une suite
% de telles chaines (separees par des <RETURN> = 10).
% Dans le dernier cas, la matrice B est de la taille de A et contient
% pour chaque entree le numero de la chaine a utiliser. Le numero
% zero utilise le format num2str ; c'est aussi le format par defaut.
%

R = 10;				% <RETURN>
[m,n]=size(A);
if exist('nom_fichier')~=1
  nom_fichier = 'stdout';
end
if strcmp(nom_fichier,'stdout'),
  fid = 1;
else
[fid, message] = fopen(nom_fichier, 'wt');
end
%
if(fid == -1)
  disp(message)
else
  ch = ['\\begin{tabular}' sprintf('{|%s}',('c|')'*ones(1,n)) R '\\hline' R];
  fin=['&' 10 '\\\\\\\\\n\\\\hline\n'];	% Grosse astuce a la Jeje
  label = 'diouxXfeEgGcs';		% Non, c'est pas n'importe quoi
%  
  for k=1:m, for l=1:n,
    if exist('sformat')~=1	% pas de format -> num2str
      sf = fnum2str(A(k,l));
    else
      if exist('B')~=1	% Un seul format -> fprintf
        sf = sformat;
      else			% Format variable
        if B(k,l)==0
          sf = fnum2str(A(k,l));
        else
          sf = strcut(sformat,B(k,l));
        end
      end
    end
    ch = [ch sf sprintf(strcut(fin,1+(l==n)))];
  end; end
  
  ch =[ch '\end{tabular}' R];
% Localisation de chaque nombre et isolement entre $ $ 
  ch = strsubst(ch,'%','$%'); 	% A gauche, facile
  ind = find(ch=='$');		% A droite, plus subtil
  ind = [ind length(ch)+1];
  for i=length(ind)-1:-1:1,
    sf = ch(ind(i):ind(i+1)-1);
    ind2=[];
    for j=1:length(label)
      ind2 = [ind2 find(sf==label(j))];
    end
    inf = min(ind2);
    sf = [sf(1:inf) '$'];
    ch = [ch(1:ind(i)-1) sf ch(ind(i)+inf:length(ch))];
  end
  fprintf(fid,ch,A);
end
%
if ~strcmp(nom_fichier,'stdout'),
  status = fclose(fid);
  if(status ~= 0)
    [message, errnum] = ferror(fid, 'clear');
    disp(message)
  else
    disp(['Sauvegarde dans fichier ', nom_fichier, ' : O.K.'])
  end
end
return
