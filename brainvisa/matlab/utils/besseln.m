function J = besseln(n,x)
%Rq : Fonction recuperee dans Matlab 3.5 pour des arguments complexes
%
%BESSELN Integer order Bessel functions.
%       BESSELN(n,X) = Bessel function, J-sub-n (X).
%       Bessel functions are solutions to Bessel's differential
%       equation of order n:
%                  2                    2   2
%                 x * y'' +  x * y' + (x - n ) * y = 0
%
%       The function is evaluated for every point in the array X.
%       The order, n, must be a nonnegative integer scalar.
%	Modified Bessel functions of integer order may be calculated
%	using BESSELN with purely imaginary values of X.  The
%	relationship is:
%
%	             n
%	I  (x) = (-1)  J  (ix)
%	 n              n
%
%       See also BESSEL, BESSELH and BESSELA.

%       C.B. Moler, 7-11-87, 5-19-90.
%       Copyright (c) 1987-90 by the MathWorks, Inc.
%
%       Reference: Abramowitz and Stegun, Handbook of Mathematical
%         Functions, National Bureau of Standards, Applied Math.
%         Series #55, sections 9.1.1 and 9.12.

   if (n < 0) | (n ~= round(n))
      error(['The order, n = ' num2str(n) ...
              ', must be a nonnegative integer scalar.']);
   end

   % Backwards three term recurrence for J-sub-n(x).

   tiny = 16^(-229);
   if tiny ~= 0 
      % IEEE and VAX-G: Jn underflows at 2^(-1022) for n > nu.
      nu = 300 + 2.5*x;
   else
      tiny = 16^(-30);
      % VAX-D: Jn underflows at 2^(-126) for n > nu.
      nu = 60 + 1.5*x;
   end
   if n >= nu
      J = 0;
      return
   end

   % Temporarily replace x=0 with x=1
   z = abs(x)==0;
   x = x + z;

   % Starting index for backwards recurrence.
   c = [ 0.9507    1.4208   14.1850
         0.9507    1.4208   14.1850
         0.9507    1.4208   14.1850
         0.7629    1.4222   13.9554
         0.7369    1.4289   13.1756
         0.7674    1.4311   12.4523
         0.8216    1.4354   11.2121
         0.8624    1.4397    9.9718
         0.8798    1.4410    8.9217
         0.9129    1.4360    7.8214
         0.9438    1.5387    6.5014
         0.9609    1.5216    5.7256
         0.9693    1.5377    5.3565
         0.9823    1.5220    4.5659
         0.9934    1.5049    3.7902
         0.9985    1.4831    3.2100
         1.0006    1.4474    3.0239
         0.9989    1.4137    2.8604
         0.9959    1.3777    2.7760
         1.0005    1.3500    2.3099]';
   j = 1+min(n,19);
   m = c(1,j).*max(3,j) + c(2,j).*(max(1,abs(x))-1) + ...
       c(3,j)./(1-log(min(1,abs(x))));
   % Make sure rem(m,4)=0.
   m = 4*ceil(m/4);
   % Make sure starting index is not absurdly large.
   mm = min(max(m(:)),2^15);

   k = mm;
   bkp1 = 0*x;
   bk = tiny*(m==k);
   bn = bk;
   t = 2*bk;
   rx = (2)./x;
   for k = mm-1:-1:0
     bkp2 = bkp1;
     bkp1 = bk;
     bk = (k+1)*bkp1.*rx - bkp2 + tiny*(m==k);
     if k == n, bn = bk; end
     if (k > 0 & rem(k,2)==0)
        s = t + 2*bk;
        if ~isfinite(s),  break, end
        t = s;
     end
     if k == 0 , t = t + bk; end
   end

   % Normalizing condition, J0(x) + 2*J2(x) + 2*J4(x) + ... = 1.
   J = bn./t;

   % Restore results for x = 0; J0(0) = 1, Jn(0) = 0 for n > 0.
   J = (1-z).*J + z*(n==0);
