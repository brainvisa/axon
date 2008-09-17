function [y,sigmab2]=adgnoise(y,snr)

% adgnoise.m       Add gaussian white noise to observation
%         
% [yb,sigmab2]  = adgnoise(y,SNRdb)
% Ce programme ajoute un bruit blanc gaussien  de rapport signal 
%  a bruit  SNRdb aux donnees Y
% 
%  Auteur      STEF        10 decembre 94 v1.0
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% 

sigmab2 = 10^(-snr/10)*mean(y(:).*y(:));
sigmab = sqrt(sigmab2);
y = y + randn(size(y))*sigmab;

return
