import sys

def clear_ins(l):
	l = l.split('] ')[1] 
	#remove comment
	if ";" in l:
		l = l.split(";")[0].strip()
	out = l.split()
	for i, o in enumerate(out):
		if i > 0:
			out[i] = int(o)
	return out
	
def clear_var(l):
	#remove comment
	if ";" in l:
		l = l.split(";")[0].strip()
	#but also handle the other dtypes
	if '"' in l:
		l = l.replace('"', '')
	elif "nil" == l:
		l = None
	else:
		try:
			l = int(l)
		except:
			pass
	return l

def RK(n):
	#RK(B) Register B or a constant index
	#RK(C) Register C or a constant index
	# RK may be registers or constants
	if n < 250:
		return registers[n]
	else:
		return constants[n-250]

# def getv(n):
	# try:
		# if locals[n] and not registers[n]:
			# return locals[n]
		# else:
			# return registers[n]
			
	# except:
		# return registers[n]
		
def read_instr(instructions, i, indent=0, was_self=False, notagain=None):
	if i == notagain:
		print("info: terminated loop construct")
		return
	ins = instructions[i]
	# print(ins[0])
	if ins[0] in ("eq", "lt", "le"):
		# if ((RK(B) == RK(C)) ~= A) then pc++
		A,B,C = ins[1:]
		#set the comparison operator
		if ins[0] == "eq":
			if A == 1:
				op = "~="
			else:
				op = "=="
		elif ins[0] == "lt":
			if A == 1:
				op = ">"
			else:
				op = "<"
		elif ins[0] == "le":
			if A == 1:
				op = ">="
			else:
				op = "<="
		print( "\t"*indent + f"if {RK(B)} {op} {RK(C)} then" )
		#true path
		read_instr(instructions, i+2, indent+1, was_self, notagain)
		#false path
		print( "\t"*indent + "else")
		read_instr(instructions, i+1, indent+1, was_self, notagain)
		print( "\t"*indent + "end")
		
	elif ins[0] == "settable":
		# A B C   R(A)[RK(B)] := RK(C)
		A,B,C = ins[1:]
		var_A = registers[A]
		var_B = RK(B)
		var_C = RK(C)
		# int indexing
		if type(var_B) == type(0):
			print( "\t"*indent + f"{var_A}[{var_B}] = {var_C}" )
		else:
			print( "\t"*indent + f"{var_A}.{var_B} = {var_C}" )
		#just continue with the next
		read_instr(instructions, i+1, indent, was_self, notagain)
		
	elif ins[0] == "gettable":
		
		# R(A) := R(B)[RK(C)]
		A,B,C = ins[1:]
		var_A = registers[A]
		var_B = registers[B]
		var_C = RK(C)
		# int indexing
		if type(var_C) == type(0):
			print( "\t"*indent + f"local {var_A} = {var_B}[{var_C}]" )
		else:
			print( "\t"*indent + f"local {var_A} = {var_B}.{var_C}" )
		#just continue with the next
		read_instr(instructions, i+1, indent, was_self, notagain)

	elif ins[0] == "jmp":
		# sBx PC += sBx
		read_instr(instructions, i+ins[1]+1, indent, was_self, notagain)
		
	elif ins[0] == "self":
		#A B C   R(A+1) := R(B); R(A) := R(B)[RK(C)]
		A,B,C = ins[1:]
		# A determines start of params & returns
		# B determines amount of parameters
		# C determines amount of returns
		
		var_A = RK(A)
		var_B = RK(B)
		var_C = RK(C)
		registers[A+1] = var_C
		# registers[A] = var_B+":"+var_C
		registers[A] = registers[B]
		# registers[A] = RK(C)
		# print( "\t"*indent + f"local {var_A} = {var_B}:{var_C}("")")
		read_instr(instructions, i+1, indent, True, notagain)
		
	elif ins[0] == "call":
		#A B C   R(A), ... ,R(A+C-2) := R(A)(R(A+1), ... ,R(A+B-1))
		A,B,C = ins[1:]
		# A determines start of params & returns
		# B determines amount of parameters: parameters = B-1
		# C determines amount of returns
		
		#get parameters from the registers after A
		if not was_self:
			params = ", ".join([str(registers[j]) for j in range(A+1, A+B)])
			if C == 1:
				print( "\t"*indent + f"{registers[A]}("+ params+")")
			else:
				returns = ", ".join([str(registers[j]) for j in range(A, A+C-1)])
				print( "\t"*indent + f"local {returns} = {registers[A]}("+ params+")")
		else:
			params = ", ".join([str(registers[j]) for j in range(A+2, A+B)])
			if C == 1:
				print( "\t"*indent + f"{registers[A]}:{registers[A+1]}("+ params+")")
			else:
				returns = ", ".join([str(registers[j]) for j in range(A, A+C-1)])
				print( "\t"*indent + f"local {returns} = {registers[A]}:{registers[A+1]}("+ params+")")
			
		read_instr(instructions, i+1, indent, False, notagain)
	
	elif ins[0] == "return":
		#A B   return R(A), ... ,R(A+B-2)
		A,B = ins[1:]
		# A determines start of returns
		# B determines amount of returns
		#B == 1 means no return values
		params = ", ".join([registers[j] for j in range(A, A+B-1)])
		print( "\t"*indent + f"return "+ params)
		
	elif ins[0] == "getglobal":
		A,B = ins[1:]
		registers[A] = constants[B]
		read_instr(instructions, i+1, indent, was_self, notagain)
		
	# elif ins[0] == "setglobal":
		# A,B = ins[1:]
		# registers[A] = constants[B]
		# read_instr(instructions, i+1, indent, was_self, notagain)
	
	elif ins[0] == "loadk":
		A,B = ins[1:]
		registers[A] = constants[B]
		read_instr(instructions, i+1, indent, was_self, notagain)
		
	elif ins[0] == "move":
		A, B = ins[1:]
		registers[A] = registers[B]
		read_instr(instructions, i+1, indent, was_self, notagain)
	
	
	###########################################################
	# Arithmetic and String Instructions
	###########################################################
	# note: we can't perform these additions because data may be vars or constants
	elif ins[0] == "add":
		#A B C  R(A) := RK(B) + RK(C)
		A,B,C = ins[1:]
		registers[A] = RK(B)# + RK(C)
		print( "\t"*indent + f"{registers[A]} = {RK(B)} + {RK(C)}")
		read_instr(instructions, i+1, indent, was_self, notagain)
		
	elif ins[0] == "sub":
		#A B C  R(A) := RK(B) - RK(C)
		A,B,C = ins[1:]
		registers[A] = RK(B)# - RK(C)
		print( "\t"*indent + f"{registers[A]} = {RK(B)} - {RK(C)}")
		read_instr(instructions, i+1, indent, was_self, notagain)
		
	elif ins[0] == "mul":
		#A B C  R(A) := RK(B) * RK(C)
		A,B,C = ins[1:]
		registers[A] = RK(B)# * RK(C)
		print( "\t"*indent + f"{registers[A]} = {RK(B)} * {RK(C)}")
		read_instr(instructions, i+1, indent, was_self, notagain)
		
	elif ins[0] == "div":
		#A B C  R(A) := RK(B) / RK(C)
		A,B,C = ins[1:]
		registers[A] = RK(B)# / RK(C)
		print( "\t"*indent + f"{registers[A]} = {RK(B)} / {RK(C)}")
		read_instr(instructions, i+1, indent, was_self, notagain)
	
	elif ins[0] == "pow":
		#A B C  R(A) := RK(B) ^ RK(C)
		A,B,C = ins[1:]
		registers[A] = RK(B)# ** RK(C)
		print( "\t"*indent + f"{registers[A]} = {RK(B)} ^ {RK(C)}")
		read_instr(instructions, i+1, indent, was_self, notagain)
		
		
	###########################################################
	# 7  Upvalues and Globals
	###########################################################
	elif ins[0] == "getupval":
		#A B   R(A) := UpValue[B]
		A, B = ins[1:]
		registers[A] = upvalues[B]
		read_instr(instructions, i+1, indent, was_self, notagain)
		
	elif ins[0] == "setupval":
		#A B UpValue[B] := R(A)
		A,B = ins[1:]
		upvalues[B] = registers[A]
		read_instr(instructions, i+1, indent, was_self, notagain)
		
	elif ins[0] == "getglobal":
		#A Bx R(A) := Gbl[Kst(Bx)]
		A, Bx = ins[1:]
		registers[A] = globals[ constants[Bx] ]
		print( "\t"*indent + f"{registers[A]} = {globals[ constants[Bx] ]}")
		read_instr(instructions, i+1, indent, was_self, notagain)
	#page 6	
	elif ins[0] == "setglobal":
		#A Bx  Gbl[Kst(Bx)] := R(A)
		A,Bx = ins[1:]
		globals[ constants[Bx] ] = registers[A]
		print( "\t"*indent + f"{globals[ constants[Bx] ]} = {registers[A]}")
		read_instr(instructions, i+1, indent, was_self, notagain)
		
	###########################################################
	# 12  Loop Instructions
	###########################################################
	elif ins[0] == "forloop":
		#A sBx    R(A)+=R(A+2)
		#if R(A) <?= R(A+1) then PC+= sBx
		A, sBx = ins[1:]
		print( "\t"*indent + f"for {registers[A]} = {A} do")
		read_instr(instructions, i+ins[2]+1, indent+1, was_self, i)
		print( "\t"*indent + f"end")
	
	###########################################################
	# 13  Table Creation
	###########################################################
	
	elif ins[0] == "newtable":
		# A B C   R(A) := {} (size = B,C)
		A,B,C = ins[1:]
		var_A = registers[A]
		print( "\t"*indent + f"local {var_A} = "+"{}")
		#just continue with the next
		read_instr(instructions, i+1, indent, was_self, notagain)
		
	elif ins[0] == "setlist":
		#A Bx     R(A)[Bx-Bx%FPF+i] := R(A+i),
		# where 1 <= i <= Bx%FPF+1
		A, Bx = ins[1:]
		
		#hardcoded in lua
		FPF = 32
		
		input = ", ".join( [ registers[A+j] for j in range(1, Bx%FPF+1) ] )
		# print(Bx%FPF+1)
		# print(A,Bx)
		print( "\t"*indent + f"{registers[A]} = "+"{"+input+"}")
		read_instr(instructions, i+1, indent, was_self, notagain)
	
	
	else:
		print("\t"*indent + "NOT IMPLEMENTED "+ins[0])
	

file = "compiled2.asm"
file = "jgb.lua"
file = sys.argv[1]
f = open(file, "r")

for line in f.readlines():
	if line.startswith(".function"):
		# vararg function flag, true if non-zero
		# maximum stack size (number of registers used)
		num_upvalues, num_params, vararg_flag, max_stack_size = [int(j) for j in line[10:].split()]
		
		locals = []
		constants = []
		instructions = []
		registers = []
		globals = {}
	
	if line.startswith(".local"):
		locals.append( clear_var(line[8:]) )
		
	if line.startswith(".const"):
		constants.append( clear_var(line[8:]) )
		
	if line.startswith("["):
		instructions.append( clear_ins(line)  )
		
	if line.startswith("; end of function"):
		registers = [f"reg{i}" for i in range(max_stack_size)]
		registers[0:len(locals)] = locals
		upvalues = [f"upval{i}" for i in range(num_upvalues)]

		moved = list(registers)
		print(num_upvalues, num_params, vararg_flag, max_stack_size)
		# print(locals)
		# print(constants)
		# print(instructions)
		read_instr(instructions, 0)
		# print(registers)
		# print(upvalues)
