function chaine2 = strsubst(chaine1,maillon1,maillon2)
% strsubst.m	substitue la chaine 'maillon2' a la chaine 'maillon1'
%		dans 'chaine1'.
%~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
% chaine2 = strsubst(chaine1,maillon1,maillon2)
%
% Auteur : J. Idier				Date : 09/96
%
% Voir aussi findstr et strcut
%~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

ind = findstr(chaine1,maillon1);
ind = [ind length(chaine1)+1];
L1 = length(maillon1);
L2 = length(maillon2);
chaine2 = chaine1(1:ind(1)-1);
for n=1:length(ind)-1,
  chaine2 = [chaine2 maillon2 chaine1(ind(n)+L1:ind(n+1)-1)];
end

% 2 variantes : une  utilisant findstr (Matlab), une recursive
% utilisant str1find (Cmex JI)

% Version Cmex
%k = 1;
%chaine2 = chaine1;
%while(k>0)
%  N = length(chaine2);
%  [k,l] = str1find(chaine2,maillon1);
%  if(k>0)
%    chaine2 = [chaine2(1:k-1) maillon2 chaine2(l+1:N)];
%  end
%end
