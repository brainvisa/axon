%Import QtCore/QtCoremod.sip

%Module somaqt 0

QProcess* makeQProcess() /Factory/;
%MethodCode
  sipRes = new QProcess;
%End
