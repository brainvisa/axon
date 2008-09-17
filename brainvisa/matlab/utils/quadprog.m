function x = quadprog(A, b, C, d, x0)
% forme d'appel : x = quadprog(A,b, C, d, x0);
% Resolution d'un probleme de << programmation quadratique >>:
% optimise le critere J(x) = x'Ax -2x'b, Cx <= d
% A matrice sumetrique > 0, b vecteur quelconque,
% C, d definissent les contraintes
% x0 valeur initiale pour l'algo iteratif
% Attention !!! l'algo peut admettre comme point fixe
% des points x tels que Cx=d
% Algorithme iteratif trouve dans le bouquin de Walter & Pronzato
% qui fait lui meme reference a Poliak. Doit converger
% en un nombre fini d'iterations (Poliak ne cite pas de
% borne sup sur le nombre d'iterations)


% on verifie que A,b,C et d sont corrects
if (size(A,1) ~= size(A,2))
  disp('Erreur controler dimensions de A')
  return
else
  b = b(:);
  x0 = x0(:);
  n = size(A,1);
  if (length(b) ~= n | length(x0) ~= n | size(C,2) ~= n)
	 disp('Erreur controler dimensions de b, C ou x0')
	 return
  else
	 d = d(:);
	 m = size(C,1);
	 if length(d) ~= m,
		disp('Erreur controler dimensions de d')
		return
	 end
  end
end

d0 = C*x0;
if any(d0 > d)
  disp('Erreur ! x0 doit satisfaire les contraintes')
end

I = (d0 == d);
iter = 0;
fin = 0;

while ~fin,
  x_prec = x0;
  I_prec = I;
  Ib = ~I;
  fIb = find(Ib);
  fI = find(I);
  iter = iter+1;
  nca = length(find(I));% nombre de contraintes actives
  Ac = [A C(I,:)'; C(I,:) zeros(nca)];
  bc = [b; d(I)];
  xc = Ac\bc;
  xp = xc(1:n);
  if (nca ~= 0)
	 lbd = xc(n+1:length(xc));
  end
  dp = C*xp;
  if any(dp(Ib) > d(Ib))
%	 q = Ib & (dp ~= d0)& (dp > d);
	 q = Ib & (dp > d);
	 fq = find(q);
	 alpha=ones(m,1);
	 alpha(fq) = (d(q)- d0(q))./(dp(q)-d0(q));
%	 qq = alpha < 0 || alpha > 1
	 [alphaopt iopt]= min(alpha);
	 x0 = alphaopt*xp + (1 -alphaopt)*x0;
	 Ib(iopt)=zeros(length(iopt),1);
	 I = ~Ib;
  else
	 x0 = xp;
	 % Contraintes satisfaites
	 if any(lbd < 0),
		I = zeros(m,1);
		I(fI(find(lbd>0))) = ones(length(find(lbd>0)),1);
	 else
		fin = 1;
		disp(sprintf('Nombre d''iteration requis : %d', iter))
	 end
  end
  d0 = C*x0;
  if (x0 == x_prec & all(I == I_prec))
	 disp('Algorithme bloque sur un point fixe')
	 fin = 1;
  end
  if iter > 1e2,
	 fin=1;
	 disp('Nombre d''iteration max depasse');
  end
end


		

x=x0;