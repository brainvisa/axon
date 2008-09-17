function ch2 = niso27(ch1)
% niso.m fabrique une chaine 7 bits (convention TeX : \'e, ...) a partir
% d'une chaine accentuee au standard NON ISO.
%~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
% chaine2 = niso27(chaine1)
%
% Auteur : J. Idier				Date : 10/97
%
% Voir aussi iso27.m
%~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
%
% Modification J.-F. Gio le 20 septembre 1997
% Rajoute les deux dernieres lignes pour guillemets francais. 
%
%
ch2 = ch1;
ch2 = strsubst2(ch2,'\`A',161);
ch2 = strsubst2(ch2,'\^A',162);
ch2 = strsubst2(ch2,'\`E',163);
ch2 = strsubst2(ch2,'\^E',164);
ch2 = strsubst2(ch2,'\"E',165);
ch2 = strsubst2(ch2,'\^I',166);
ch2 = strsubst2(ch2,'\"I',167);
ch2 = strsubst2(ch2,'\`U',173);
ch2 = strsubst2(ch2,'\^U',174);
ch2 = strsubst2(ch2,'\''Y',177);
ch2 = strsubst2(ch2,'\''y',178);
ch2 = strsubst2(ch2,'\c{C}',180);
ch2 = strsubst2(ch2,'\c{c}',181);
ch2 = strsubst2(ch2,'\~N',182);
ch2 = strsubst2(ch2,'\~n',183);
ch2 = strsubst2(ch2,'\^a',192);
ch2 = strsubst2(ch2,'\^e',193);
ch2 = strsubst2(ch2,'\^o',194);
ch2 = strsubst2(ch2,'\^u',195);
ch2 = strsubst2(ch2,'\''a',196);
ch2 = strsubst2(ch2,'\''e',197);
ch2 = strsubst2(ch2,'\''o',198);
ch2 = strsubst2(ch2,'\''u',199);
ch2 = strsubst2(ch2,'\`a',200);
ch2 = strsubst2(ch2,'\`e',201);
ch2 = strsubst2(ch2,'\`o',202);
ch2 = strsubst2(ch2,'\`u',203);
ch2 = strsubst2(ch2,'\"a',204);
ch2 = strsubst2(ch2,'\"e',205);
ch2 = strsubst2(ch2,'\"o',206);
ch2 = strsubst2(ch2,'\"u',207);
ch2 = strsubst2(ch2,'\^i',209);
ch2 = strsubst2(ch2,'\''i',213);
ch2 = strsubst2(ch2,'\"A',216);
ch2 = strsubst2(ch2,'\`i',217);
ch2 = strsubst2(ch2,'\"O',218);
ch2 = strsubst2(ch2,'\''E',220);
ch2 = strsubst2(ch2,'\"i',221);
ch2 = strsubst2(ch2,'\^O',223);
ch2 = strsubst2(ch2,'\`I',230);
ch2 = strsubst2(ch2,'\''O',231);
ch2 = strsubst2(ch2,'\`O',232);
ch2 = strsubst2(ch2,'\~O',233);
ch2 = strsubst2(ch2,'\~o',234);
ch2 = strsubst2(ch2,'\''U',237);
ch2 = strsubst2(ch2,'\"y',239);

% Rajoute par Gio le 20-09-97
ch2 = strsubst2(ch2,'\<',251);
ch2 = strsubst2(ch2,'\>',253);
