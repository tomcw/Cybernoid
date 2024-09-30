acme.exe -DUSE_PHASOR=1 cybernoid.a
@REM copy cybernoid.labels %APPLEWIN_DBG%\A2_USER1.sym
move /y CYBERNOID CYBERNOID.PH

acme.exe -DUSE_PHASOR=0 cybernoid.a
copy cybernoid.labels %APPLEWIN_DBG%\A2_USER1.sym
