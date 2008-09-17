function apprf = huber(f,t)

% huber(f,t)  = abs(f)         si abs(f)>=t
%             = .5/t*f.^2+.5*t sinon
%
% 2eme param negatif => autre convention :
% huber(f,-t) = 2*t*abs(f)-t^2 si abs(f)>t
%             = f.^2           sinon
%~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
% J.Idier 12/99
%~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

apprf = abs(f);
if(t>0)
  ind = find(apprf<t);
  apprf(ind) = (.5/t)*f(ind).^2 + .5*t;
elseif(t<0)
  t = -t;
  ind = find(apprf<t);
  apprf = 2*t*apprf-t^2;
  apprf(ind) = f(ind).^2;
end
