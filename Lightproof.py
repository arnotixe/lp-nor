# -*- encoding: UTF-8 -*-
# Lightproof grammar checker for LibreOffice and OpenOffice.org
# http://launchpad.net/lightproof
# version 1.4.3 (2011-12-05)
#
# 2009-2011 (c) László Németh (nemeth at numbertext org), license: MPL 1.1 / GPLv3+ / LGPLv3+

import uno, unohelper, sys, traceback, re
from lightproof_impl_la import locales
from lightproof_impl_la import pkg
import lightproof_handler_la
from string import join

from com.sun.star.linguistic2 import XProofreader, XSupportedLocales
from com.sun.star.linguistic2 import ProofreadingResult, SingleProofreadingError
from com.sun.star.lang import XServiceInfo, XServiceName, XServiceDisplayName
from com.sun.star.lang import Locale
from com.sun.star.text.TextMarkupType import PROOFREADING

# loaded rules
langrule = {}
# ignored rules
ignore = {}

# cache for morphogical analyses
analyses = {}
stems = {}
suggestions = {}

# assign Calc functions
calcfunc = None

# check settings
def option(lang, opt):
    return lightproof_handler_la.get_option(lang.Language + "_" + lang.Country, opt)

# filtering affix fields (ds, is, ts etc.)
def onlymorph(st):
    if st != None:
        st = re.sub(r"^.*(st:|po:)", r"\1", st) # keep last word part
        st = re.sub(r"\b(?=[dit][sp]:)","@", st) # and its affixes
        st = re.sub(r"(?<!@)\b\w\w:\w+","", st).replace('@','').strip()
    return st

# if the pattern matches all analyses of the input word, 
# return the last matched substring
def _morph(rLoc, word, pattern, all, onlyaffix):
    global analyses
    if word == None:
        return None
    if word not in analyses:
        x = spellchecker.spell(u"<?xml?><query type='analyze'><word>" + word + "</word></query>", rLoc, ())
        if not x:
            return None
        t = x.getAlternatives()
        if not t:
            t = [""]
        analyses[word] = t[0]
    a = analyses[word].split("</a>")[:-1]
    result = None
    p = re.compile(pattern)
    for i in a:
        if onlyaffix:
            i = onlymorph(i)
        result = p.search(i)
        if result:
            result = result.group(0)
            if not all:
                return result
        elif all:
            return None
    return result

def morph(rLoc, word, pattern, all=True):
    return _morph(rLoc, word, pattern, all, False)

def affix(rLoc, word, pattern, all=True):
    return _morph(rLoc, word, pattern, all, True)

def spell(rLoc, word):
    if word == None:
        return None
    return spellchecker.isValid(word, rLoc, ())

# get the tuple of the stem of the word or an empty array
def stem(rLoc, word):
    global stems
    if word == None:
        return []
    if not word in stems:
        x = spellchecker.spell(u"<?xml?><query type='stem'><word>" + word + "</word></query>", rLoc, ())
        if not x:
            return []
        t = x.getAlternatives()
        if not t:
            t = []
        stems[word] = list(t)
    return stems[word]

# get the tuple of the morphological generation of a word or an empty array
def generate(rLoc, word, example):
    if word == None:
        return []
    x = spellchecker.spell(u"<?xml?><query type='generate'><word>" + word + "</word><word>" + example + "</word></query>", rLoc, ())
    if not x:
        return []
    t = x.getAlternatives()
    if not t:
        t = []
    return list(t)

# get suggestions
def suggest(rLoc, word):
    global suggestions
    if word == None:
        return word
    if word not in suggestions:
        x = spellchecker.spell("_" + word, rLoc, ())
        if not x:
            return word
        t = x.getAlternatives()
        suggestions[word] = join(t, "\n")
    return suggestions[word]

