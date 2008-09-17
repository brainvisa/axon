% som.m 			Auteur : Gio
%				Date : juin 1996
%
% Comme sum, mais n effectue pas la somme si on envoie un vecteur ligne.
%
%


function Mat = som(Mat)


if size(Mat,1)~=1

	Mat = sum(Mat);

end
