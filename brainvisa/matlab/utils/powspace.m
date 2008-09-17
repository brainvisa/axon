function v = powspace(x1,x2,P,N)
% powspace(x1,x2,P,N) imite linspace(x1,x2,N) pour generer
% N points repartis suivant x^P.
%	Auteur :	J. Idier	Date : 03/94
if P<0
  v = linspace(1,0,N+1);
%  v = v(1:N).^P - 1;
  v = exp(log(v(1:N)).*P) - 1;
  v = x1 + (x2-x1)*v/v(N);
else
%  v = x1 + (x2-x1)*linspace(0,1,N).^P;
  v = linspace(0,1,N);
  v(2:N) = x1 + (x2-x1)*exp(log(v(2:N)).*P);
  v(1) = x1;
end
