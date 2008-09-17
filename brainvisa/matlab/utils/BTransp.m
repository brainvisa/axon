% BTransp.m 				Auteur : Gio, JI
%					Date : 29 mai 1996
%
% Block transposition 
%
% Sert a travailler sur une matrice block diagonale de facon economique.
% Les elements block diagonaux (Y1, Y2, Y3...) sont collectionnes dans en
% colonnes. Ca renvoit la transposee de la matrice block diagonale, rangee
% de la meme facon. C est a dire : 
%
% 
%                Y1                 Y1 t   
% Tu lui donnes  Y2  et ca te rend  Y2 t   
%                Y3                 Y3 t 
%                Y4                 Y4 t 
% 
%
% Bien sur il faut preciser un certain parametre (sans ca il y a ambiguite
% sur la definition des blocks). Il faut donner K le nombre de ligne de
% chaque block.
%
%


function Mat = BTransp(Mat,K)


% Un premier transpose, c est deja ca de fait
	Mat = Mat';


% Recuperation de tailles
	[N M] = size(Mat);


% Teste coherence de l affaire
	if rem(M,K) ~=0 
		disp('Ca colle pas dans les tailles')
		Mat = Mat';
		return
	end

% Defini le nombre de block
	Nbre = M/K;


% Premiere toutouille d indice 
% (qui forme la premiere colonne de la matrice d indice finale ie IndTot)
	IndV  = (1:N)';
	IndH = 0:K*N:(Nbre-1)*K*N;


	IndTot = IndV(:,ones(Nbre,1))+IndH(ones(N,1),:);
	IndTot = IndTot(:);


% Seconde toutouille 
% (qui permet de generer la dimension horizontale de la matrice d indice finale
	IndNewH = 0:N:(K-1)*N;

	IndFinal = IndTot(:,ones(1,K))+IndNewH(ones(N*Nbre,1),:);


% Finalement 
	Mat = Mat(IndFinal);
	Mat = reshape(Mat,Nbre*N,K);

