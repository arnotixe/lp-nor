# -*- encoding: UTF-8 -*-
import Linguistic_xcu
import description_xml
import Lightproof_py
import lightproof_handler_py
import Compile
import Dialog
import sys

implname = ""
lang = ""
langlist = ""
version = "0.1"
author = ""
datadir = "."
name = ""
link = ""
dlg = True

if len(sys.argv) == 1:
    print """Synopsis: [-D] [-n name] [-v version] [-d datadir] [-i impl] locale [locale list]
-i id: id is a vendor/implementation ID to identify the extension
-l link: link for the extension site
-d datadir: the source directory of the [language].dat and [language].dlg files
-D         Compile without dialog.
-n name: the name of the extension for the extension manager of OpenOffice.org
-v version: version of the language data/grammar checker"""
    sys.exit(0)

state = ""
for i in sys.argv[1:]:
    if i[0:1] == '-':
        if i[1:2] in "idlnv":
            state = i
            continue
        elif i[1:2] == 'D':
            dlg = False
        else:
            print "missing option: " + i
            sys.exit(0)
    else:
        if state == '-i':
            implname = i
        elif state == '-d':
            datadir = i
        elif state == '-v':
            version = i
        elif state == '-n':
            name = i
        else:
            lang = i
            langlist = sys.argv[-1].replace("_", "-")
            break
        state = ""

if lang == "":
    print "missing language parameter"
    sys.exit(0)

if link == "":
    link = "http://launchpad.net/lightproof"

if implname == "":
    pkg = lang
else:
    pkg = implname + "_" + lang

if name == "":
    name = "Lightproof (" + lang + ")"

f = open("Lightproof.py", "w")
f.write(Lightproof_py.__doc__%(pkg, pkg, pkg, pkg, pkg, pkg))
f.close()

f = open("pythonpath/lightproof_handler_%s.py"%pkg, "w")
f.write(lightproof_handler_py.__doc__%(pkg, pkg, pkg))
f.close()

f = open("Linguistic.xcu", "w")
f.write(Linguistic_xcu.__doc__%(pkg, langlist.replace(",", " ")))
f.close()

f = open("description.xml", "w")
f.write(description_xml.__doc__%(pkg, name, version, link, link))
f.close()

def locnam(st):
    loc = {}
    for i in st.split(","):
        print i
        a = i.split("-")
        if len(a) == 1:
            loc[i] = [ a[0], "", ""]
        else:
            loc[i] = [ a[0], a[1], ""]
    return str(loc)

f = open("pythonpath/lightproof_impl_%s.py"%pkg, "w")
f.write('# -*- encoding: UTF-8 -*-\n')
f.write('pkg = "%s"\n'%pkg)
f.write('lang = "%s"\n'%lang)
f.write('locales = %s\n'%locnam(langlist))
f.write('version = "%s"\n'%version)
f.write('author = "%s"\n'%author)
f.close()

manifest = """<?xml version="1.0" encoding="UTF-8"?>
<manifest:manifest>
        <manifest:file-entry manifest:full-path="dialog/OptionsDialog.xcs"
                manifest:media-type="application/vnd.sun.star.configuration-schema" />
        <manifest:file-entry manifest:full-path="dialog/OptionsDialog.xcu"
                manifest:media-type="application/vnd.sun.star.configuration-data" />
        <manifest:file-entry manifest:media-type="application/vnd.sun.star.uno-component;type=Python"
                manifest:full-path="Lightproof.py"/>
        <manifest:file-entry
                manifest:media-type="application/vnd.sun.star.configuration-data"
                manifest:full-path="Linguistic.xcu" />
</manifest:manifest>"""

manifest2 = """<?xml version="1.0" encoding="UTF-8"?>
<manifest:manifest>
        <manifest:file-entry manifest:media-type="application/vnd.sun.star.uno-component;type=Python"
                manifest:full-path="Lightproof.py"/>
        <manifest:file-entry
                manifest:media-type="application/vnd.sun.star.configuration-data"
                manifest:full-path="Linguistic.xcu" />
</manifest:manifest>"""

code = Compile.c(datadir, lang, "pythonpath/", pkg)
f = open("Lightproof.py", "a")
f.write(code)
f.close()

try:
    Dialog.c(pkg, author, lang, "data/", "dialog/", "pythonpath/", dlg)
    f = open("META-INF/manifest.xml", "w")
    f.write(manifest)
    f.close()
except:
    dlg = False

if not dlg:
    # without dialog
    f = open("META-INF/manifest.xml", "w")
    f.write(manifest2)
    f.close()
