function f = fnum2str(x, prec)
% Renvoie le format associe a NUM2STR, cad que
% fprintf(fnum2str(x, prec),x) est equivalent a num2str(x, prec)

if isstr(x)
  f = x;
else
  if (nargin == 1)
    f = '%.4g';
  else
    f = ['%.' num2str(prec) 'g'];
  end
end
return
