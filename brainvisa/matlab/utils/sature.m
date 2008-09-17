function y = sature(x, seuilmin, seuilmax)
% forme d'appel :  y = sature(x, seuilmin, seuilmax)
% Seuille une matrice  x
%

[M,N]=size(x);
x = x(:);
y=x;
a=find(x>seuilmax);
if(~isempty(a)),
  y(a)=seuilmax(ones(length(a),1));
end
a=find(x<seuilmin);
if(~isempty(a)),
  y(a)=seuilmin(ones(length(a),1));
end
y = reshape(y,M,N);