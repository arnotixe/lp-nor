# -*- encoding: UTF-8 -*-
import sys
import re
from string import split
import os
import codecs

comment = re.compile(ur"[\n#]")
ids = re.compile(ur"\w+:\s*\*?\w+(,\s*\*?\w+)*")
lang = re.compile(ur"\[.+=.+\]\s*")
titl = re.compile(ur"\w+\s*=\s*")
helptexts = []

xdl_header = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE dlg:window PUBLIC "-//OpenOffice.org//DTD OfficeDocument 1.0//EN" "dialog.dtd">
<dlg:window xmlns:dlg="http://openoffice.org/2000/dialog" xmlns:script="http://openoffice.org/2000/script" dlg:id="%s" dlg:left="101" dlg:top="52" dlg:width="196" dlg:height="72" dlg:closeable="true" dlg:moveable="true" dlg:withtitlebar="false">
 <dlg:bulletinboard>
"""
xdl_footer = """</dlg:bulletinboard>
</dlg:window>
"""
xdl_group = '<dlg:fixedline dlg:id="%s" dlg:tab-index="%d" dlg:left="5" dlg:top="%d" dlg:width="240" dlg:height="10" dlg:value="&amp;%s"/>\n'
xdl_item = '<dlg:checkbox dlg:id="%s" dlg:tab-index="%d" dlg:left="%d" dlg:top="%d" dlg:width="%d" dlg:height="10" dlg:value="&amp;%s" dlg:checked="%s" %s/>\n'

xcs_header = """<?xml version="1.0" encoding="UTF-8"?>
<oor:component-schema xmlns:oor="http://openoffice.org/2001/registry" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
oor:name="%s" oor:package="org.openoffice" xml:lang="en-US">
<info>
<author>%s</author>
<desc>Contains the options data used for the test extensions.</desc>
</info>
<templates>
"""
xcs_leaf_header = ur"""
                <group oor:name="%s">
                        <info>
                                <desc>The data for one leaf.</desc>
                        </info>
"""
xcs_leaf = ur"""<prop oor:name="%s" oor:type="xs:string">
                                <value></value>
</prop>
"""
xcs_leaf_footer = ur"""                </group>
"""
xcs_component_header = """        </templates>
        <component>
                <group oor:name="Leaves">
"""
xcs_component = """
                        <node-ref oor:name="%s" oor:node-type="%s"/>
"""
xcs_footer = """                </group>
        </component>
        
</oor:component-schema>
"""
xcu_header = u"""<?xml version='1.0' encoding='UTF-8'?>
<!DOCTYPE oor:component-data SYSTEM "../../../../component-update.dtd">
<oor:component-data oor:name="OptionsDialog" oor:package="org.openoffice.Office" xmlns:oor="http://openoffice.org/2001/registry" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <node oor:name="Nodes">
                <node oor:name="org.openoffice.lightproof" oor:op="fuse">
                        <prop oor:name="Label">
                                <value xml:lang="en">Dictionaries</value>
                                <value xml:lang="hu">Szótárak</value>
                        </prop>
                        <node oor:name="Leaves">
"""
xcu_node_header = """
                                <node oor:name="org.openoffice.lightproof.%s" oor:op="fuse">
                                        
                                        <prop oor:name="Id">
                                                <value>org.openoffice.comp.pyuno.lightproof.oxt.%s</value>
                                        </prop>
                                        
                                        <prop oor:name="Label">
"""
xcu_node = """
                                                <value xml:lang="%s">%s</value>
"""
xcu_node_footer = """
                                        </prop>
                                        
                                        <prop oor:name="OptionsPage">
                                                <value>%%origin%%/%s.xdl</value>
                                        </prop>
                                        
                                        <prop oor:name="EventHandlerService">
                                                <value>org.openoffice.comp.pyuno.LightproofOptionsEventHandler.%s</value>
                                        </prop>
                                        
                                </node>
"""
xcu_footer = """
                        </node>
                </node>
        </node>
