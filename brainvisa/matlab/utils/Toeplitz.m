function t = Toeplitz(c,r)
%	TOEPLITZ(C,R) is a non-symmetric Toeplitz matrix having C as its
%	first column and R as its first row.   TOEPLITZ(C) is a symmetric
%	(or Hermitian) Toeplitz matrix.  See also HANKEL.
% 	Auteur : J. Idier		Version 1.0	Date : 02/96
t = [];
if nargin == 1
	[m,n] = size(c);
	if n == 1
		r = c';
	else
		r = c;
		c = c';
		if n
			c(1) = r(1);
		end
	end
%else
%	if all(size(r)&size(c))
%		if r(1) ~= c(1)
%			disp(' ')
%			disp('Column wins diagonal conflict.')
%		end
%	end
end
n = max(size(r));
m = max(size(c));
c = c(:);		% Make sure C is a column vector
r = r(:).';		% Make sure R is a row vector
t = ones(m,n);		% Allocate T
k = min(m,n);

for i=1:k                   	 % Fill in the matrix
	t(i,i:n) = r(1:n-i+1); % ith row, upper triangle
	t(i:m,i) = c(1:m-i+1); % ith col, lower triangle
end
