% FenAdaptAR.m					Auteur : Gio
%						Date : 22-04-96
%
%
% Routine de construction des matrices de donnees pour 
% analyse AR adaptative.
%
%	Pour les differents fenetrages (entre 0 et P zeros avant et apres)
%	Forme Foward seulement et Forward-Backward
%
% 
%	Syntaxe : 	MatData = FenAdaptAR(Data,P,fen)
%	---------
%
% 	Entree :
%	--------
%		Data :	Matrice des donnees, M signaux de longueur N, en colonnes
%		P :	Ordre du modele
%		fen : 	Type de fenetrage (Voir codage ci-dessous et exemples)
%
%	Sortie :
%	--------
% 		Mat :	Matrice de donnees (Voir exemples ci-dessous)
%
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
%		  respectivement avant et apres dans la forme forward
%		* NbreAvBack et NbreApBack fixent le nombre de zero
%		  respectivement avant et apres dans la forme backward
%
% Remarque :
%-----------
%
%	1- Le cas Forward Backward est traite en faisant appel 
%	   deux fois a cette routines (recursivite)
%
%	2- Dans le cas Forward Backward la matrice renvoyee 
%	   contient d abord tout ce qui correspond a du forward puis 
%	   tout ce qui correspond a du backward
%
%
%	3- Dans toutes les configurations la matrice renvoyee 
%	   est la matrice de la forme d'innovation. Pour obtenir
%	   la forme prediction il suffit de prelever d une part 
%	   la premiere colonne et d autre part les autres.
%
%
% Exemple avec 2 signaux de 4 echantillons :
%
%	Data =
%	
%	     1    10
%	     2    20
%	     3    30
%	     4    40
%
% 	Pour un ordre P=2 et la forme pre fenetree (cad fen=[2 0]), ca donne
%
%
%	M =
%
%	     1     0     0
%	     2     1     0
%	     3     2     1
%	     4     3     2
%	    10     0     0
%	    20    10     0
%	    30    20    10
%	    40    30    20
%
%
%
% 	Pour un ordre P=3 et la forme post fenetree et forwrad backward [0 3 0 3] )
%
%	M =
%	
%	     1     0     0     0
%	     2     1     0     0
%	     3     2     1     0
%	     4     3     2     1
%	    10     0     0     0
%	    20    10     0     0
%	    30    20    10     0
%	    40    30    20    10
%	     4     0     0     0
%	     3     4     0     0
%	     2     3     4     0
%	     1     2     3     4
%	    40     0     0     0
%	    30    40     0     0
%	    20    30    40     0
%	    10    20    30    40
%
%
%



	function MatData = FenAdaptAR(Data,P,fen)



%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Teste coherence et definit constantes

% Nbre de cases distances
	[N M] = size(Data);	

% Teste longueur paramatre de fenetrage
	if length(fen)~=2 & length(fen)~=4
	disp('Le parametre de fenetrage doit etre de taille 2 ou 4')
	%beep(1)
	break
	end

% Teste Ordre < NbreDonnees-1 
	if P >= N
	disp(['L''ordre de l''AR (=' num2str(P) ') ne doit pas exceder le nbre de donnees - 1 (=' num2str(N-1) ')'])
	%beep(1)
	break
	end


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Traitement du cas length(fen)=2 (forme forward seulement)
if length(fen)==2

% Nbre de zeros avant et apres
	ZeAv = fen(1);
	ZeAp = fen(2);

% Test et verification du nombre de zero
	if ZeAv<0 | ZeAv>P
	disp(['Le nbre de 0 avant (=' num2str(ZeAv) ') doit etre compris entre 0 et p (=' num2str(P) ')'])
	%beep(1)
	break
	end

	if ZeAp<0 | ZeAp>P
	disp(['Le nbre de 0 apres (=' num2str(ZeAp) ' ) doit etre compris entre 0 et p (=' num2str(P) ')'])
	%beep(1)
	break
	end

% Test pour info  si equivalent a une forme classique (pre, post, ...)
	%if ZeAv==0 & ZeAp==0
	%disp('C''est du non fenetre')
	%end
	%if ZeAv==0 & ZeAp==P
	%disp('C''est du post-fenetre')
	%end
	%if ZeAv==P & ZeAp==0
	%disp('C''est du pre-fenetre')
	%end
	%if ZeAv==P & ZeAp==P
	%disp('C''est du pre- et post-fenetre')
	%end


% Bourrage de zeros
	Data = [zeros(ZeAv,M) ; Data ; zeros(ZeAp,M)];

% Taille des signaux (incluant les zeros)
	Nnew = size(Data,1);

% Fabrique la matrice d'indices qui va bien
% (Ca construit la matrice de donnees relative au vecteur de donnees : [1 2 3...])
	VectInd = 1:Nnew; 
	MatInd = toeplitz( VectInd(P+1:Nnew) , VectInd(P+1:-1:1) );
	MatInd = MatInd';
	MatInd = MatInd(:);

% Construction de la matrice finale (Tout est la !!!!!)
	MatData = reshape(Data(MatInd,:),P+1,(Nnew-P)*M).';



end % de length(fen)==2



%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Traitement du cas length(fen)=4 (cad forme forward backward)
%	(fait appel 2 fois an 'FenAR' (recursivite))
if length(fen)==4

	%disp('C''est du Forward-Backward')
	
	% Les tests sont pas necessaires car ils sont fait dans la recursion

	% Change notation
	ZeAvForw = fen(1);
	ZeApForw = fen(2);
	ZeAvBack = fen(3);
	ZeApBack = fen(4);
	       
	Mat1 = FenAdaptAR(     Data         ,P,[ZeAvForw ZeApForw]);
	Mat2 = FenAdaptAR(conj(flipud(Data)),P,[ZeAvBack ZeApBack]); % C est bien flip et conj 
	
	MatData = [Mat1; Mat2];

end % de length(fen)==4

