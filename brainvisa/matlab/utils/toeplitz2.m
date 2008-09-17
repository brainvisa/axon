% Forme d'appel :
%    T = toeplitz2(R);
% Donne la matrice Toeplitz/bloc-Toeplitz (M*N)x(M*N)
% equivalente a une matrice d'autocorrelation
% R (2*M-1)x(2*N-1) donnee
% Si R = [r(1-M,1-N) ...     r(1-M,N-1) ]
%             .
%         r(M-1, 1-N) ...     r(M-1,N-1)  ]
%
% toeplitz2(R) = 
%           T(0)  T(-1) T(-2) .... T(2-N) T(1-N)
%           T(1)  T(0)  T(2) .... T(N-2) T(N-1)
%           T(2)                        .
%            .                          .
%            .                          . 
%            .                          .
%           T(N-1) ..................... T(1)  
%
% Ou T(j) = matrice toeplitz formee avec
%  r(:,j) eme colonne de R de taille 2M-1
%
% pour voir comment s'ordonnent les valeurs
% faire toeplitz2(reshape((-12:12),5,5))
% 
function T = toeplitz2(R),


M=ceil(size(R,1)/2);
N=ceil(size(R,2)/2);
k = (1:M)';
l = (1:N);
o = ones(M,1);
p = ones(1,N);
k=k(:,p);k=k(:);
l=l(o,:);l=l(:);
O = ones(1,N*M);
K = k(:,O) - k(:,O)'+M;
L = l(:,O) - l(:,O)'+N;
I = (L-1)*(2*M-1) + K;
%R=R(:);
T = reshape(R(I),M*N,M*N);

