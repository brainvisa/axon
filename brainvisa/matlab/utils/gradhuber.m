function g = gradhuber(f,t)
% Gradient de la fonction de regularisation de Huber
% definie dans seismic :
% si t>0
% gradhuber(f,t)  = sign(f)   si abs(f)>=t
%             		= f/t 		sinon
%
% Si t<0
% gradhuber(f,-t) = 2*t*sign(f)	si abs(f)>=t
%             = 2*f           sinon
%~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
% P. CIUCIU, le 07/02/00
% FORMAT D'APPEL : g = gradhuber(f,t)
%~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

g = sign(f);
apprf=abs(f);
if(t>0)
  ind = find(apprf<t);
  g(ind) = f(ind)/t;
elseif(t<0)
  t = -t;
  ind = find(apprf<t);
  g =2*t*g;
  g(ind)=2*f(ind);
end
