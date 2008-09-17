function plotSlices(images,transp,first,step,last,ColorRange,Binaire);

%~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
%
%  function plotSlices(images,transp,first,step,last,ColorRange);
%   
%  images = array of images. images is a 3D array.
%  transp = if 1, transp is given to all the
%           pixels with value equal to images(2,2,J);
%  first = number of the first image to plot
%  step  = step between slices to plot
%  last  = number of the last image to plot
%  ColorRange = 2 element vector used to set color scale
%               by mean of caxis(ColorRange)
%  Binaire = 1  -->  Image 3D binaire, representation de ses coupes en degrade
%  Binaire = 0  -->  Image 3D normale.
%       
%  Author:  Andrea Ridolfi        Date: 01/99
%  ridolfi@lss.supelec.fr
%  GPI-Laboratoire des Signaux et Systemes
%
%~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


view([17.5,30]);
hold on;

if (transp==1),
for Z=first:step:last,
   plan=Z*ones(size(images,1),size(images,2));
   plan(images(:,:,Z)==0)=NaN;
   %%plan(images(:,:,Z)~=images(2,2,Z))=1/Z;
   H=surf(plan);
   if (Binaire),
     set(H,'CData',(last-Z)/(last-first)*images(:,:,Z), ...
	 'FaceColor','texturemap','LineStyle','none');
   else,
     set(H,'CData',images(:,:,Z), ...
	 'FaceColor','texturemap','LineStyle','none');
   end;
end;
else,
for Z=first:step:last,
   H=surf(Z*ones(size(images,1),size(images,2)));
   if (Binaire),
     set(H,'CData',(last-Z)/(last-first)*images(:,:,Z), ...
	 'FaceColor','texturemap','LineStyle','none');
   else,
     set(H,'CData',images(:,:,Z), ...
	 'FaceColor','texturemap','LineStyle','none');
   end;
end;
end;

caxis(ColorRange);
