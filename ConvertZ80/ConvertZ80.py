import os
import re
import sys

Z80Regs8	= ('a','b','c','d','e','f','h','l')
Z80Regs16	= ('af', 'bc', 'de', 'hl', 'ix')

#==============================================================================

def GetLine(f):
	szLine = f.readline()
	while szLine != '':
		if szLine[0] != ';':
			return szLine
		szLine = f.readline()
	return ''

#------------------------------------------------------------------------------

def GetConst(S):
	const = S
	if re.match('\d', const):	# 1st char is [0..9]
		if const[len(const)-1] == 'h':
			const = const[:len(const)-1]	# Strip last char

		if len(const) > 4 and const[0] == '0':
			const = const[1:]				# Strip leading zero

		if len(const) > 2 and const[0] == '0':
			const = const[1:]				# Strip leading zero

		const = '$' + const

	return const

#--------------------------------------

# S = 0008h -> $0008
# S = label -> label
# S = labeh -> labeh
def GetAddr16(S):
	return GetConst(S)

#--------------------------------------

# S = (0008h) -> $0008
# S = (label) -> label
# S = (labeh) -> labeh
def GetIndirectAddr16(S):
	res = S[:len(S)-1] 	# Strip last char
	res = res[1:] 		# Strip 1st char
	return GetConst(res)

#--------------------------------------

def GetRegOffset(S):
	reg = S[1:3]						# Middle 2 chars
	if reg not in Z80Regs16:
		print 'Illegal Z80 reg: ' + reg
		return ('', '')

	offset = S[4:]	# Strip 1st 4 chars: '(ix+'
	offset = offset[:len(offset)-1]		# Strip last char: ')'

	if offset[len(offset)-1] == 'h':
		offset = offset[:len(offset)-1]	# Strip last char: 'h'
	offset = '$' + offset

	return reg, offset

#==============================================================================

def adc(S):

	if S[2] in Z80Regs8 and S[3] not in Z80Regs8:
		const = GetConst(S[3])
		print '\tlda\t' + 'Reg' + S[2].upper()
		print '\tadc\t' + '#' + const
		print '\tsta\t' + 'Reg' + S[2].upper()

	else:
		print 'ADC error: unsupported addressing mode: ' + S[2], S[3]

#------------------------------------------------------------------------------

def add(S):

	ind2 = S[3][0] == '('		# S[3] is indirect

	m2plus = re.search('\+', S[3])

	if S[2] in Z80Regs8 and S[3] in Z80Regs8:
		# add a,a
		if S[2] == S[3]:
			print '\tlda\t' + 'Reg' + S[2].upper()
			print '\tasl\t'
			print '\tsta\t' + 'Reg' + S[2].upper()
		else:
			print '\tclc\t'
			print '\tlda\t' + 'Reg' + S[2].upper()
			print '\tadc\t' + 'Reg' + S[3].upper()
			print '\tsta\t' + 'Reg' + S[2].upper()

	elif S[2] in Z80Regs8 and ind2 and m2plus:
		# add a,(ix+18h)
		reg, offset = GetRegOffset(S[3])
		print '\tclc\t' + '\t; CARRY possibly wrong'
		print '\tldy\t' + '#' + offset
		print '\tlda\t' + 'Reg' + S[2].upper()
		print '\tadc\t' + '(Reg' + reg.upper() + '),y'
		print '\tsta\t' + 'Reg' + S[2].upper()

	elif S[2] in Z80Regs8:
		# add a,05h
		const = GetConst(S[3])
		print '\tclc\t' + '\t; CARRY possibly wrong'
		print '\tlda\t' + 'Reg' + S[2].upper()
		print '\tadc\t' + '#' + const
		print '\tsta\t' + 'Reg' + S[2].upper()

	elif S[2] in Z80Regs16 and S[3] in Z80Regs16:
		# add hl,bc
		print '\t+ADDW\t' + 'Reg' + S[2].upper() + ', ' + 'Reg' + S[3].upper()

	else:
		print 'ADD error: unsupported addressing mode: ' + S[2], S[3]

#------------------------------------------------------------------------------

def _and(S):

	ind2 = S[2][0] == '('		# S[2] is indirect

	m2plus = re.search('\+', S[2])

	if S[2] in Z80Regs8:
		# and e
		print '\tand\t' + 'Reg' + S[2].upper()

	elif ind2 and m2plus:
		# and (ix+1bh)
		reg, offset = GetRegOffset(S[2])
		print '\tldy\t' + '#' + offset
		print '\tand\t' + '(Reg' + reg.upper() + '),y'

	else:
		# and 3fh
		const = GetConst(S[2])
		print '\tand\t' + '#' + const

