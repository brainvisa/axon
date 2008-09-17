% FenAR.m 				Auteur : Gio
%					Date : Avril 96
%
% Formation de la matrice des donnees
% et du vecteur donnees pour prediction lineaire
% directe et retrograde
% dans les differentes formes de fenetrage
%
%
% Syntaxe: [s,X] = FenAR(y,p,fen)
%
%
%   Entree: y: vecteur des donnees effectivement observee
%           p: ordre du modele AR
%           fen: fenetrage (voir "code" ci dessus)  
%
%   Sortie: X: matrice des donnees
%           s: vecteur observation
%
%
% Codage du fenetrage : 
% ----------------------
%
% Le parametre fen peut etre de taille 2 ou 4.
%
%
%	1 - s il est de taille 2 : fen = [NbreAv NbreAp]
%		NbreAv et NbreAp fixent le nombre de zero
%		respectivement avant et apres
%		
%	2 - s il est de taille 4 : fen = [NbreAvForw NbreApForw NbreAvBack NbreApBack]
%		* NbreAvForw et NbreApForw fixent le nombre de zero
%		respectivement avant et apres dans la forme forward
%		* NbreAvBack et NbreApBack fixent le nombre de zero
%		respectivement avant et apres dans la forme backward
%%

function [s,X]=FenAR(y,p,fen)

% Constantes
	y = y(:);
	n = length(y);

% Test longueur paramatre de fenetrage
	if length(fen)~=2 & length(fen)~=4
	disp('Le parametre de fenetrage doit etre de taille 2 ou 4')
	%beep(1)
	break
	end

% Teste Ordre < NbreDonnees-1 
	if p >= n
	disp(['L''ordre de l''AR (=' num2str(p) ') ne doit pas exceder le nbre de donnees - 1 (=' num2str(n-1) ')'])
	%beep(1)
	break
	end


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Traitement du cas length(fen)=2 (forme forward seulement)
if length(fen)==2
	
	% Change notation
	NbreAv = fen(1);
	NbreAp = fen(2);

	% Test et verification du nombre de zero
	if NbreAv<0 | NbreAv>p
	disp(['Le nbre de 0 avant (=' num2str(NbreAv) ') doit etre compris entre 0 et p (=' num2str(p) ')'])
	%beep(1)
	break
	end

	if NbreAp<0 | NbreAp>p
	disp(['Le nbre de 0 apres (=' num2str(NbreAp) ' ) doit etre compris entre 0 et p (=' num2str(p) ')'])
	%beep(1)
	break
	end

	% Test pour info  si equivalent a une forme classique (pre, post, ...)
	if NbreAv==0 & NbreAp==0
	%disp('C''est du non fenetre')
	end
	if NbreAv==0 & NbreAp==p
	%disp('C''est du post-fenetre')
	end
	if NbreAv==p & NbreAp==0
	%disp('C''est du pre-fenetre')
	end
	if NbreAv==p & NbreAp==p
	%disp('C''est du pre- et post-fenetre')
	end

	
% Pre et post
	s = [y ; zeros(p,1)];
	X = toeplitz([0 ; y(1:n) ; zeros(p-1,1)],zeros(1,p));

% Extraction en fonction de la forme de demandee
        s = s(p+1-NbreAv:n+NbreAp);
	X = X(p+1-NbreAv:n+NbreAp,:); 


end % de length(fen)==2

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Traitement du cas length(fen)=4 (cad forme forward backward)
%	(fait appel 2 fois an 'FenAR' (recursivite))
% 
if length(fen)==4

	%disp('C''est du Forward-Backward')
	% Les tests sont pas necessaires car ils sont fait dans la recursion

	% Change notation
	NbreAvForw = fen(1);
	NbreApForw = fen(2);
	NbreAvBack = fen(3);
	NbreApBack = fen(4);
	
	[s1 X1] = FenAR(y,p,[NbreAvForw NbreApForw]);
	[s2 X2] = FenAR(conj(flip(y)),p,[NbreAvBack NbreApBack]);
				% C est bien flip et conj 
	
	s = [s1; s2];
	X = [X1; X2];

end % de length(fen)==4

