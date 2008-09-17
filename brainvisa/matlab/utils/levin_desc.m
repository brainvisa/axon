
% levin_desc.m   Algorithme de Levinson descendant (mexfile)
%                Programme LEVIN_DESCMEX       Version 1.0
%  
%                Auteur: F. Champagnat    Date: 07/92.
%    
%     
%                Ce programme realise l'interface entre l'environnement
%		Matlab et les programmes de l'application seismic DRGOC
%        
%		Objet:
%		-----
%                Cette fonction met en oeuvre l'algorithme de Levinson
%		descendant : elle prend en entree la suite des p para-
%		metres AR et rend la suite des p coefficients de reflection
%		ainsi que la suite des (p+1) correlations correspondantes
%		la variance du bruit generateur etant prise egale a un.
%		la fonction permet en outre de tester la stabilite du filtre
%		recursif defini par les parametres AR.
%
%
%                                                                                
%                Forme d'appel:
%                -------------
%                [r, k] = levin_desc(a); 
%                
%                Variables d'entree et de sortie:
%                -------------------------------
%	E	a:      Coefficients AR. 
%			Vecteur Matlab ligne ou colonne.
%
%	S	r:      Coefficients de correlation.
%			Vecteur Matlab ligne ou colonne.
%			length(r) = length(a)+1.
%
%	S	k:      Coefficients de reflection.
%			Vecteur Matlab ligne ou colonne.
%			length(k) = length(a).

function [r, k] = levin_desc(a); 
[r, k] = levin_descmex(a);

