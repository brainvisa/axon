function B = centre(A)
% Chaque colonne de B est la version centree de la colonne
% correspondante de A

if min(size(A))==1
  B = A - mean(A);
else
  m = mean(A);
  B = A - m(ones(size(A,1),1),:);
end
