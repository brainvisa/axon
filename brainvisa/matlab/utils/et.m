function c = et(a,b)
% et.m     ET logique sur les parties entiere de 2 reels
% et(a,b) est le ET logique de floor(abs(a)) et de floor(abs(b)),
% valable pour des scalaires et des vecteurs.
%
n = min(length(a),length(b));
a = a(:);
b = b(:);
a = a(1:n);
b = b(1:n);
a = floor(abs(a));
b = floor(abs(b));
L = floor(log(max(max(a,b)))/log(2));	% Fournit la plus grande puissance
					% de 2 contenue dans a et b
l = round(exp(log(2)*(0:L);
c = (rem(floor(a*(ones(l)./l)),2).*rem(floor(b*(ones(l)./l)),2))*l';
end
