function [m,i,j] = max2(mat)
% max2.m         maximum d'une matrice et indices du max
% Maximum (et ses arguments, optionnels) pour une matrice
%

% J ai du enlever le dernier end. Gio le 20-09-97.
%
[M,I] = max(mat);
[m,j] = max(M);
i = I(j);
%end
