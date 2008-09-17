function [m,i,j] = min2(mat)
% min2.m        minimum et indices correspondants pour une matrice
% Minimum et ses arguments pour une matrice
[M,I] = min(mat);
[m,j] = min(M);
i = I(j);
%end
