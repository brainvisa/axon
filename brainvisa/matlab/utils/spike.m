function [xo, yo] = spike(x, y, p)
% spike.m         Plot en mode impulsionnel
% SPIKE	spike graph.
%
% Syntax: [XX, YY] = spike(X, Y, p)
%
% SPIKE(Y, p) draws a spike graph of the elements of vector Y.
% SPIKE(X, Y, p) draws a spike graph of the elements in vector Y at
% the locations specified in X. The optional 'p' is similar to 
% colour, line or point types used for PLOT.
% [XX, YY] = SPIKE(X, Y) does not draw a graph, but returns vectors
% X and Y such that PLOT(XX, YY) is the spike chart.
% See also BAR, STAIRS and HIST.


% J ai du enlever un "end". Gio le 20-09-97               
n = length(x);
if nargin == 1
	y = x;
	x = 1:n;
end
if (nargin == 2) & isstr(y)
	p = y;
	y = x;
	x = 1:n;
end
x = x(:);
y = y(:);
x = [x x x]';
x = x(:);
n = length(y);
y = [zeros(n,1) y zeros(n,1)]';
y = y(:);

%end   % Enleve par Gio le 20-09-97

if nargout == 0
    if exist('p') == 1
	plot(x, y, p)
	axy = axis; axis;
	hold on; plot([axy(1) axy(2)], [0 0], p); hold off;
    else
	plot(x, y)
	axy = axis; axis;
	hold on; plot([axy(1) axy(2)], [0 0]); hold off;
    end
else
	xo = x;
	yo = y;
end
