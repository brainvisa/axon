function [x, b] = adn_lassy(x, snr, g_re, g_im);
%     adn_lassy.m     ajout bruit blanc gaussien circulaire 
%     ajout d'un bruit cxe gaussien blanc circulaire
%     grace a makegwn et aux bonnes graines du Lassy                       
%
%    formes d'appel: [y, b] = adn_lassy(x, snr, g_re, g_im);   
%                    [y, b] = adn_lassy(x, snr, g_re);   
%                    [y, b] = adn_lassy(x, snr); 
%    y signal bruite
%    b sequence de bruit qui a ete ajoutee au signal x 
%    g_re (g_im) graine de bruit pour partie reelle (imaginaire)
%    Si ces 2 valeurs sont omises elles sont tirees au hasard
%     
  x = x(:);
  xr = real(x);
  xi = imag(x);   
  n = length(x);
  snr = snr/10;
  snr = 10^snr; 

% verification des arguments, choix des graines par defaut
                                                  
  if((nargin ~= 2) & (nargin ~= 3) & (nargin ~= 4))
     disp('nombre d''arguments incorrect');
     return;
  end
  if(nargin == 2 | nargin == 3)
     rand('uniform');
     if(nargin == 2)
         g_re = 1+floor(51*rand);
     end  
     g_im = 1+floor(51*rand);
     while(g_im == g_re)
         g_im = 1+floor(51*rand);
     end
     disp(['graine re: ',num2str(g_re)]);
     disp(['graine im: ',num2str(g_im)]);
  end
  if(g_re > 51)
     g_re=rem(fix(g_re),51);
  end  
  if(g_im > 51)
     g_im=rem(fix(g_im),51);
  end  

% Partie reelle du bruit

  vs = cov(xr);
  if(vs > 0)
     a = sqrt(vs/snr); 
     eval(['! makegwn -b br_re.mat ',num2str(g_re),' 0.0 ',num2str(a),' ',num2str(n)]);
     load br_re;
     br = Mat;
     vb = cov(br);
     disp(['Partie reelle : SNR empirique     =' num2str(10*log10(vs/vb))]);
  else
     br = zeros(n,1);
  end

% Partie imaginaire du bruit

  vs = cov(xi);
  if(vs > 0)
     a = sqrt(vs/snr);
     eval(['! makegwn -b br_im.mat ',num2str(g_im),' 0.0 ',num2str(a),' ',num2str(n)]);
     load br_im;
     bi = Mat;                              
     vb = cov(bi);
     disp(['Partie imaginaire : SNR empirique =' num2str(10*log10(vs/vb))]);
  else
     bi = zeros(n,1);  
  end

% Ajout du bruit

  b = br + sqrt(-1)*bi;
  x = x + b;

% fin de routine           

end

