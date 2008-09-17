function dfx =dbanana(x)
% dbanana.m        gradient de  banana utilise pour les tests d'optimisation
%  renvoie la valeur du gradient de  banana fonction dont le minimum global
%  se trouve en x=y=1
%
%      f(x,y) = 100*(y-x^2)^2 +(1-x)^2 
%
%      A utiliser pour tester un gradient par exemple
%     auteur    Stef le 6decembre 94 , pompe sur optdemo.m
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
dfx=[100*(4*x(1)^3-4*x(1)*x(2))+2*x(1)-2; 100*(2*x(2)-2*x(1)^2)];
