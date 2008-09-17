function ch2 = iso(ch1)
% iso.m	fabrique une chaine accentuee au standard ISO a partir
% d'une chaine 7 bits (convention TeX : \'e, ...
% Permet d'accentuer des titres de figures Matlab.
%~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
% chaine2 = iso(chaine1)
%
% Auteur : J. Idier				Date : 08/97
%
% Voir aussi niso.m
%~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
%
% Modification J.-F. Gio le 20 septembre 1997
% Rajoute les dernieres lignes pour guillemets francais, ...
%
%
ch2 = ch1;
ch2 = strsubst(ch2,'\`A',192);
ch2 = strsubst(ch2,'\^A',194);
ch2 = strsubst(ch2,'\`E',200);
ch2 = strsubst(ch2,'\^E',202);
ch2 = strsubst(ch2,'\"E',201);
ch2 = strsubst(ch2,'\^I',206);
ch2 = strsubst(ch2,'\"I',205);
ch2 = strsubst(ch2,'\`U',217);
ch2 = strsubst(ch2,'\^U',219);
ch2 = strsubst(ch2,'\''Y',221);
ch2 = strsubst(ch2,'\''y',253);
ch2 = strsubst(ch2,'\c{C}',199);
ch2 = strsubst(ch2,'\c{c}',231);
ch2 = strsubst(ch2,'\~N',209);
ch2 = strsubst(ch2,'\~n',241);
ch2 = strsubst(ch2,'\^a',226);
ch2 = strsubst(ch2,'\^e',234);
ch2 = strsubst(ch2,'\^o',244);
ch2 = strsubst(ch2,'\^u',251);
ch2 = strsubst(ch2,'\''a',225);
ch2 = strsubst(ch2,'\''e',233);
ch2 = strsubst(ch2,'\''o',243);
ch2 = strsubst(ch2,'\''u',250);
ch2 = strsubst(ch2,'\`a',224);
ch2 = strsubst(ch2,'\`e',232);
ch2 = strsubst(ch2,'\`o',242);
ch2 = strsubst(ch2,'\`u',249);
ch2 = strsubst(ch2,'\"a',228);
ch2 = strsubst(ch2,'\"e',235);
ch2 = strsubst(ch2,'\"o',246);
ch2 = strsubst(ch2,'\"u',252);
ch2 = strsubst(ch2,'\^i',238);
ch2 = strsubst(ch2,'\''i',237);
ch2 = strsubst(ch2,'\"A',196);
ch2 = strsubst(ch2,'\`i',236);
ch2 = strsubst(ch2,'\"O',214);
ch2 = strsubst(ch2,'\''E',201);
ch2 = strsubst(ch2,'\"i',239);
ch2 = strsubst(ch2,'\^O',212);
ch2 = strsubst(ch2,'\`I',204);
ch2 = strsubst(ch2,'\''O',211);
ch2 = strsubst(ch2,'\`O',210);
ch2 = strsubst(ch2,'\~O',213);
ch2 = strsubst(ch2,'\~o',245);
ch2 = strsubst(ch2,'\''U',218);
ch2 = strsubst(ch2,'\"y',255);

% Rajoute par Gio le 20-09-97
ch2 = strsubst(ch2,'\<',171);
ch2 = strsubst(ch2,'\>',187);
ch2 = strsubst(ch2,'\^1',185);
ch2 = strsubst(ch2,'\^2',178);
ch2 = strsubst(ch2,'\^3',179);
