function comet(x, y, p, colorbody, colortail)
%COMET	New version of Comet plot. With customizable colors.
%	COMET(Y) displays an animated comet plot of the vector Y.
%	COMET(X,Y) displays an animated comet plot of vector Y vs. X.
%	COMET(X,Y,p) uses a comet of length p*length(Y).  Default is p = 0.10.
%       COMET(X,Y,p,colorbody,colortail) customize the color
%	COMET, by itself, is self demonstrating.
%	Example:
%	    t = -pi:pi/200:pi;
%	    comet(t,tan(sin(t))-sin(tan(t)))
%	See also QUAKEDEMO, COMET3.

%	Charles R. Denham, MathWorks, 1989.
%	Revised 2-9-92, LS and DTP; 8-18-92, 11-30-92 CBM.
%       Revised 3-2-95, STEF & GPI production's
%	Copyright (c) 1984-94 by The MathWorks, Inc.

if nargin == 0,
   x = -pi:pi/200:pi;
   y = tan(sin(x))-sin(tan(x));
   p = 0.1;
else
  if nargin < 2, y = x; x = 1:length(y); end
  if nargin < 3, p = 0.10; end
  if nargin < 4, colorbody = 'y';colortail='k';end;
  if nargin < 5, colortail='k';end;
end
axis_state = axis('state');

if (axis_state(1:4) == 'auto')
    axis([min(x(isfinite(x))) max(x(isfinite(x))) min(y(isfinite(y))) max(y(isfinite(y)))])
end;
% Cyan circle head, yellow line body, and magenta line tail.
head = line('color','c','linestyle','o','erase','xor','xdata',x(1),'ydata',y(1));
body = line('color',colorbody,'linestyle','-','erase','none','xdata',[],'ydata',[]);
tail = line('color',colortail,'linestyle','-','erase','none','xdata',[],'ydata',[]);

m = length(x);
k = round(p*m);

% Grow the body
for i = 2:k+1
   j = i-1:i;
   set(head,'xdata',x(i),'ydata',y(i))
   set(body,'xdata',x(j),'ydata',y(j))
   drawnow
end

% Primary loop
for i = k+2:m
   j = i-1:i;
   set(head,'xdata',x(i),'ydata',y(i))
   set(body,'xdata',x(j),'ydata',y(j))
   set(tail,'xdata',x(j-k),'ydata',y(j-k))
   drawnow
end

% Clean up the tail
for i = m+1:m+k
   j = i-1:i;
   set(tail,'xdata',x(j-k),'ydata',y(j-k))
   drawnow
end
