import sys
import re
from string import split

repl = {}
tests = []
comp = []
modes = ["[Word]", "[word]", "[Char]", "[char]", "[code]"]
mode = "[Word]"
code = u""
language = ""

def prepare_for_eval(s):
	s = re.sub("(affix|spell|morph|stem|option|suggest|generate)\(", r'\1(LOCALE,', s)
	s = re.sub(r"word\(\s*(\d)", r'word(s[m.end():],\1', s)	 # word(n)
	s = re.sub(r"word\(\s*-(\d)", r'wordmin(s[:m.start()],\1', s) # word(-n)
	s = re.sub(r"[\\](\d)", r'm.group(\1)', s)
	s = re.sub("[{]([^}]+)}", r'm.group("\1_1")', s)
	return s


def mysplit(s, line):
	global repl
	global tests
	global comp
	global modes
	global mode
	orig = s
	if s[0:1] == '[':
		if s.strip() in modes:
			mode = s.strip()
			return None
		elif re.match(r"\[\w+\]$", s.strip()):
			sys.stderr.write("Unknown mode: " + s + "\n")
			return None
	dec = 0
	exprep = 0 # replacement is a Python expression (beginning with sign =)
	condition = False
	# description
	c = s.rfind("#")
	com = u""
	if c > -1:
		com = prepare_for_eval(s[c+1:].strip())
		s = s[:c]
	m1 = re.search("<-", s)
	m2 = re.search("->", s)
	if m1 and m2:
	    condition = prepare_for_eval(s[m1.end(0): m2.start(0)].strip())
	    s = s[0:m1.start(0)] + s[m2.start(0):]
	if s[0:1] == '"':
		# quoted
		pos = s[1:].find('"')
		while pos > 0 and s[pos] == '\\':
			pos = s[pos:].find('"')
		s1 = s[1:pos+1]
		s2 = s[pos+2:].strip()
	else:
		m = re.compile("->").search(s)
		if not m:
			m = re.compile("[_a-zA-Z][_a-zA-Z0-9]*").match(s)
			if not m:
			    sys.stderr.write("Syntax error in line " + str(line) + "\n")
			    return None
			s1 = m.group(0)
			s2 = s[m.end(0):].strip()
			# replace previous definitions
			for i in repl:
			    ire = re.compile("[{]" + i + "}")
			    if re.search(ire, s2):
				s2 = ire.sub(repl[i], s2)
			# make named group
			s2 = "(?P<" + m.group(0) + ">" + s2 + ")"
			dec = 1
		else:
			s1 = s[0:m.start(0)].strip()
			if re.match("TEST: ", s1):
			    tests += [[s1[5:].strip(), s[m.end(0):].strip(), line]]
			    return None
			s2 = s[m.start(0):].strip()
	m = re.compile("->").match(s2)
	if dec!= 1 and m:
		s2 = s2[m.end(0):].strip()
	elif dec!=1:
		sys.stderr.write("Syntax error in line " + str(line) + "\n")
		return None
	if s2[0:1] == '=':
		exprep = 1
	if s2[0:1] == '"' and s2[-1:]=='"':
		s2 = s2[1:-1]
	if dec==1:
		repl[s1] = s2
		return None
	else:
		for i in repl:
			s1 = re.sub("[{]" + i + "}", repl[i], s1)
		# modes
		if mode == "[Word]" or mode == "[word]":
			if s1[0] == '^':
				s1 = ur"((?<=[!?.] )|^)" + s1[1:] + ur"(?![-\w\u2013\u00AD])"
			else:
				s1 = ur"(?<![-\w\u2013.,\u00AD])" + s1 + ur"(?![-\w\u2013\u00AD])"
		# modes with casing ([Word] or [Char])
		if mode == "[Word]" or mode == "[Char]":
			s1 = "(?i)" + s1
		# add Unicode flag to the regex by (?u)
		s1 = re.sub("[(][?][iI][)]", "(?iu)", s1)
		if not re.match("[(][?][iI][uU][)]", s1):
			s1 = "(?u)" + s1
		else:
			# casing
			lu = re.compile("(?u)\w")
			s3 = u""
			state = 0
			for i in range(0, len(s1)):
			    c = s1[i]
			    if c == "[":
				    state = 1
			    if state == 1 and c == "]":
				    state = 0
			    if c == "<" and i > 3 and s1[i-3:i]=="(?P":
				    state = 2
			    if state == 2 and c == ">":
				    state = 0
			    if c == "?" and i > 0 and s1[i-1:i]=="(":
				    state = 5
			    if state == 5 and c == ")":
				    state = 0
			    if lu.match(c) and c.islower() and state == 0:
				    if c=="i" and (language == "tr" or language == "az"):
					s3 += u"[\u0130" + c + "]"
				    else:
					s3 += "[" + c.upper() + c + "]"
			    elif lu.match(c) and c.islower() and state == 1 and s1[i+1:i+2] != "-":
				    if s1[i-1:i] == "-" and s1[i-2:i-1].islower():  # [a-z] -> [a-zA-Z]
					s3 += c + s1[i-2:i-1].upper() + "-" + c.upper()
				    elif c=="i" and (language == "tr" or language == "az"):
					s3 += u"\u0130" + c
				    else:
					s3 += c.upper() + c
			    else:
				    s3 += c
			    if c == "\\":
				    state = 4
			    elif state == 4:
				    state = 0
			s1 = s3
		s1 = renum("[?]P<([^<_]*)>", s1, "?P<")
		if exprep == 0:
			s2 = re.sub("[{]([_a-zA-Z][_a-zA-Z0-9]*)}", r"\\g<\1>", s2)
			s2 = renum(r"\\g<([^<_]*)>", s2, r"\\g<")
		else:
			s2 = prepare_for_eval(s2)
	# check
        if re.compile("[(][?]iu[)]").match(s1):
	    cap = True
	    sc = re.sub("[(][?]iu[)]", "(?u)", s1)
	else:
    	    cap = False
	    sc = s1
	try:
	    if not condition:
		comp += [[re.compile(sc), s2, com, cap, line]]
	except:
	    sys.stderr.write("ERROR in line " + str(line) + ":" + str([s1]) + "\n")
	return [s1, s2, com, condition]