#------------------------------------------------------------------------------

def cp(S):

	ind2 = S[2][0] == '('		# S[2] is indirect

	m2plus = re.search('\+', S[2])

	if ind2 and m2plus:
		# cp (ix+10h)
		reg, offset = GetRegOffset(S[2])
		print '\t+CP_INDIRECT_OFFSET\t' + 'Reg' + reg.upper() + ', ' + offset

	elif not ind2:		
		const = GetConst(S[2])
		print '\tcmp\t' + '#' + const

	else:
		print 'CP error: unsupported addressing mode: ' + S[2]

#------------------------------------------------------------------------------

def dec(S):

	ind2 = S[2][0] == '('		# S[2] is indirect

	m2plus = re.search('\+', S[2])

	if S[2] in Z80Regs8:
		print '\tdec\t' + 'Reg' + S[2].upper()

	elif S[2] in Z80Regs16:
		# dec hl
		reg = GetAddr16(S[2])
		print '\t+DECW\t' + 'Reg' + reg.upper()

	elif ind2 and m2plus:
		# dec (ix+11h)
		reg, offset = GetRegOffset(S[2])
		if reg == '':
			return
		print '\t+DEC_INDIRECT_OFFSET\t' + 'Reg' + reg.upper() + ', ' + offset

	else:
		print ';DEC error: unsupported addressing mode: ' + S[2]

#------------------------------------------------------------------------------

def inc(S):

	ind2 = S[2][0] == '('		# S[2] is indirect

	if S[2] in Z80Regs8:
		print '\tinc\t' + 'Reg' + S[2].upper()
		return

	#

	if ind2:
		# inc (hl)
		reg = GetIndirectAddr16(S[2])

	else:
		# inc hl
		reg = GetAddr16(S[2])

	if reg not in Z80Regs16:
		print 'INC error: Illegal Z80 reg: ' + reg
	elif ind2:
		print '\t+INC_INDIRECT\t' + 'Reg' + reg.upper()
	else:
		print '\t+INCW\t' + 'Reg' + reg.upper()

#------------------------------------------------------------------------------

def jp(S):

	if S[3] == '':
		print '\tjmp\t' + S[2]
		return

	if S[2] == 'z':
		print '\t+JP_Z\t' + S[3]
	elif S[2] == 'nz':
		print '\t+JP_NZ\t' + S[3]
	elif S[2] == 'c':
		print '\t+JP_C\t' + S[3]
	elif S[2] == 'nc':
		print '\t+JP_NC\t' + S[3]
	else:
		print ';JP error: unsupported cc: ' + S[2]

#------------------------------------------------------------------------------

def jr(S):

	if S[3] == '':
		print '\tjmp\t' + S[2]
		return

	if S[2] == 'z':
		print '\tbeq\t' + S[3]
	elif S[2] == 'nz':
		print '\tbne\t' + S[3]
	elif S[2] == 'c':
		print '\tbcc\t' + S[3]	# C inverted
	elif S[2] == 'nc':
		print '\tbcs\t' + S[3]	# C inverted
	else:
		print 'JR error: unsupported cc: ' + S[2]

#------------------------------------------------------------------------------

