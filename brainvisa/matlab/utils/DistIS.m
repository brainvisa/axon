% DistIS.m 					Auteur : JFG,
%						Date : mi-novembre 1995
%
% Calcul de distances de Itakura Saito entre spectres
%
% Tu lui donnes deux series de spectres bien ranges en colonnes
% Ca te renvoie : la suite des distances bien rangees sur une ligne
%                 et la distance moyenne
%
% Syntaxe [IS ISMoy] = DistIS(S, Ref)
%
% Les spectres doivent etre en colonnes
% Ajout dernier argument le 7/04/2000 par P. CIUCIU pour calcul pourcentage

function [IS, ISMoy,ISpc] = DistIS(S, Ref)



if size(S,1)~=size(Ref,1) | size(S,2)~=size(Ref,2)
	error('Les spectres n''ont pas le meme taille');
end


Rap = S./Ref; 
%Rap = Ref./S; 

IS = mean( Rap - 1 - log(Rap) );

ISMoy = mean(IS);
ISpc = 100 * sum2( Rap - 1 - log(Rap) ) / sum2(Ref);
