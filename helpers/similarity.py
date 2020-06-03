#!/usr/local/bin/python
# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import absolute_import
from builtins import str
from builtins import map
from builtins import range
from builtins import object
from past.utils import old_div
import re
import difflib
from difflib import SequenceMatcher
import Levenshtein
from common import PREFIXES, coerce_to_unicode, to_ascii,remove_stopwords

def split(s):
    return re.split('[ |\-]*', s)

class Similarity(object):
    def __init__(self):
        pass

    def levenshtein_ratio(self, a,b):
        "Calculates the Levenshtein distance between a and b."
        return Levenshtein.ratio(a,b)

    def levenshtein_ratio2(self, a, b):
        d = Levenshtein.distance(a, b)
        return 1.0 - (float(d)/10.0)
    def to_ascii(self, s):
        d = to_ascii
        s = str(s)
        for k in list(d.keys()):
            s = s.replace(k, d[k])
        return s

    def average_distance(self, l1, l2, distance_function=None):
        """the average distance of the words in l1 and l2
        use the distance function to compute distances between words in l1 and l2
        return the average distance of the highest scores for each of the words from both lists

        i.e.:
        average_disatnce(['n1a', 'n1b'], ['n2'])
        is the average of :
            max(d(n1a, n2))
            max(d(n1b, n2))
            max(d(n2, n1a), d(n2,n1b))

        average_disatnce(['n1a', 'n1b'], ['n2a', 'n2b'])
        is the average of:
            max(d(n1a, n2a), d(n1a, n2b))
            max(d(n1b, n2a), d(n1b, n2b))
            max(d(n2a, n1a), d(n2a,n1b))
            max(d(n2b, n1a), d(n2a,n1b))

        """
        if not distance_function:
            distance_function = self.levenshtein_ratio
        teller = 0.0
        noemer = 0.0
#       assert l1
#       assert l2, str(l1 + l2)
        #compuate array of values
        if not l1 or not l2:
            return 1.0
        #make l1 the shortes

        l1, l2 =len(l1)<len(l2) and (l1, l2) or (l2, l1)

        #compute the distrances
        distances = []
        for s1 in l1:
            ls = [(distance_function(s1, s2), s2) for s2 in l2]
            ls.sort(reverse=True)
            distances.append((ls, s1))
        distances.sort(reverse=True)
        #compuate maxima for each colum and each row
        done = []
        for ls, s1 in distances:
            for d, s2 in ls:
                if s2 not in done:
                    done.append(s2)
                    teller += d
                    noemer += 1
                    break

        #if there is a difference in length, we penalize for each item
        for i in range(len(l2) - len(l1)):
            teller += .9
            noemer += 1
#        for s1 in l1:
#            max[s1] =
#           teller += max([d[s1][s] for s in d[s1].keys()])
#          noemer += 1
#     for s2 in l2:
#        teller += max([d[s][s2] for s in d.keys()])
#       noemer += 1
        return old_div(teller,noemer)

    def ratio(self,n1,n2, explain=0):
        """Combine several parameters do find a similarity ratio"""

        weight_normal_form =  3.0 #distance between soundexes of normal form
        weight_normal_form_if_one_name_is_in_initials = old_div(weight_normal_form, 4) #distance between soundexes of normal form
        weight_normal_form_soundex =  9.0 #average distance between soundexes of normal form
        weight_normal_form_soundex_if_one_name_is_in_initials =old_div(weight_normal_form_soundex,4) #distance between soundexes of normal form
        weight_geslachtsnaam1 = 7.0 #distance between soundexes of geslachtsnamen
        weight_geslachtsnaam2 = 7.0 #distance between geslachtsnaam
        weight_initials =  2 #distance between initials
        weight_initials_if_one_name_is_in_initials =  weight_initials * 2 #distance between initials if one of the names is in intials
            #(for example, "A.B Classen")


        ### NORMAL FORM

        nf1 = n1.guess_normal_form()
        nf2 = n2.guess_normal_form()
        #remove diacritics
        nf1 = to_ascii(nf1)
        nf2 = to_ascii(nf2)