def ld(S):

	m2 = S[2] in Z80Regs8
	m3 = S[3] in Z80Regs8

	m2plus = re.search('\+', S[2])
	m3plus = re.search('\+', S[3])

	len2 = len(S[2])
	len3 = len(S[3])

	ind2 = S[2][0] == '('		# S[2] is indirect
	ind3 = S[3][0] == '('		# S[3] is indirect

	if m2 and m3:
		# ld c,a
		print '\t+LD\t' + 'Reg' + S[2].upper() + ', ' + 'Reg' + S[3].upper()
		return

	elif m2 and not ind3:
		# ld c,80h
		const = GetConst(S[3])
		print '\t+LD_REG_IMM\t' + 'Reg' + S[2].upper() + ', ' + const
		return

	elif m2 and ind3 and len3 == len('(xx)'):
		# ld a,(hl)
		reg = S[3][1:3]		# Middle 2 chars
		if reg not in Z80Regs16:
			print 'Illegal Z80 reg: ' + reg
			return
		print '\t+LD_REG_INDIRECT\t' + 'Reg' + S[2].upper() + ', ' + 'Reg' + reg.upper()
		return

	elif m2 and ind3 and m3plus:
		# ld h,(ix+15h)
		reg, offset = GetRegOffset(S[3])
		if reg == '':
			return
		print '\t+LD_REG_INDIRECT_OFFSET\t' + 'Reg' + S[2].upper() + ', ' + 'Reg' + reg.upper() + ', ' + offset
		return

	elif m2 and ind3:
		# ld a,(0f1fdh)
		# ld a,(lf1fd)
		abs = GetIndirectAddr16(S[3])
		print '\t+LD_REG_INDIRECT_ABS\t' + 'Reg' + S[2].upper() + ', ' + abs
		return

	elif S[2] in Z80Regs16 and ind3:
		# ld hl,(lf1f6)
		# ld hl,(0f1f6h)
		src = GetIndirectAddr16(S[3])
		print '\t+LDW_INDIRECT\t' + 'Reg' + S[2].upper() + ', ' + src
		return

	elif S[2] in Z80Regs16:
		# ld ix,lf214
		# ld hl,0008h
		const = GetAddr16(S[3])
		print '\t+LDW\t' + 'Reg' + S[2].upper() + ', ' + const
		return

	elif ind2 and m2plus and m3:
		# ld (ix+19h),a
		reg, offset = GetRegOffset(S[2])
		if reg == '':
			return
		print '\t+LD_INDIRECT_OFFSET\t' + 'Reg' + reg.upper() + ', ' + offset + ', ' + 'Reg' + S[3].upper()
		return

	elif ind2 and m2plus and not m3:
		# ld (ix+19h),01h
		reg, offset = GetRegOffset(S[2])
		if reg == '':
			return
		const = GetConst(S[3])
		print '\t+LD_INDIRECT_OFFSET_IMM\t' + 'Reg' + reg.upper() + ', ' +  offset + ', ' + const
		return

	elif ind2 and m3:
		# ld (hl),a
		# ld (0f1fch),a
		# ld (lf1fc),a
		Addr16 = GetIndirectAddr16(S[2])
		if Addr16 in Z80Regs16:
			print '\t+LD_INDIRECT\t' + 'Reg' + Addr16.upper() + ', ' + 'Reg' + S[3].upper()
		else:
			print '\t+LD_INDIRECT_ABS\t' + Addr16 + ', ' + 'Reg' + S[3].upper()
		return

	elif ind2 and not m3:
		# ld (hl),00h
		# ld (0f1f6h),hl
		# ld (lf1f6h),hl
		Addr16 = GetIndirectAddr16(S[2])
		const = GetConst(S[3])
		if Addr16 in Z80Regs16:
			print '\t+LD_INDIRECT_IMM\t' + 'Reg' + Addr16.upper() + ', ' + const
		elif const in Z80Regs16:
			print '\t+LDW_INDIRECT\t' + Addr16 + ', ' + 'Reg' + const.upper()
		else:
			print 'Illegal Z80 reg: ' + Addr16
		return

	#

	print 'LD error: No match for ' + S[2], S[3]

#------------------------------------------------------------------------------

def orr(S):

	if S[2] in Z80Regs8:
		# or l
		print '\tora\t' + 'Reg' + S[2].upper()
	else:
		# or 38h
		const = GetConst(S[2])
		print '\tora\t' + '#' + const

#------------------------------------------------------------------------------

def pop(S):

	if S[2] in Z80Regs16:
		# pop de
		print '\t+POP16\t' + 'Reg' + S[2].upper()
	else:
		print 'POP error: unsupported addressing mode'

#------------------------------------------------------------------------------

def push(S):

	if S[2] in Z80Regs16:
		# push de
		print '\t+PUSH16\t' + 'Reg' + S[2].upper()
	else:
		print 'PUSH error: unsupported addressing mode'

#------------------------------------------------------------------------------

def sbc(S):

	if S[2] in Z80Regs16 and S[3] in Z80Regs16:
		# sbc hl,bc
		print '\t+SBCW\t' + 'Reg' + S[2].upper() + ', ' + 'Reg' + S[3].upper()
	else:
		print 'SBC error: unsupported addressing mode'

#------------------------------------------------------------------------------

