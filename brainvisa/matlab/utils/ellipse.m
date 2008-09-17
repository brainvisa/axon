function Z = ellipse(lx,ly,cx,cy,ax,ay,val);
% Z = val a l'interieur de l'ellipse de centre (cx,cy) et
% d'axes de longueur (ax,ay) dans une matrice de taille (lx,ly)
% Par defaut, (cx,cy) = (lx+1,ly+1)/2, (ax,ay) = (lx,ly)/2, val = 1
%~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
% J.Idier 01/97
%~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

if exist('ly')~=1
  ly = lx;
end
if exist('val')~=1
  val = 1;
end
if exist('cy')~=1
  cx = (lx+1)/2; cy = (ly+1)/2;
end
if exist('ay')~=1
  ax = lx/2; ay = ly/2;
end
x = (((1:lx)-cx)/ax).^2;
y = (((1:ly)'-cy)/ay).^2;
Z = (x(ones(ly,1),:) + y(:,ones(1,lx)) <= 1);
if val ~= 1
  Z(Z) = val(Z(Z)+0);
end  
