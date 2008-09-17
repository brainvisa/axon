function f = symediff(A,ordre)

% symediff.m  Similaire diff de Matlab, mais symetrique
% 
% Auteur: Raphael Reposo
% Date: 03-05-95
%
% [x1;...;xn] --> [x1-x2;x2-x3;...;xn-1-xn;xn-x1](xp -xp+1),p=1...M-1
% A l'ordre 2:
% [x1;...;xn] --> [2x1-x2-xn;...;2xn-xn-1-x1]
%
% Format d'appel:
% f=symdiff(x,1) ou symdiff(x,2)
%
%
%


if nargin<2
	ordre=1;
end
s=size(A,1);
if ordre==1
	f=[-diff(A);A(s,:)-A(1,:)];
end
if ordre==2
	d=-diff(A,2);
	f=[2*A(1,:)-A(2,:)-A(s,:);d;2*A(s,:)-A(1,:)-A(s-1,:)];
end
if (ordre~=1)*(ordre~=2)
	error('Le parametre d''ordre ne peut prendre que les valeurs 1 ou 2');
end
