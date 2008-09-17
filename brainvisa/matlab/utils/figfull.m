function figfull(nb)

% function figfull(nb)
% Appelle figure en diminuant les marges.
%~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
% J.Idier 06/98
%~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

clf;
axes('position',[.05 .05 .9 .9]);
if exist('nb')~=1
  figure;
else  
  figure(nb);
end
