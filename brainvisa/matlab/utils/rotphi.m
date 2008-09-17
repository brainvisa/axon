function x_r = rotphi2(x, phi)
% rotphi.m      rotation de phase 'une ondelette MA       
% Cette fonction permet d'appliquer une rotation de
% phase a une ondelette representee sous forme MA.
%
% La forme d'appel est la suivante:
%
% x_r = rotphi2(x, phi)
%
% x:      Nom de la variable MATLAB (vecteur colonne)
%         contenant l'ondelette discretisee
% phi:    Angle de rotation, en degres.
%

% Definition de l'unite des imaginaires
j = sqrt(-1);

% TF du signal x, et dimensions de x et de sa TF
x=x(:);
x_hat = fft(x);
N = length(x);

p = floor(N / 2);

% Calcul de l'angle de rotation en radians, et
% des facteurs permettant d'effectuer la rotation
phi_r = pi * phi / 180;
fmoins = exp(-j * phi_r);
fplus = exp(j * phi_r);

% Rotation de phase : on ne touche pas a la phase
% de la composante continue, ni celle de la frequence 1/2
% Si N est pair
if(N==2*p)
   x_r_hat = [x_hat(1); fmoins*x_hat(2:p);
               x_hat(p+1); fplus*x_hat(p+2:N)];
else
   x_r_hat = [x_hat(1); fmoins*x_hat(2:p+1);
               fplus*x_hat(p+2:N)];
end


% Retour dans le domaine temporel, et troncature
% a la dimension de x
x_r = ifft(x_r_hat);
x_r = real(x_r);

