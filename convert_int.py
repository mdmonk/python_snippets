#!/usr/bin/env python
#####################

def main():
	pass

def ConvDecToBaseVar4(num, base):
	if num < 2: return str(num)
	if base > 16 or base < 2:
		raise ValueError, 'The base number must be between 2 and 16.'
	dd = dict(zip(range(16), [hex(i).split('x')[1] for i in range(16)]))
	ans = ''
	while num != 0:
		num, rem = divmod(num, base)
		ans =  str(rem)+ans
	return ans

if __name__ == "__main__":
	main()
