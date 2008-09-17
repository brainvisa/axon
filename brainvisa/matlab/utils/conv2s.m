% conv2s.m	convolution a noyau separable 
%
%
%  appel 	: y = conv2s(x,h,v)
%		  ou y = conv2s(x,h,v,'shape')
%
%		x : image 
%		h : noyau horizontal
%		v : noyau vertical
%	'shape' : 'full' , 'valid', 'mirror' et 'rormi'
%		
%		'full' : forme pre-post 	image bordee de 0 
% 		'valid': forme covariance
%		'mirror': symetrise les bords puis 'valid'
%		'rormi' : 'full' puis repliement des bords
%
%   les formes 'full' valid corresponde a H et H^t si on prend soins de
%		retourner les noyaux avec fliplr et flipud
%  
%      idem pour 'mirror' et 'rormi'
%
% 
%		 AUTEUR : stef    juin 95
%
%
%  faire make dans le repertoire /CNES/SRC/conv2s