</oor:component-data>
"""

indexes = {}
indexes_def = {}
modules = {}

def create_xdl(inp, target):
    global indexes
    global indexes_def
    global modules
    f = open(inp,'r')
    name = os.path.basename(inp)[:-4]
    indexes[name] = []
    indexes_def[name] = []
    modules[name] = []
    f2 = open(target + "/" + name + ".xdl",'w')
    lines = f.readlines()
    state = 0
    f2.write(xdl_header%name)

    k = 0
    k2 = 0
    lin = 0
    ok = False
    for i in lines:
        i = i.strip()
        if "=" in i and r"\n" in i:
            helptexts.append(i.split("=")[0])
    for i in lines:
        i = unicode(i.strip().replace(r"\n", "@#@") + "\n", "UTF-8")
        lin = lin + 1
        if not comment.match(i):
            if state == 0:
                ok = True
                if ids.match(i.strip()):
                    j = split(i.strip(),":")
                    f2.write(xdl_group%(j[0].strip(), k, k2 * 10 + 5, j[0].strip()))
                    for l in split(j[1],","):
                        k = k + 1
                        k2 = k2 + 1
                        l = l.strip()
                        la = split(l, " ")
                        l3 = 0
                        itemlen = int(240 / len(la)) 
                        for l2 in la:
                            if l2 != "-":
                                checked = "false"
                                if l2[0] == '*':
                                    checked = "true"
                                    l2 = l2[1:]
                                    indexes_def[name] += [l2]
                                indexes[name] += [l2]
                                helptext = ""
                                if l2 in helptexts:
                                    helptext = "dlg:help-text=\"&amp;hlp_" + l2 + "\""
                                f2.write(xdl_item%(l2, k, 10 + itemlen * l3, k2 * 10 + 5, itemlen, l2, checked, helptext))
                                l3 = l3 + 1
                                k = k + 1
                    k2 = k2 + 1
                    k = k + 1
                else:
                    ok = False
            if lang.match(i.strip()):
                if state == 0:
                    f2.write(xdl_footer)
                f2.close()
                i = i.strip()
                langname = i[1:i.find("=")]
                modules[name] += [langname[:langname.find("_")], i[i.find("=")+1:-1]]
                f2 = open(target + "/" + name + "_" + langname + ".properties",'w')
                state = state + 1
                if state == 1:
                    f3 = open(target + "/" + name + "_" + langname + ".default",'w')
                    f3.close()
            elif titl.match(i.strip()):
                hlp = i.encode("unicode-escape").replace(r"\n","\n").replace(r"\t","\t").replace(r"\x","\\u00").split("@#@", 1)
                if len(hlp) > 1:
                    helptexts.append(hlp[0].split("=")[0])
                    f2.write("hlp_" + hlp[0].split("=")[0] + "=" + hlp[1])
                    hlp[0] = hlp[0] + "\n"
                f2.write(hlp[0])
            elif not ok:
                print "Syntax error in line %d: %s" %(lin, i)
    f2.close()

def c(pkg, author, language, inpdir, target, prgtarget, dlg):

 targetdir = "./"
 prgtargetdir = "./"

 if target != None:
    targetdir = target

 if prgtarget != None:
    prgtargetdir = prgtarget

 inpfiles = []

 for i in language.split(","):
    inpfiles += [inpdir + i + ".dlg"]

 # create opts file

 f2 = open(prgtargetdir + "lightproof_opts_%s.py"%pkg,'w')
 f2.write("lopts = {}\n")
 f2.write("lopts_default = {}\n")
 f2.close()

 if not dlg:
    return

 # create xdl dialog data files

 for i in inpfiles:
    create_xdl(i, targetdir)

 f2 = open(targetdir + "/OptionsDialog.xcs",'w')
 f2.write(xcs_header%("Lightproof_" + pkg, author))
 for i in indexes:
    f2.write(xcs_leaf_header%i)
    f2.write(xcs_leaf*len(indexes[i])%tuple(indexes[i]))
    f2.write(xcs_leaf_footer)
 f2.write(xcs_component_header)
 for i in indexes:
    f2.write(xcs_component%(i,i))
 f2.write(xcs_footer)
 f2.close()

 f2 = codecs.open(targetdir + "/OptionsDialog.xcu",'w', encoding="UTF-8")
 f2.write(xcu_header) # LANG
 for i in indexes:
    f2.write(xcu_node_header%(pkg, pkg))
    f2.write(xcu_node*(len(modules[i])/2)%tuple(modules[i]))
    f2.write(xcu_node_footer%(i, pkg))
 f2.write(xcu_footer)
 f2.close()

 # python resource file

 f2 = open(prgtargetdir + "lightproof_opts_%s.py"%pkg,'a')
 for i in indexes:
    f2.write("lopts['" + i + "'] = " + str(indexes[i]) + "\n")
 for i in indexes:
    f2.write("lopts_default['" + i + "'] = " + str(indexes_def[i]) + "\n")
 f2.close()
