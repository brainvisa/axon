function fx =banana(x);
% banana.m        fonction banana utilise pour les tests d'optimisation
%  renvoie la valeur de la fonction banana suivante dont le minimum global
%  se trouve en x=y=1
%
%      f(x,y) = 100*(y-x^2)^2 +(1-x)^2 
%
%     auteur    Stef le 6decembre 94 , pompe sur optdemo.m
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
fx=100*(x(2)-x(1)^2)^2+(1-x(1))^2;
