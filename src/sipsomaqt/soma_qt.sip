%Import QtCore/QtCoremod.sip

%Module somaqt

%If (WS_WIN)

%UnitCode
#include <windef.h>
#include <winbase.h>
%End

%InitialisationCode
  SetErrorMode(SEM_NOGPFAULTERRORBOX);
%End

%End

QProcess* makeQProcess() /Factory/;
%MethodCode
  sipRes = new QProcess;
%End