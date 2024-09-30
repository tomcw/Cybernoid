acme.exe -DUSE_PHASOR=1 cybernoid2.a
@REM copy cybernoid2.labels %APPLEWIN_DBG%\A2_USER1.sym
move /y CYBERNOID2 CYBERNOID2.PH

acme.exe -DUSE_PHASOR=0 cybernoid2.a
copy cybernoid2.labels %APPLEWIN_DBG%\A2_USER1.sym
