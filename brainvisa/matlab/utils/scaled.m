function B = scaled(A)
% Chaque colonne de B est proportionnelle a la colonne
% correspondante de A, mais de somme egale a 1

if min(size(A))==1
  B = A/mean(A);
else
  m = mean(A);
  B = A./m(ones(size(A,1),1),:);
end
