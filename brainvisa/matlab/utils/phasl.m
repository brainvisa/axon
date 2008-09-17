function phi = phasl(ro,fo);
% phasl.m        Caracteristiques d'une cellule du 2eme ordre !!
% phi = phasl(ro,fo)
% cette fonction trace les caracs d'une cellule
% du second ordre purement recursive reelle de pole
% zo = ro.exp(2ipi.fo), ro < 1, 0 <= fo < 1/2
% et rend la phase du dephaseur ideal qui replie
% le zero 1/zo (a l'exterieur du CU) en un zero en
% zo (a l'interieur du CU), calculee sur 500 pts.
%
 N = 500;
 w = (0:N-1)'*pi/N;
 z = exp(sqrt(-1)*w);
 wdg = w*180/pi;
% exemple de Bellanger
% xo = .6073;
% yo = .5355;
 wo = 2*pi*fo;
 zo = ro*exp(sqrt(-1)*wo);
 xo = real(zo);
 yo = imag(zo);
 H = ones(N,1)./(ones(N,1) - 2*xo*conj(z) + (ro^2)*(conj(z).^2));
% frequence de resonance
 fr = (1/(2*pi))*acos(2*xo*(1 + ro^2)/(4*ro*ro));
 Hm = (1/(1-ro))*(1/((1+ro)*sin(wo)));
% affichage module et phase de la cellule du second ordre
 subplot(3,1,1),plot(wdg/360,abs(H),'-',fr,Hm,'o');
 title('Module et resonnance (o)')
 subplot(3,1,2),plot(wdg/360,-angle(H)*180/pi);
 title('Phase')
 subplot(3,1,3),plot(wdg/360,-angle(H)*180/pi + wdg);
 title('Phase du filtre realisable')
 xlabel(['Cellule rec. 2, pole : mod=',num2str(ro),' freq=',num2str(fo)]);
 disp('Tapez retour');
 pause;
% Phase du dephaseur remplacant le zero 1/zo (de module > 1)
% par le zero zo.
 phi = 2*angle(H)*180/pi - 2*wdg;
 subplot(1,1,1);
 plot(wdg/360,phi);
 title(['Phase du dephaseur qui replie z=',num2str(1/ro),'.exp(2ipi.',num2str(fo),')'])
% fin de routine
end
