% loadbs.m      Load une matrice entiere, VERSION SILENCIEUSE
%   Charge une matrice Matlab a partir d'un fichier en byte (unsigned char)
%   afin d'economiser l'espace disque
%
%	Auteur :	F. Champagnat		Date : 09/93
%			
%	Forme d'appel : A = loadbs(nomfich, m, n) ou A = loadb(nomfich)
%
%			A	: matrice Matlab
%			nomfich : chaine Matlab
%			m	: nombre de lignes
%			n	: nombre de colonnes
%

% Ce programme utilise les fonctions fichier de Matlab 4.0
% Il existe une version pour Matlab 3.5 utilisant un MEX-file

function A = loadbs(nomfich,m,n)

if(~exist(nomfich))
    disp(['''', nomfich, ''' n''existe pas']);
    A=[];
else
    [fid, message] = fopen(nomfich, 'r');
    if(fid == -1)
        disp(message)
    else
        A = fread(fid, inf, 'uchar');
        if(nargin == 3)
            if(length(A) == m*n)
                A = reshape(A, m, n);
            end
        end
        status = fclose(fid);
        if(status ~= 0)
            [message, errnum] = ferror(fid, 'clear');
            disp(message)
%        else
%            disp(['Lecture du fichier ''', nomfich, ''' : O.K.']);
        end
    end
end
