@setlocal
@if exist "%~d0%~p0..\..\brainvisa\neuro.py" (
  @python -S -OO "%~d0%~p0..\..\brainvisa\neuro.py" %*
) else (
  @python -S -OO "%~d0%~p0..\brainvisa\neuro.py"
)
@endlocal