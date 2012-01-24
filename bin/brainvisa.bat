@setlocal
@if exist "%~d0%~p0..\..\brainvisa\neuro.py" (
  @python "%~d0%~p0..\..\brainvisa\neuro.py" %*
) else (
  @python "%~d0%~p0..\brainvisa\neuro.py" %*
)
@endlocal