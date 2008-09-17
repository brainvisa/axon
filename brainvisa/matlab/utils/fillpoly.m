function A = fillpoly(x,y,M,N,val)

% function A = fillpoly(x,y,M,N,val)
% Genere une matrice nulle de taille (M,N) sauf une zone polygonale
% CONVEXE valant val, de sommets decrits par les vecteurs x, y.
% (pour les polygones non convexes, assembler plusieurs polygones
% convexes par OU logique).
%~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
% J.Idier 03/98
%~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

if exist('val')~=1
  val = 1;
end

A = ones(M,N);
mm = (1:M)';
om = ones(M,1);
nn = 1:N;
on = ones(1,N);
L = length(x);
for l = 1:L
  l1 = rem(l,L)+1;
  l2 = rem(l+1,L)+1;
  a = (x(l1)-x(l))/(y(l1)-y(l));
  signok = sign((x(l2)-x(l))-a*(y(l2)-y(l)));
  A = A&(sign(mm(:,on)-x(l1)-a*(nn(om,:)-y(l1)))==signok);
end
if val ~= 1
  Z(Z) = ampl(Z(Z)+0);
end  
