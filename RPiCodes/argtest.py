import sys

default = {'-r':(160,120),'-f':90}
argv = sys.argv

params = []

if len(argv)>1:
	for flag in ['-r','-f']:
		try:
			params.append(argv[argv.index(flag)+1])
		except IndexError:
			params.append(default[flag])
else:
	params = [default[flag] for flag in ['-r','-f']]

res,fps = params
print res,fps
