% getglassy.m   Renvoie la graine dont le numero est compris entre 1 et 51 !!!! 
%Forme d'appel : dseed = getglassy(num);
% Renvoie la graine dont le numero est 'num'
%
%	num doit etre un entier compris entre 1 et 51
%
%
function  dseed = getglassy(num)

if(num > 51 | num < 1)
   disp('numero de graine ramene a 1')
   num = 1;
end

load glassy
dseed = glassy(floor(num));
