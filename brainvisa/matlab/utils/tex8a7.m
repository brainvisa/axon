function tex8a7(nomf,nomfich)
if(~exist(nomf))
    disp(['''', nomf, ''' n''existe pas']);
    A=[];
else
    [fid, message] = fopen(nomf, 'r');
    if(fid == -1)
        disp(message)
    else
        A = fread(fid, inf, 'uchar');
	B = iso27(A');
        
	[fid, message] = fopen(nomfich, 'w');
	if(fid == -1)
	    disp(message)
	else
	    count = fwrite(fid, B, 'uchar');
	    if(count ~= prod(size(B)))
disp(['Probleme a l''ecriture dans fichier ''', nomfich, '''', num2str(count)])
	    end
	    status = fclose(fid);
	    if(status ~= 0)
	        [message, errnum] = ferror(fid, 'clear');
	        disp(message)
	    else
disp(['Sauvegarde dans fichier ', nomfich, ' : O.K.'])
	    end
	end
    end
end