#        ratio_normal_form = self.levenshtein_ratio(nf1, nf2)
        ratio_normal_form = self.average_distance(split(nf1), split(nf2))
        #create a simkplified soundex set for this name
        #remove stopwords
        nf1 =remove_stopwords( nf1)
        nf2 = remove_stopwords( nf2)

        #l# = min(len(nf1.split()), len(nf2.split()))
        #nf1 = ' '.join(nf1.split()[:l])
        #nf2 = ' '.join(nf2.split()[:l])
        #we use the soundex_nl property of the name, so the property gets cached
        se1 = n1.soundex_nl(nf1, group=2, length=-1)
        se2 = n2.soundex_nl(nf2, group=2, length=-1)
        #make the nfs of the same length

        ratio_normal_form_soundex = self.average_distance( se1, se2)



        #gelachtsnaam wordt op twee manieren met elkaar vergeleken

        #de soundexes van de achternaam worden meegewoen
        g1 = n1.geslachtsnaam() #or n1.get_volledige_naam()
        g2 = n2.geslachtsnaam() #or n2.get_volledige_naam()
        g1 = to_ascii(g1)
        g2 = to_ascii(g2)
        g1_soundex = n1.soundex_nl(g1, group=2, length=-1)
        g2_soundex = n2.soundex_nl(g2, group=2, length=-1)
        ratio_geslachtsnaam1 = self.average_distance(g1_soundex, g2_soundex)

        #n de afstand van de woorden in de achtenraam zelf
        ratio_geslachtsnaam2 = self.average_distance(
             re.split('[ \.\,\-]', g1.lower()),
             re.split('[ \.\,\-]', g2.lower()),
             self.levenshtein_ratio)

        #count initials only if we have more than one
        #(or perhaps make this: if we know the first name)

        if len(n1.initials()) == 1 or len(n2.initials()) == 1:
            #initials count much less if there is only one
            weight_initials = 0
            ratio_initials = .5
        elif n1.contains_initials() or n2.contains_initials():
            ratio_initials = self.levenshtein_ratio(n1.initials().lower(), n2.initials().lower())
            weight_initials = weight_initials_if_one_name_is_in_initials
        elif len(n1.initials()) > 1 and len(n2.initials()) > 1:
            ratio_initials = self.levenshtein_ratio(n1.initials().lower(), n2.initials().lower())
        else:
            ratio_initials = 0.7

        if n1.contains_initials() or n2.contains_initials():
            weight_normal_form = weight_normal_form_if_one_name_is_in_initials
            weight_normal_form_soundex = weight_normal_form_soundex_if_one_name_is_in_initials

        try:
            teller = ratio_normal_form * weight_normal_form +  ratio_normal_form_soundex * weight_normal_form_soundex+ ratio_geslachtsnaam1*weight_geslachtsnaam1 + ratio_geslachtsnaam2*weight_geslachtsnaam2 +  ratio_initials*weight_initials
            noemer =  weight_normal_form  +  weight_normal_form_soundex + weight_initials + weight_geslachtsnaam1 + weight_geslachtsnaam2
            final_ratio = old_div(teller,noemer)

        except ZeroDivisionError:
            return 0.0
        if explain:
            d = [
            ('ratio_normal_form',ratio_normal_form,),
            ('weight_normal_form',weight_normal_form, ),
            ('ratio_geslachtsnaam1 (soundex)', ratio_geslachtsnaam1, ),
            ('weight_geslachtsnaam1', weight_geslachtsnaam1, ),
            ('ratio_geslachtsnaam2 (letterlijke geslachtsnaam)', ratio_geslachtsnaam2, ),
            ('weight_geslachtsnaam2', weight_geslachtsnaam2, ),
            ('ratio_initials', ratio_initials, ),
            ('weight_initials', weight_initials, ),
            ('final_ratio', final_ratio,),
            ('teller',teller,),
            ('noemer', noemer,),
            ]
            s = '-' * 100 + '\n'
            s += 'Naam1: %s [%s] [%s] %s\n' % (n1, n1.initials(), n1.guess_normal_form(), se1)
            s += 'Naam2: %s [%s] [%s] %s\n' % (n2, n2.initials(), n2.guess_normal_form(), se2)
            s += 'Similarity ratio: %s\n' % final_ratio
            s += '--- REASONS'  + '-' * 30 + '\n'
            format_s = '%-30s | %-10s | %-10s | %-10s | %-10s | %s-10s\n'
            s += format_s % ('\t  property', '  ratio', '  weight','relative_weight',  '  r*w', 'r * relative_w')
            s += '\t' + '-' * 100 + '\n'
            format_s = '\t%-30s | %-10f | %-10f | %-10f | %-10f | %-10f\n'
            s += format_s % (' normal_form', ratio_normal_form, weight_normal_form,old_div(weight_normal_form,teller), ratio_normal_form * weight_normal_form, old_div(ratio_normal_form * weight_normal_form,teller))
            s += format_s % ('soundex van normal_form', ratio_normal_form_soundex, weight_normal_form_soundex,old_div(weight_normal_form_soundex,teller), ratio_normal_form_soundex* weight_normal_form_soundex, old_div(ratio_normal_form_soundex * weight_normal_form_soundex,teller))
            s += format_s % ('soundex van geslachtsnaam1', ratio_geslachtsnaam1, weight_geslachtsnaam1,old_div(weight_geslachtsnaam1,teller), ratio_geslachtsnaam1 * weight_geslachtsnaam1, old_div(ratio_geslachtsnaam1 * weight_geslachtsnaam1,teller))
            s += format_s % ('geslachtsnaam', ratio_geslachtsnaam2, weight_geslachtsnaam2,old_div(weight_geslachtsnaam2,teller),  ratio_geslachtsnaam2 *weight_geslachtsnaam2 , old_div(ratio_geslachtsnaam2 * weight_geslachtsnaam2,teller))
            s += format_s % ('initials', ratio_initials, weight_initials, old_div(weight_initials,teller), ratio_initials *weight_initials, old_div(ratio_initials * weight_initials,teller))
            s += '\tTOTAL  (numerator)                                       | %s (counter = %s)\n' %  (teller, noemer)
            return s
            return '\n'.join(['%s: %s' % (k, v) for k,v in d])
        return final_ratio

    def explain_ratio(self, n1, n2):
        return self.ratio(n1, n1, explain=1)



