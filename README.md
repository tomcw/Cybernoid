# Cybernoid Music Disk

My motivation was to really push the MAME AY8910 emu code, as the Apple
Mockingboard music (Skyfox, Ultima) wasn't really exercising it that
hard.

So as a little R&D proj, I thought I'd convert Dave Rogers' Spectrum
128 Cybernoid routine (written in 1988).

Here's a summary of how I did it:
- I got cybernoid.ay from [here](http://www.worldofspectrum.org/projectay/gdmusic.htm)
- Split it into bin's with AYSplitR
- Disassembled with Inkland's dz80w [here](http://www.inkland.org.uk/dz80/index.htm)
- I wrote 6502 macros to replace the z80 opcodes
- For cybernoid, I hand converted the z80 code to 6502 (using the macros)
- I added a few extension to AppleWin's debugger to help debug the 6502 code (ACME symbol loading & ZP pointer support).

I use Skyfox's MB detection routine.

The Z80 regs are emulated with zero-page memory locations $F0..$F8
The playback routine is very inefficient, as it:
- saves the ZP memory
- restores the Z80 regs
- runs the IRQ handler
- saves the Z80 regs
- restores the ZP memory

This allows playback to work simultaneously with Applesoft & ProDOS. If
DOS3.3 doesn't disable IRQs around disk I/O, then it won't work on a
real Apple (under DOS3.3), but it'll still work on an emulator :-)

I profiled the IRQ handler and IIRC, it takes about 20% of the frame on
average. This is poor, but the code can easily be optimised. Remember
this was really just a proof of concept.

After this, I wrote a python script to do the Z80->6502, and quickly
converted Cybernoid-II.

Currently playback on real h/w produces noisy renditions of the tunes. I
have replaced my AY-register update routine with the slower one used by Skyfox
which gives better but not perfect results.

Tom
25 March 2006