# group renum (<groupname> -> <groupname_1> etc.)
def renum(regex, s1, beg):
	j={}
	mr = re.compile(regex)
	m = mr.search(s1)
	nl = s1.find("\\n")
	while m:
		# restart numbering in new lines
		if nl > -1 and m.start(0) > (nl + 1):
			j={}
			nl = s1[m.start(0):].find("\\n")
			if nl > -1:
				nl = m.start(0) + nl
		n = m.group(1)
		if n in j:
			j[n] += 1
		else:
			j[n] = 1
		s1 = re.sub(mr, beg + n + "_" + str(j[n]) + ">", s1, 1)
		m = mr.search(s1)
	return s1

def cap(a, iscap):
    global language
    if iscap:
	for i in range(0, len(a)):
	    if a[i][0:1] == "i":
		if language == "tr" or language == "az":
		    a[i] = u"\u0130" + a[i][1:]
		elif a[i][1:2] == "j" and language == "nl":
		    a[i] = "IJ" + a[i][2:]
		else:
		    a[i] = "I" + a[i][1:]
	    else:
		a[i] = a[i].capitalize()
    return a

def c(data, lang, target, pkg):
 global language
 global code
 language = lang
 f = open(data + "/" + language + ".dat",'r')
 r = re.compile("[\n#]")

 targetdir = "./"
 if target != None:
    targetdir = target

 dic = []

 lines = f.readlines()

 for i in range(0, len(lines)):
	lines[i] = unicode(lines[i], "UTF-8")


# print code section

 lines2 = []

 cm = 0
 for i in lines:
	if i.strip() in modes:
		if i.strip() == "[code]":
			cm = 1
			continue
		else:
			cm = 0
	if cm == 1:
		code = code + i
	else:
		lines2 = lines2 + [i]

 lines = lines2

# concatenate multiline commands
# last tabulator + comment is the message
 l = u""
 comment = 0
 for i in range(len(lines)-1, -1, -1):
	if re.match("	", lines[i]):
	    if not (comment and re.match("	+#", lines[i])):
		l = lines[i].strip() + " " + l
	    if re.search("#", lines[i]):
		comment = 1
	    del lines[i]
	elif l != "":
	    lines[i] = lines[i].strip() + " " + l
	    l = ""
	    comment = 0

# processing
 for i in range(0, len(lines)):
	if not r.match(lines[i]):
		item = mysplit(lines[i].strip(), i + 1)
		if item != None:
			dic = dic + [item]

 for i in tests:
    res = i[0]
    match = 0
    for r in comp:
	while 1:
	    m = r[0].search(res)
	    if m:
		match = 1
		try:
		    res = r[0].sub(r[1], res)
		except:
		    sys.stderr.write("Failed substitution in line " + str(r[4]) + "\n")
		    break		    
		iscap = (r[3] and m.group(0)[0:1].isupper())
		res = "\\n".join(cap(res.split("\n"), iscap))
	    else:
		break
    if match == 1 and res != i[1]:
	    sys.stderr.write("Failed test in line " + str(i[2]) + ":\n")
	    sys.stderr.write("    TEST: " + str([i[0]]) + "\n")
	    sys.stderr.write("EXPECTED: " + str([i[1]]) + "\n")
	    sys.stderr.write("  RESULT: " + str([res]) + "\n")
    elif match == 0:
    	    sys.stderr.write("Warning: Non matched test in line " + str(i[2]) + "\n")
    

 f.close()

 f = open(targetdir + "lightproof_" + pkg + ".py", "w")
 f.write("dic = %s" % dic)
 f.close()
 code = re.sub(r"(?<![\\])\\n", "\n", code.encode("unicode-escape"))
 return re.sub(r"(?<![\\])\\t", "\t", code).replace(r"\\n", r"\n").replace(r"\\t", r"\t")
