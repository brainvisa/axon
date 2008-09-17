function saveb(A,nomfich)
[fid, message] = fopen(nomfich, 'w');
if(fid == -1)
    disp(message)
else
    count = fwrite(fid, A, 'uchar');
    if(count ~= prod(size(A)))
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