# get the nth word of the input string or None
def word(s, n):
    a = re.match("(?u)( [-.\w%]+){" + str(n-1) + "}( [-.\w%]+)", s)
    if not a:
        return None
    return a.group(2)[1:]

# get the (-)nth word of the input string or None
def wordmin(s, n):
    a = re.search("(?u)([-.\w%]+ )([-.\w%]+ ){" + str(n-1) + "}$", s)
    if not a:
        return None
    return a.group(1)[:-1]

def calc(funcname, par):
    global calcfunc
    global SMGR
    if calcfunc == None:
        calcfunc = SMGR.createInstance( "com.sun.star.sheet.FunctionAccess")
        if calcfunc == None:
                return None
    return calcfunc.callFunction(funcname, par)

def proofread( nDocId, TEXT, LOCALE, nStartOfSentencePos, nSuggestedSentenceEndPos, rProperties ):
    global ignore
    aErrs = []
    s = TEXT[nStartOfSentencePos:nSuggestedSentenceEndPos]
    for i in get_rule(LOCALE):
        if i[0] and not str(i[0]) in ignore:
            for m in i[0].finditer(s):
              if not i[3] or eval(i[3]):
                aErr = uno.createUnoStruct( "com.sun.star.linguistic2.SingleProofreadingError" )
                aErr.nErrorStart        = nStartOfSentencePos + m.start(0) # nStartOfSentencePos
                aErr.nErrorLength       = m.end(0) - m.start(0)
                aErr.nErrorType         = PROOFREADING
                aErr.aRuleIdentifier    = str(i[0])
                iscap = (i[4] and m.group(0)[0:1].isupper())
                if i[1][0:1] == "=":
                        aErr.aSuggestions = tuple(cap(eval(i[1][1:]).split("\n"), iscap, LOCALE))
                else:
                        aErr.aSuggestions = tuple(cap(m.expand(i[1]).split("\n"), iscap, LOCALE))
                comment = i[2]
                if comment[0:1] == "=":
                        comment = eval(comment[1:])
                aErr.aShortComment      = comment.split("\n")[0]
                aErr.aFullComment       = comment.split("\n")[-1]
                aErr.aProperties        = ()
                aErrs = aErrs + [aErr]
    return tuple(aErrs)

def cap(a, iscap, rLoc):
    if iscap:
        for i in range(0, len(a)):
            if a[i][0:1] == "i":
                if rLoc.Language == "tr" or rLoc.Language == "az":
                    a[i] = u"\u0130" + a[i][1:]
                elif a[i][1:2] == "j" and rLoc.Language == "nl":
                    a[i] = "IJ" + a[i][2:]
                else:
                    a[i] = "I" + a[i][1:]
            else:
                a[i] = a[i].capitalize()
    return a

def get_rule(rLocale):
        module = rLocale.Language
        if rLocale.Country != "":
                module = module + "_" + rLocale.Country
        try:
                return langrule[module]
        except:
                try:
                        module = rLocale.Language
                        return langrule[module]
                except:
                        try:
                                d = __import__("lightproof_" + pkg)
                        except:
                                print "Error: missing language data: " + module
                                return None
        # compile regular expressions
        for i in d.dic:
                try:
                        if re.compile("[(][?]iu[)]").match(i[0]):
                                i += [True]
                                i[0] = re.sub("[(][?]iu[)]", "(?u)", i[0])
                        else:
                                i += [False]
                        i[0] = re.compile(i[0])
                except:
                        print "Lightproof: bad rule -- ", i[0]
                        i[0] = None
        langrule[module] = d.dic
        return langrule[module]

