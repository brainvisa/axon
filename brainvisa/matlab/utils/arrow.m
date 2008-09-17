%
% arrow.m --  affichage d'un chapeau en bout de polygone 
%
% SYNTAXE : arrow(X,Y,[Z,width,pourc])  
%
% basee sur line
%
%
% pourc : tel que width = pourc * height, vaut 0.9 par defaut
% Z, width et pourc : parametres optionnels
% Pour l'affichage 2D avec width et pourc, mettre Z='n'
%
% Pour notations et valeurs par defaut, se reporter a PSTRICKS
%
% Ecrit par Chucky le 08/09/99
%
%

function arrow(X,Y,varargin);

WIDTH = .03;  % largeur par defaut
POURC = .9;  % largeur par defaut
POURC_INSERT = 0.4;  % pourcentage de la hauteur 
 
lgth = POURC;
width = WIDTH;
if ((nargin == 5) | (nargin>=4 & varargin{1}=='n'))
   lgth = varargin{nargin};  % lecture de pourc
end;
if ((nargin >= 4) | (nargin>=3 & varargin{1}=='n'))
   width = varargin{nargin-1}; 
end;
lgth = width/lgth;
inset = POURC_INSERT*lgth;

if ((nargin==5) | (nargin>=3 & varargin{1}~='n'))  % cas 3D
  Z = varargin{1};
  if ((length(X) ~= length(Y)) | (length(X) ~= length(Z)))
    error('ARROW.M : Les vecteurs d''entree ne sont pas de meme longueur');
  end;
  if (length(X)~=2),
    X=X([length(X)-1,length(X)]);  % on ne conserve que le dernier segment
    Y=Y([length(Y)-1,length(Y)]);
    Z=Z([length(Z)-1,length(Z)]);
  end;

  height = sqrt((diff(X)).^2+(diff(Y)).^2+(diff(Z)).^2); 
  VDIR = 1/height*[diff(X),diff(Y),diff(Z)];
  WDIR=[1,0,0];
  if (sum(VDIR.*WDIR))
    WDIR = [0,0,1];
  end;

  ARROW = zeros(4,3);   %  l'arrow a dessiner
  ARROW(1,:) = [X(2),Y(2),Z(2)];  % la pointe de l'arrow
  H = ARROW(1,:)-lgth*VDIR;          % projection de P3 sur (P1 P2)
  ARROW(2,:) = H+width/2*cross(VDIR,WDIR);
  ARROW(4,:) = H-width/2*cross(VDIR,WDIR);
  ARROW(3,:) = ARROW(1,:)-(lgth-inset)*VDIR;  % 

  patch(ARROW(:,1),ARROW(:,2),ARROW(:,3),'k');

elseif (nargin<=3)  % cas 2D
  if (length(X) ~= length(Y))
    error('ARROW.M : Les vecteurs d''entree ne sont pas de meme longueur');
  end;
  if (length(X)~=2),
    X=X([length(X)-1,length(X)]);  % on ne conserve que le dernier segment
    Y=Y([length(Y)-1,length(Y)]);
  end; 

  height = sqrt((diff(X)).^2+(diff(Y)).^2); 
  VDIR = 1/height*[diff(X),diff(Y)];

  ARROW = zeros(4,2);   %  l'arrow a dessiner
  ARROW(1,:) = [X(2),Y(2)];  % la pointe de l'arrow

  % H = Projection de P3 sur (P1 P2)
  % alpha = (P2H,P2P3)
  %
  alpha = atan(width/(2*lgth));
  dist = sqrt(width*width/4+lgth*lgth);      % Pythagore 
  ARROW(2,:) = ARROW(1,:)+dist*VDIR*[-cos(alpha),-sin(alpha);sin(alpha),-cos(alpha)]';
  ARROW(4,:) = ARROW(1,:)-dist*VDIR*[cos(alpha),-sin(alpha);sin(alpha),cos(alpha)]';
  ARROW(3,:) = ARROW(1,:)-(lgth-inset)*VDIR;  % 

  patch(ARROW(:,1),ARROW(:,2),'k');
end;