GROUPS1 = (
            ('' ,['[^a-z]', 'en$']), #alleen alfabetische characters
#            ('', [r'^%s' % s for s in PREFIXES + ['h']]),

            ('.',['ah', 'eh','ij', 'a', 'e', 'i', 'o','u','y', r'\.\.\.', r'\.\.']),
            ('s',['z', 'ss', 'sch$']),
            ('p',['b', 'pp']),
            ('g',['ch', 'gg']),
            ('k',['q','kw', 'c', 'x', 'kk']),
            ('t',['d',  'tt']), #d, dt, tt, dd --> t
            ('f',['ph', 'v', 'w', 'ff']),
#            ('h',[]),
            ('l',['ll']),
            ('n',['m', 'nn']),
            ('r',['rh', 'rr'] ),
         #   ('', '1234567890')
)

GROUPS2 = (
            ('' ,['[^a-z]', 'en$', 'us$']), #alleen alfabetische characters
            ('' ,[r'\(', r'\)']),
            ('a',['ah', 'ae','aa',]),
            ('e',['ee', 'eh',]),
            ('i',['ie', 'ij', 'y', 'ei']),
            ('o',['oh', 'oo', ]),
            ('u',['ue', 'oe','uu', ]),
            ('ui',['uy', ]),
            ('s',['z', 'ss', 'sch$']),
            ('p',['b', 'pp']),
            ('g',['ch', 'gg']),
            ('k',['q','kw', 'c', 'x', 'kk', 'ks$']),
            ('t',['d',  'tt']), #d, dt, tt, dd --> t
            ('f',['ph', 'v', 'w', 'ff']),
#            ('h',[]),
            ('l',['ll']),
            ('n',['m', 'nn']),
            ('r',['rh', 'rr'] ),

#            ('', '1234567890')
)

GROUPS1 = [(k, re.compile('|'.join(ls))) for k, ls in GROUPS1]
GROUPS2 = [(k, re.compile('|'.join(ls))) for k, ls in GROUPS2]

def soundex_nl(s, length=4, group=1):
    """
    stab at giving names a simplified canonical form

    De truuk is een vorm te vinden zodat zoveel mogelijk 'gelijkvormige' namen
    dezelfde "soundex" krijgen...

    Er zijn verschillende "groepen"
        - groep 1: identificeer zoveel mogelijk
        - groep 2: identificeer wat minder

    lenght geeft the lengte van het resultaat aan. length = -1 geeft de hele string
    """
    s = s.lower()
    s = to_ascii(s)

    #strip of certain suffixes
#    for suffix, replacement in [
#        ('en', ''),
#        ('sch', 's'),
#        ]:
#        if s.endswith(suffix):
#            s = s[:-len(suffix)] + replacement
#            break

    #strip of certain prefixes
    for x in PREFIXES + ['h']:
        if s.startswith(x):
            s = s[len(x):]


    if group == 1:
        groups = GROUPS1
    elif group == 2:
        groups = GROUPS2

    else:
        raise Exception('"group" argument must be either 1 or 2')
    #THIS DOES LOST OF UNNCECESSARY STUFF

    if 1:
        #create a single regular expression
        for k, regexp in groups:
#            regexp = re.compile('|'.join(ls))
            s = regexp.sub(k, s)
            while regexp.search(s):
                s = regexp.sub(k, s)
    if 0:
        ls = []
        d = {}
        for k, l in groups:
            ls += l
            for x in l:
                d[x] = k
        s = multiple_replace(d, s)
    if 0:
        ls = []
        d = {}
        for k, l in groups:
            ls += l
            for x in l:
                d[x] = k


        to_replace =[]
        for x in ls:
            if re.search(x, s):
                to_replace.append(x)
        for x in to_replace:
            s = re.sub(x, d[x], s)
    if s.endswith('.'):
        s = s[:-1]
    if not s:
        s = '.'
    if length > 0:
        s = s[:length]
    s = str(s)
    return s

def multiple_replace(dict, text):
    """ Replace in 'text' all occurences of any key in the given
    dictionary by its corresponding value.  Returns the new tring."""

    # Create a regular expression  from the dictionary keys
    regex = re.compile("(%s)" % "|".join(map(re.escape, list(dict.keys()))))

    # For each match, look-up corresponding value in dictionary
    return regex.sub(lambda mo: dict[mo.string[mo.start():mo.end()]], text)