class Lightproof( unohelper.Base, XProofreader, XServiceInfo, XServiceName, XServiceDisplayName, XSupportedLocales):

    def __init__( self, ctx, *args ):
        global spellchecker
        global SMGR
        self.ctx = ctx
        self.ServiceName = "com.sun.star.linguistic2.Proofreader"
        self.ImplementationName = "org.openoffice.comp.pyuno.Lightproof." + pkg
        self.SupportedServiceNames = (self.ServiceName, )
        self.locales = []
        for i in locales:
            l = locales[i]
            self.locales += [Locale(l[0], l[1], l[2])]
        self.locales = tuple(self.locales)
        currentContext = uno.getComponentContext()
        SMGR = currentContext.ServiceManager
        spellchecker = SMGR.createInstanceWithContext("com.sun.star.linguistic2.SpellChecker", currentContext)
        lightproof_handler_la.load(currentContext)

    # XServiceName method implementations
    def getServiceName(self):
        return self.ImplementationName

    # XServiceInfo method implementations
    def getImplementationName (self):
                return self.ImplementationName

    def supportsService(self, ServiceName):
                return (ServiceName in self.SupportedServiceNames)

    def getSupportedServiceNames (self):
                return self.SupportedServiceNames

    # XSupportedLocales
    def hasLocale(self, aLocale):
        if aLocale in self.locales:
            return True
        for i in self.locales:
            if (i.Country == aLocale.Country or i.Country == "") and aLocale.Language == i.Language:
                return True
        return False

    def getLocales(self):
        return self.locales

    # XProofreader
    def isSpellChecker(self):
        return False

    def doProofreading(self, nDocId, rText, rLocale, nStartOfSentencePos, \
        nSuggestedSentenceEndPos, rProperties):
        aRes = uno.createUnoStruct( "com.sun.star.linguistic2.ProofreadingResult" )
        aRes.aDocumentIdentifier = nDocId
        aRes.aText = rText
        aRes.aLocale = rLocale
        aRes.nStartOfSentencePosition = nStartOfSentencePos
        aRes.nStartOfNextSentencePosition = nSuggestedSentenceEndPos
        l = rText[nSuggestedSentenceEndPos:nSuggestedSentenceEndPos+1]
        while l == " ":
            aRes.nStartOfNextSentencePosition = aRes.nStartOfNextSentencePosition + 1
            l = rText[aRes.nStartOfNextSentencePosition:aRes.nStartOfNextSentencePosition+1]
        if aRes.nStartOfNextSentencePosition == nSuggestedSentenceEndPos and l!="":
            aRes.nStartOfNextSentencePosition = nSuggestedSentenceEndPos + 1
        aRes.nBehindEndOfSentencePosition = aRes.nStartOfNextSentencePosition

        try:
            aRes.aErrors = proofread( nDocId, rText, rLocale, \
                nStartOfSentencePos, aRes.nBehindEndOfSentencePosition, rProperties)
        except:
            traceback.print_exc(file=sys.stdout)
            aRes.aErrors = ()
        aRes.aProperties = ()
        aRes.xProofreader = self
        return aRes

    def ignoreRule(self, rid, aLocale):
        global ignore
        ignore[rid] = 1

    def resetIgnoreRules(self):
        global ignore
        ignore = {}

    # XServiceDisplayName
    def getServiceDisplayName(self, aLocale):
        return "Lightproof Grammar Checker (" + pkg + ")"

g_ImplementationHelper = unohelper.ImplementationHelper()
g_ImplementationHelper.addImplementation( Lightproof, \
        "org.openoffice.comp.pyuno.Lightproof." + pkg,
        ("com.sun.star.linguistic2.Proofreader",),)

g_ImplementationHelper.addImplementation( lightproof_handler_la.LightproofOptionsEventHandler, \
        "org.openoffice.comp.pyuno.LightproofOptionsEventHandler." + pkg,
        ("com.sun.star.awt.XContainerWindowEventHandler",),)

def classical(wxx, w):
    wu = w.replace("v", "u")
    if wu == wxx[:len(wu)]:
        return w + wxx[len(wu) + 1:]
    if wu.capitalize() == wxx[:len(wu)]:
        return w.capitalize() + wxx[len(wu) + 1:]
    return suggest(wxx)
