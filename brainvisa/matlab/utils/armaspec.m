% Affiche le module de la reponse en frequence
% d'un ARMA(a,b)
%
%        y(n) = b(1)*x(n) + b(2)*x(n-1) + ... + b(nb+1)*x(n-nb)
%                         - a(2)*y(n-1) - ... - a(na+1)*y(n-na)
%
% Forme d'appel : Hf = armaspec(b, a, N, yscale)
%
% yscale = argument optionnel pour specifier si l'on veut un trace
% en log sur les y
%	yscale = 'log', 'square' ou 'linear'
% H(f) est calcule pour f = 0, 1/N, 2/N, ... 1 - 1/N
%
% |H(f)| est represente sur un axe symetrique [-0.5 0.5]
% mais le vecteur Hf renvoye correspond aux valeurs successives
% f = 0, 1/N, 2/N, ... 1 - 1/N

function Hf = armaspec(b, a, N, yscale),

if (nargin < 4)
yscale = 'linear';
end

a = a(:);
b = b(:);

if(a(1) ~= 1)
   a = a / a(1);
   b = b / a(1);
end

tfa = fft(a, N);
tfb = fft(b, N);
Hf = tfb(:)./tfa(:);
f  = (0:N-1)'/N;
p = floor(N/2);
f(N-p+1:N) = f(N-p+1:N) - 1 ;

if (strcmp(yscale,'square'))
  plot(fftshift(f), abs(fftshift(Hf)).^2)
else
  plot(fftshift(f), abs(fftshift(Hf)))
end
set(gca,'XTick', [-0.5 -0.4 -0.3 -0.2 -0.1 0 0.1 0.2 0.3 0.4 0.5])

if (strcmp(yscale,'log'))
    set(gca,'YScale','log')
end