def sub(S):

	ind2 = S[2][0] == '('		# S[2] is indirect

	if S[2] in Z80Regs8:
		# sub l
		print '\tsbc\t' + 'Reg' + S[2].upper() + '\t; CARRY possibly wrong'

	elif ind2:
		# sub (hl)
		reg = GetIndirectAddr16(S[2])
		if reg not in Z80Regs16:
			print 'DEC error: Illegal Z80 reg: ' + Addr16
			return
		print '\t+SUB_INDIRECT\t' + 'Reg' + reg.upper()

	else:
		# sub 80h
		const = GetConst(S[2])
		print '\tsec\t' + '\t; CARRY possibly wrong'
		print '\tsbc\t' + '#' + const

#------------------------------------------------------------------------------

def ret(S):

	if S[2] == '':
		print '\trts'
	elif S[2] == 'z':
		print '\t+RET_Z\t' + S[3]
	elif S[2] == 'nz':
		print '\t+RET_NZ\t' + S[3]
	elif S[2] == 'c':
		print '\t+RET_C\t' + S[3]
	elif S[2] == 'nc':
		print '\t+RET_NC\t' + S[3]
	else:
		print ';RET error: unsupported cc: ' + S[2]

	print ''

#------------------------------------------------------------------------------

def xor(S):

	ind2 = S[2][0] == '('		# S[2] is indirect

	if S[2] in Z80Regs8:
		print '\t+LD_REG_IMM\t' + 'Reg' + S[2].upper() + ', 0' + '\t; xor ' + S[2]
#	elif ind2:
#		reg = GetIndirectAddr16(S[2])
	else:
		print 'XOR error: unsupported addressing mode'

#==============================================================================

def Process(S):
	if S[0] != '':
		print S[0]

	if S[1] == '':
		return 1				# No opcode
	elif S[1] == 'nop':
		return 0				# Assume this is data section

	elif S[1] == 'adc':
		adc(S)
	elif S[1] == 'add':
		add(S)
	elif S[1] == 'and':
		_and(S)
	elif S[1] == 'call':
		print '\tjsr\t' + S[2]
	elif S[1] == 'dec':
		dec(S)
	elif S[1] == 'cp':
		cp(S)
	elif S[1] == 'inc':
		inc(S)
	elif S[1] == 'jp':
		jp(S)
	elif S[1] == 'jr':
		jr(S)
	elif S[1] == 'ld':
		ld(S)
	elif S[1] == 'ldi':
		print '\t+LDI'
	elif S[1] == 'or':
		orr(S)
	elif S[1] == 'pop':
		pop(S)
	elif S[1] == 'push':
		push(S)
	elif S[1] == 'ret':
		ret(S)
	elif S[1] == 'sbc':
		sbc(S)
	elif S[1] == 'sub':
		sub(S)
	elif S[1] == 'xor':
		xor(S)
	else:
		s = ';\t'
		for i in range(len(S)):
			s = s + S[i]
		s = s + '\t; ** Unknown opcode **' 
		print s

	return 1

#------------------------------------------------------------------------------

def hdr_code():
	print ';ACME 0.85'
	print ''
	print '!cpu 6502	; Compatible with all Apple2\'s'
	print '!to \"TEST\", plain'
	print '!sl \"TEST.labels\"'
	print '*=$6000'
	print ''
	print '!source \"..\\Common\\Z80-Macros.a\"'
	print '!source \"..\\Common\\ZP-Macros.a\"'
	print '!source \"..\\Common\\AppleDefs.a\"'
	print '!source \"..\\Common\\MockingboardDefs.a\"'
	print ''
	print ';------------------------------------------------------------------------------'
	print ''
	print '!zone code'
	print ''

#------------------------------------------------------------------------------

def hdr_data():
	print ''
	print ';------------------------------------------------------------------------------'
	print ''
	print '!zone data'
	print ''

#------------------------------------------------------------------------------

def help():
	print 'ConvertZ80 v1.0.0'
	print ''
	print 'Usage: ConvertZ80.py <z80.asm>'

#------------------------------------------------------------------------------

def main():
	if len(sys.argv) < 2:
		help()
		return

	hFileIn = open(sys.argv[1], 'r')

	#if len(sys.argv) >= 3:
	#	hFileOut = open(sys.argv[2], 'w')

	hdr_code()

	n = 0
	while n < 1000:
		szLine = GetLine(hFileIn)
		if szLine == '':
			break
		Split = re.split('\s+|,', szLine)
		if Process(Split) == 0:
			break
		n = n + 1

	hdr_data()
	 
	hFileIn.close()
	#hFileOut.close()

#------------------------------------------------------------------------------

main()
