% DistL1L2.m 					Auteur : JFG,
%						Date : mi-novembre 1995
%
% Calcul de distances L1 et L2 entre spectres
%
% Tu lui donnes deux series de spectres bien ranges en colonnes
% Ca te renvoie : les deux suites de distance bien rangees sur une ligne
%                 et les deux distances moyennes
%
% Syntaxe [L1, L2, L1Moy, L2Moy] = DistL1L2(S, Ref)
%
% Les spectres doivent etre en colonnes
%


function [L1, L2, L1Moy, L2Moy, L1pc, L2pc] = DistL1L2(S, Ref)

if size(S,1)~=size(Ref,1) | size(S,2)~=size(Ref,2)
	error('Les spectres n''ont pas le meme taille');
end


L1 = mean( abs(Ref-S) );   
L2 = sqrt( mean( (Ref-S).^2) );

L1Moy = mean(L1) ;
L2Moy = mean(L2) ;

%L1pc = 100 * sum( abs(Ref(:)-S(:)) ) / sum(Ref(:));
%L2pc = 100 * sqrt(sum((Ref(:)-S(:)).^2))/sqrt(sum(Ref(:).^2));

L1pc = 100 * sum2( abs(Ref-S) ) / sum2(Ref);
L2pc = 100 * sqrt(sum2((Ref-S).^2)) /sqrt(sum2(Ref.^2));
