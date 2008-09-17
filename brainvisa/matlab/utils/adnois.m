function z = adnois(x, SN, seed)
% adnois.m      Addition of Gaussian random white noise to impulsive signal x 
%
% Syntax:       z = adnois(x, SN, seed)
%
%               x: Signal that noise will be added to. First column is arrival time
%                    second one is 
%               SN: Signal-to-noise ratio, in dB.
%               seed: Seed of the random noise generator. The default
%                     value is set to 0.0
%
%               z: Noisy sequence.
%

%     Modification stef le 2 decembre 94 mise en comformite syntaxe matlab 4.2
%     Modification herve le 6 aout 97 mise en comformite syntaxe matlab 5.1
%       INITIALIZATION

if exist('seed') ~= 1           % If no seed has been specified
    seed = 0.0;                 % Set it to default value
end

[m, n] = size(x);               % Dimension of x and z
z = zeros(m,n);                 % Initialization if z

rx = (x(:, 2)' * x(:, 2)) / m;  % Mean power of x
rn = rx / (10^(SN/10));         % Variance of the noise
Stdn = rn^0.5;                  % Standard deviation of the noise

%       COMPUTATION OF z

z(:, 1) = x(:, 1);              % z has the sane time support then x
randn('seed', seed);            % Initialize seed for normal distribution

z(:, 2) = Stdn*randn(size(x(:, 2))) + x(:, 2);
                                % Addition of noise wuth signal-to-noise
                                % ratio equal to SN
return
