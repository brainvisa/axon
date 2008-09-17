function [X, Y] = grille(x,y)

% Genere la grille decrite par le vecteur d'abscisse x
% et le vecteur d'ordonnee y

x = x(:); y = y(:);
M = length(x); N = length(y);
X = [x x; x(ones(N,1)) x(M(ones(N,1)))]';
Y = [y(ones(M,1)) y(N(ones(M,1))); y y]';

if ~nargout
  plot(X,Y,'k:')
end
