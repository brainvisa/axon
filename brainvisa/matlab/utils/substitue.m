% substitue.m      substitution de chaines de caractere 
% Forme d'appel : substitue(fic1,ch1,ch2,fic2)
% substitue la chaine 'ch2' a la chaine 'ch1' dans 'fic1' le resultat est
% stocke dans 'fic2'
function substitue(fic1,ch1,ch2,fic2)

texte = loadb(fic1);
if ~isempty(texte)
  lt = length(texte);
  x = findstr(texte,ch1);	% Findstr remplace parse, obsolete
  if ~isempty(x)
    Lx = length(x);
    disp(['Nombre d''occurences : ', num2str(Lx)])
    L1 = length(ch1);
    L2 = length(ch2);
    dL = L2 - L1;
    X = zeros(Lx,L1);
    l1 = 0:L1-1;
    X = x(:,ones(L1,1)) + l1(ones(Lx,1),:);
    X = X(:);
    ind = ones(lt,1);
    ind(X) = zeros(length(X),1);
    xx = find(ind == 1);

    texte2 = zeros(length(texte)+Lx*dL,1);
    lt2 = size(texte2);
    decal = [0 ; dL(ones(Lx-1,1))];	% Bonne instruction mais Bug Matlab
    decal = cumsum(decal);
    y = x + decal;
    Y = zeros(Lx,L2);
    for l2 = 1:L2
        Y(:,l2) = y + (l2-1);
    end;
    Y=Y(:);
    ind2 = ones(lt2,1);
    ind2(Y) = zeros(length(Y),1);
    yy = find(ind2 == 1);

    texte2(yy) = texte(xx);

    for k=1:Lx,
        texte2(y(k):y(k)+L2 -1)=ch2;
    end
    texte2=abs(texte2);
    saveb(texte2,fic2)
  end
end                
           
