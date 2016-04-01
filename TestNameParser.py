import re
from org.wikidata.wdtk.datamodel.helpers import Datamodel
from org.wikidata.wdtk.datamodel.helpers import ItemDocumentBuilder
from org.wikidata.wdtk.datamodel.helpers import ReferenceBuilder
from org.wikidata.wdtk.datamodel.helpers import StatementBuilder
from org.wikidata.wdtk.datamodel.interfaces import DatatypeIdValue
from org.wikidata.wdtk.datamodel.interfaces import EntityDocument
from org.wikidata.wdtk.datamodel.json.jackson import JacksonTermedStatementDocument
from org.wikidata.wdtk.datamodel.interfaces import ItemDocument
from org.wikidata.wdtk.datamodel.interfaces import ItemIdValue
from org.wikidata.wdtk.datamodel.interfaces import PropertyDocument
from org.wikidata.wdtk.datamodel.interfaces import PropertyIdValue
from org.wikidata.wdtk.datamodel.interfaces import Reference
from org.wikidata.wdtk.datamodel.interfaces import Statement
from org.wikidata.wdtk.datamodel.interfaces import StatementDocument
from org.wikidata.wdtk.datamodel.interfaces import StatementGroup

NEWITEM = ItemIdValue.NULL

def buildStatement(forItem, property, value, reference):
    if isinstance(reference, str): 
        if WD_QrefRE.sub(reference)==reference:
            refproperty = 'P248'
        ref = (ReferenceBuilder.newInstance()
                               .withPropertyValue(Datamodel.makeWikidataPropertyIdValue(refproperty),
                                                  Datamodel.makeWikidataItemIdValue(reference))
                               .build())
    else:
        ref = reference
    if isinstance(property, str): 
        if WD_PrefRE.sub(property)==property:
            prop = Datamodel.makeWikidataItemIdValue(property)
    else:
        prop = property
    if isinstance(value, str): 
        if WD_QrefRE.sub(value)==value:
            val = Datamodel.makeWikidataItemIdValue(value)
    else:
        val = value
    return (StatementBuilder.forSubjectAndProperty(forItem, prop)
                            .withValue(val)
                            .withReference(ref)
                            .build())

refDataItemProperty = Datamodel.makeWikidataPropertyIdValue("P248")
ubosListOfSchools = Datamodel.makeWikidataItemIdValue("Q22679902")
ubosReference = (ReferenceBuilder.newInstance()
                                 .withPropertyValue(refDataItemProperty, ubosListOfSchools)
                                 .build())
instanceOf = Datamodel.makeWikidataPropertyIdValue("P31")
operatedByProperty = Datamodel.makeWikidataPropertyIdValue("P137")
refUrlProperty = Datamodel.makeWikidataPropertyIdValue("P854")
administrativeRegionProperty = Datamodel.makeWikidataPropertyIdValue("P131")
coordinatesProperty = Datamodel.makeWikidataPropertyIdValue("P625")
countryProperty = Datamodel.makeWikidataPropertyIdValue("P17")

countryUgandaStatement = buildStatement(NEWITEM, countryProperty, Datamodel.makeWikidataItemIdValue("Q1036"), ubosReference)
primarySchoolStatement = buildStatement(NEWITEM, instanceOf, Datamodel.makeWikidataItemIdValue("Q9842"), ubosReference) 
nurserySchoolStatement = buildStatement(NEWITEM, instanceOf, Datamodel.makeWikidataItemIdValue("Q1076052"), ubosReference) 
secondarySchoolStatement = buildStatement(NEWITEM, instanceOf, Datamodel.makeWikidataItemIdValue("Q159334"), ubosReference) 
schoolStatement = buildStatement(NEWITEM, instanceOf, Datamodel.makeWikidataItemIdValue("Q3914"), ubosReference) 

churchOfUgandaStatement = buildStatement(NEWITEM, operatedByProperty, Datamodel.makeWikidataItemIdValue("Q1723759"), ubosReference) 
seventhDayAdventistsStatement = buildStatement(NEWITEM, operatedByProperty, Datamodel.makeWikidataItemIdValue("Q104319"), ubosReference) 
    
class NameParser():
    earlyChildDevelopmentRE = re.compile(r'''(?ux)
                                    \s                 # space
                                    [E](arly)*         # Early, but usually abbreviated to ECD
                                    \.*\s*             # Could be with . or spaces in between
                                    [Cc]*(hild)*       # Child
                                    \.*/*\s*
                                    [Dd](evelopment)*  # Development
                                    \.*\s              # may have a ., must have a space ''')
    muslimRE = re.compile(r'''(?ux)
                                   ([Mm]oslem |
                                    [Mm]uslim |
                                    [Ii]slam |
                                    Imam\s+ |
                                    Quran)''')
    schoolRE = (r'''(?ux)\.*/*\\*\s*([Ss](chool|chl|ch|c)\.*|Chool)''') # School abbreviated in various ways
    commonmisspellings = [
        (re.compile(r'''\s*&\s*'''),                                ' & '),
        (re.compile(r'''Ii'''),                                     'II'),
        (re.compile(r'''Iii'''),                                    'III'),
        (re.compile(r'''Micheal'''),                                'Michael'),
        (re.compile(r'''Magdalane'''),                              'Magdalena'),
        (re.compile(r'''clare'''),                                  'Clare'),
        (re.compile(r'''Lawrance'''),                               'Lawrence'),
        (re.compile(r'''Domnic'''),                                 'Dominic'),
        (re.compile(r'''Matyr'''),                                  'Martyr'),
        (re.compile(r'''Aloysious'''),                              'Aloysius'),
        (re.compile(r'''S[ae]cre[dt]\s+Heart'''),                   'Sacred Heart'),
        (re.compile(r'''Mor*dern'''),                               'Modern'),
        (re.compile(r'''Cntr'''),                                   'Center'),
        (re.compile(r'''Acc*ademy'''),                              'Academy'),
        (re.compile(r'''Telet[au]bb*ies'''),                        'Teletubbies'),
        (re.compile(r'''(?uxi)buss*iness*'''),                      'Business'),
        (re.compile(r'''(?uxi)\sPrep(\.|aratory)*\s''' + schoolRE), ' Preparatory School'),
        (re.compile(r'''(?uxi)\sN(ur|ursery)*/\s*Pr*(im|imary)*''' + schoolRE),
                                                                    ' Nursery and Primary School'),
        (re.compile(r'''Intern*ational'''),                         'International'),
        (re.compile(r'''Intergrated'''),                            'Integrated'),
        (re.compile(r'''Juniour'''),                                'Junior'),
        (re.compile(r'''Sheph*[ea]rd'''),                           'Shepherd'),
        (re.compile(r'''^Saintt*\s'''),                             'Saint '),
        (re.compile(r'''^S[tT][\.|\s]*'''),                         'Saint '),
        (re.compile(r"""(?uxi)(Queen       |
                               King        |
                               Peter       |
                               Michael     |
                               Mary        |
                               Clare       |
                               Steven      |
                               Martyr      |
                               Andrew
							   )s'*"""),                            lambda pat: pat.group(1) + "'s"),
        (re.compile(r'''(?ux)^(Saint)      # fix wrong replacement of St to Saint
                        \s+
                        (A[nr]dard         # Standard, quite a few were apparently Stardard
                        |Arch              # Starch
                        |Ate               # State
                        |Ar                # Star
                        |Ep                # Step
                        |One               # Stone
                        |Ephen             # Stephen
                        )\s'''),                                    lambda pat: 'St' + pat.group(2).lower()+ ' '),
        (re.compile(r'''Stardard'''),                               'Standard'), # quite a few were apparently Stardard
        (re.compile(r'''\bR\.*C\.*C\.*\b'''),                       'Roman Catholic Church'), #RCC or R.C.C.
        (re.compile(r'''\bR\.*C\.*\b'''),                           'Roman Catholic'),        #RC  or R.C.
        (re.compile(r'''(?ux)
                        \b              # word boundary
                        [Ss](eventh)*   # Seventh, could be abbreviated
                        \.*\s*-*        # may have a . or a space or a dash
                        [Dd](ay)*       # Day, could be abbreviated
                        \.*\s*          # may have a . or a space
                        [Aa](dventist)* # Adventist, could be abbreviated
                        \.*\b           # may have a ., must end at word boundary '''),
                                                                    'Seventh-day Adventist'),    #SDA, S.D.A., etc
        (re.compile(r'''(?ux)
                        \b              # word boundary
                        [Cc](hurch)*    # Church, but can also be abbreviated as C/U or CoU
                        \.*\s*          # or C.O.U.
                        ([Oo]f*|/)*     # of is not necessarily present
                        \.*\s*
                        [Uu](ganda)*    # Uganda, may be abbreviated
                        \.*\b           # may have a ., must end at word boundary '''),
                                                                    'Church of Uganda'),
        (re.compile(r'''Stelizabeth'''),                            'Saint Elizabeth'),
        (re.compile(r'''^Devine'''),                                'Divine'),
        (re.compile(r'''Quaran'''),                                 'Quran'),
        (re.compile(r'''Bourding'''),                               'Boarding'),
        (re.compile(r'''Coolege'''),                                'College'),
        (re.compile(r'''HighWay'''),                                'Highway'),
        (re.compile(r'''(?uxi)\sP\.*S\.(\s|$)'''),
                                                                    ' Primary School '),
        (re.compile(r'''(?uxi)\sP(r*\\*(i|im|ima[rc]*y|mary)*|\.)\s'''),
                                                                    ' Primary '),
        (re.compile(r'''(?uxi)\s((S(chool|chl|ch|c)\.*)|Chool)'''),
                                                                    ' School '),
        (re.compile(r'''(?uxi)\bS(\.*|\s*)S\b\.*-*'''),             'Secondary School '),
        (re.compile(r'''(^\s+|\s+$)'''),                            ''),
        (re.compile(r'''(\s\s+)'''),                                ' '),
        ]

    primarySchoolRE = re.compile(r'''(?ux)\sPrimary''')
    secondarySchoolRE = re.compile(r'''(?ux)\s[Ss]e*\\*(conda*ry)*''' + schoolRE) # Secondary School abbreviated in various ways
    kindergartenRE = re.compile(r'''(?ux)\sKind[ea]rgar*ten''')
    nurserySchoolRE = re.compile(r'''(?ux)\s[Nn](\.|urs[ea]ry)*\s''')
    nurseryAndPrimarySchoolRE = re.compile(r'''(?ux)\sNursery\s(and|&)\sPrimary\s''' + schoolRE)
    capitaliseAllButShortWordsRE = re.compile(r"""(?ux)
                                     (?P<startOfStringOrSpace>^|\s)
                                     (?P<word>\S+)
                                      """)
    def capitaliseAllButShortWords(self, m):
        lowerWord = m.group('word').lower()
        #print lowerWord
        if lowerWord in ['and','or','of','for','the']:
            return m.group('startOfStringOrSpace') + lowerWord
        else:
            return m.group('startOfStringOrSpace') + m.group('word')[0].upper() + m.group('word')[1:]

    def __init__(self, name):
        self.tagsToSet = {'name': name}
        self.extraWDStatements = []
        self.level = ''
    def parse(self):
        name = self.capitaliseAllButShortWordsRE.sub(self.capitaliseAllButShortWords, self.tagsToSet['name'])
        for subRE,repl in self.commonmisspellings:
            name=subRE.sub(repl,name)
            #print name, repl
        #print 'after substitions:', name
        if 'Seventh-day Adventist' in name:
            self.tagsToSet['operator'] = 'Seventh-day Adventist Church'
            self.tagsToSet['operator:wikidata'] = 'Q104319'
            self.tagsToSet['religion'] = 'christian'
            self.tagsToSet['denomination'] = 'adventist'
            self.extraWDStatements.append(seventhDayAdventistsStatement)

        if 'Church of Uganda' in name:
            self.tagsToSet['operator'] = 'Church of Uganda'
            self.tagsToSet['operator:wikidata'] = 'Q1723759'
            self.tagsToSet['religion'] = 'christian'
            self.tagsToSet['denomination'] = 'anglican'
            self.extraWDStatements.append(churchOfUgandaStatement)

        if self.muslimRE.search(name):
            self.tagsToSet['religion'] = 'muslim'

        if 'Roman Catholic' in name:
            self.tagsToSet['religion'] = 'christian'
            self.tagsToSet['denomination'] = 'roman_catholic'
        elif 'Catholic' in name:
            self.tagsToSet['religion'] = 'christian'
            self.tagsToSet['denomination'] = 'catholic'
        elif 'Christian' in name:
            self.tagsToSet['religion'] = 'christian'

        name = self.earlyChildDevelopmentRE.sub(' Early Childhood Development  ', name)
        if self.earlyChildDevelopmentRE.search(name):
            self.tagsToSet['operator'] = 'Early Childhood Development'

        name = self.nurserySchoolRE.sub(' Nursery ', name)
        name = self.kindergartenRE.sub(' Kindergarten', name)
        print 'before level: ', name
        if self.nurseryAndPrimarySchoolRE.search(name) or ((self.nurserySchoolRE.search(name) or self.kindergartenRE.search(name)) and self.primarySchoolRE.search(name)):
            self.extraWDStatements.extend([primarySchoolStatement, nurserySchoolStatement])
            self.tagsToSet['isced:level'] = '0;1'
            self.level = 'nursery and primary '
        elif self.nurserySchoolRE.search(name) or self.kindergartenRE.search(name):
            self.extraWDStatements.append(nurserySchoolStatement)
            self.tagsToSet['isced:level'] = '0'
            self.level = 'nursery '
        elif self.primarySchoolRE.search(name):
            self.extraWDStatements.append(primarySchoolStatement)
            self.tagsToSet['isced:level'] = '1'
            self.level = 'primary '
        name = self.secondarySchoolRE.sub(' Secondary School', name)
        if self.secondarySchoolRE.search(name):
            self.extraWDStatements.append(secondarySchoolStatement)
            self.tagsToSet['isced:level'] = '2;3;4'
            self.level = 'secondary '
        self.tagsToSet['name'] = name.replace('  ',' ')
        #self.extraWDStatements.append(schoolStatement)
        #self.tagsToSet['isced:level'] = ''; level = ''

        return self.tagsToSet, self.extraWDStatements, self.level
        
io = [('Intergrated High School',                     ({'name': u'Integrated High School'}, [], '')),
      #('Ecole Française "Les Grands Lacs"',           ({'name': u'École Française "Les Grands Lacs"'}, [], '')),
      ('Progressive Juniour School',                  ({'name': u'Progressive Junior School'}, [], '')),
      ('Parriet Prep School',                         ({'name': u'Parriet Preparatory School'}, [], '')),
      ('Daycare Cntr',                                ({'name': u'Daycare Center'}, [], '')),
      ('Volcano Accademy',                            ({'name': u'Volcano Academy'}, [], '')),
      ('makerere bussines school',                    ({'name': u'Makerere Business School'}, [], '')),
      ('Namirembe Kindargarten',                      ({'isced:level': '0', 'name': u'Namirembe Kindergarten'},
                                                      [nurserySchoolStatement], 'nursery ')),
      ("Teletabies Infant School",                    ({'name': u"Teletubbies Infant School"}, [], '')),
     # ("light doves Pre- School and Kindergaten",     ({'name': u"Light Doves Preschool and Kindergarten"}, [], '')),
      ('St Jude Primary School',                      ({'isced:level': '1', 'name': u'Saint Jude Primary School'},
                                                      [primarySchoolStatement], 'primary ')),
      ("Saint Micheal Primary School",                ({'isced:level': '1', 'name': u"Saint Michael Primary School"},
                                                      [primarySchoolStatement], 'primary ')),
      ("Saint Peters Secondary School",               ({'isced:level': '2;3;4', 'name': u"Saint Peter's Secondary School"},
                                                      [secondarySchoolStatement], 'secondary ')),
      ("Great Shephard Primary School",               ({'isced:level': '1', 'name': u"Great Shepherd Primary School"},
                                                      [primarySchoolStatement], 'primary ')),
      ("Great Sheperd Primary School",                ({'isced:level': '1', 'name': u"Great Shepherd Primary School"},
                                                      [primarySchoolStatement], 'primary ')),
      ("Good Shepard Unique Primary School",          ({'isced:level': '1', 'name': u"Good Shepherd Unique Primary School"},
                                                      [primarySchoolStatement], 'primary ')),
      ##("KyomukamaPrimary School",                     ({'isced:level': '1', 'name': u"Kyomukama Primary School"},
      ##                                                [primarySchoolStatement], 'primary ')),
      ("Secret Heart Nursery and Primary School",     ({'isced:level': '0;1', 'name': u"Sacred Heart Nursery and Primary School"},
                                                      [primarySchoolStatement, nurserySchoolStatement], 'nursery and primary ')),
      ("Crane Nursary And Primary School",            ({'isced:level': '0;1', 'name': u"Crane Nursery and Primary School"},
                                                      [primarySchoolStatement, nurserySchoolStatement], 'nursery and primary ')),
      ("Akuoro Nursery& Primary school",              ({'isced:level': '0;1', 'name': u"Akuoro Nursery & Primary School"},
                                                      [primarySchoolStatement, nurserySchoolStatement], 'nursery and primary ')),
      ("Victory Primay School",                       ({'isced:level': '1', 'name': u"Victory Primary School"},
                                                      [primarySchoolStatement], 'primary ')),
      ("Nakatwe Primacy School",                      ({'isced:level': '1', 'name': u"Nakatwe Primary School"},
                                                      [primarySchoolStatement], 'primary ')),
      ##('King David high school',                      ({'name': u'King David High school'}, [], '')),
      ('Kings way nursery school',                    ({'isced:level': '0', 'name': u"King's Way Nursery School"},
                                                      [nurserySchoolStatement], 'nursery ')),
      ("Delhi Public School Interational",            ({'name': u"Delhi Public School International"}, [], '')),
      ("Divine Mercy Primary chool",                  ({'isced:level': '1', 'name': u"Divine Mercy Primary School"},
                                                      [primarySchoolStatement], 'primary ')),
      ("Devine Care Primary School",                  ({'isced:level': '1', 'name': u"Divine Care Primary School"},
                                                      [primarySchoolStatement], 'primary ')),
      ("Grace Mixed Day and Bourding Primary School", ({'isced:level': '1', 'name': u"Grace Mixed Day and Boarding Primary School"},
                                                      [primarySchoolStatement], 'primary ')),
      ("Okangali Pri School",                         ({'isced:level': '1', 'name': u"Okangali Primary School"},
                                                      [primarySchoolStatement], 'primary ')),
      ("Gogonyo Mordern Primary School",              ({'isced:level': '1', 'name': u"Gogonyo Modern Primary School"},
                                                      [primarySchoolStatement], 'primary ')),
      ("Agurur Ii Primary School",                    ({'isced:level': '1', 'name': u"Agurur II Primary School"},
                                                      [primarySchoolStatement], 'primary ')),
      ("Queens Way Primary School",                   ({'isced:level': '1', 'name': u"Queen's Way Primary School"},
                                                      [primarySchoolStatement], 'primary ')),
      #("Odikai Nursery And Primary Teachers Coolege", ({'isced:level': '5', 'name': u"Odikai Nursery and Primary Teachers' College"},
      #                                                [], 'college ')),
      ("Muljibhai Madhvani College Wairaka",          ({'name': u"Muljibhai Madhvani College Wairaka"}, [], '')),
      ("HighWay Nursery and Primary School",          ({'isced:level': '0;1', 'name': u"Highway Nursery and Primary School"},
                                                      [primarySchoolStatement, nurserySchoolStatement], 'nursery and primary ')),
      ("Disney kindergaten",                          ({'isced:level': '0', 'name': u"Disney Kindergarten"},
                                                      [nurserySchoolStatement], 'nursery ')),
      ("Wiggins Prmary School",                       ({'isced:level': '1', 'name': u"Wiggins Primary School"},
                                                      [primarySchoolStatement], 'primary ')),
      ("Devine secondry school",                      ({'isced:level': '2;3;4', 'name': u"Divine Secondary School"},
                                                      [secondarySchoolStatement], 'secondary ')),
      ("Busanza P.S.",                                ({'isced:level': '1', 'name': u"Busanza Primary School"},
                                                      [primarySchoolStatement], 'primary ')),
      ('Child Of Hope P.S.',                          ({'isced:level': '1', 'name': u'Child of Hope Primary School'},
                                                      [primarySchoolStatement], 'primary ')),
      ('St. Denis Ssebugwawo SS Ggaba',               ({'isced:level': '2;3;4',
                                                        'name': u'Saint Denis Ssebugwawo Secondary School Ggaba'},
                                                        [secondarySchoolStatement], 'secondary ')),
      ("St Marys Ss Mbale",                           ({'isced:level': '2;3;4',
                                                        'name': u"Saint Mary's Secondary School Mbale"},
                                                        [secondarySchoolStatement], 'secondary ')),
      ("St Denis Primary",                            ({'isced:level': '1', 'name': u"Saint Denis Primary"},
                                                      [primarySchoolStatement], 'primary ')),
      ("King David's SS-Aloet",                       ({'isced:level': '2;3;4',
                                                        'name': u"King David's Secondary School Aloet"},
                                                        [secondarySchoolStatement], 'secondary ')),
      ("Saint Ardard Primary School",                 ({'isced:level': '1', 'name': u"Standard Primary School"},
                                                      [primarySchoolStatement], 'primary ')),
     # ("Standrew's Primary School",                   ({'isced:level': '1', 'name': u"Saint Andrew's Primary School"},
     #                                                 [primarySchoolStatement], 'primary ')),
      #('St. Johns Junior School',                     ({'name': u"Saint John's Junior School"}, [], '')),
      ('Saint Ar Primary School',                     ({'isced:level': '1', 'name': u'Star Primary School'},
                                                      [primarySchoolStatement], 'primary ')),
      ('Saint Ar High Secondary School',              ({'isced:level': '2;3;4', 'name': u'Star High Secondary School'},
                                                      [secondarySchoolStatement], 'secondary ')),
      ('Saint Arch Factory Primary School',           ({'isced:level': '1', 'name': u'Starch Factory Primary School'},
                                                      [primarySchoolStatement], 'primary ')),
      ('Saint Ep Primary School',                     ({'isced:level': '1', 'name': u'Step Primary School'},
                                                      [primarySchoolStatement], 'primary ')),
      ('Saint Andard Primary School',                 ({'isced:level': '1', 'name': u'Standard Primary School'},
                                                      [primarySchoolStatement], 'primary ')),
      ('Saint One Primary School',                    ({'isced:level': '1', 'name': u'Stone Primary School'},
                                                      [primarySchoolStatement], 'primary ')),
      ('Saint Ephen Primary School',                  ({'isced:level': '1', 'name': u'Stephen Primary School'},
                                                      [primarySchoolStatement], 'primary ')),
      ('Saint Ate Of Wisdom Nursery And Primary School', ({'isced:level': '0;1',
                                                      'name': u'State of Wisdom Nursery and Primary School'},
                                                      [primarySchoolStatement, nurserySchoolStatement], 'nursery and primary ')),
      ('St. ',                                        ({'name': u'Saint'}, [], '')),
      ("Saint Joseph Of Nazareth High School",        ({'name': u"Saint Joseph of Nazareth High School"}, [], '')),
      ("St. Peters Primary School",                   ({'isced:level': '1', 'name': u"Saint Peter's Primary School"},
                                                      [primarySchoolStatement], 'primary ')),
      ("ST. Andrews Church Primary school",           ({'isced:level': '1', 'name': u"Saint Andrew's Church Primary School"},
                                                      [primarySchoolStatement], 'primary ')),
      ("Saintt Mugagga Primary School",               ({'isced:level': '1', 'name': u"Saint Mugagga Primary School"},
                                                      [primarySchoolStatement], 'primary ')),
      ("Saint Mary's Magdalane Girl's Secondary School", ({'isced:level': '2;3;4', 'name': u"Saint Mary's Magdalena Girl's Secondary School"},
                                                      [secondarySchoolStatement], 'secondary ')),
      ("Saint Marys' Kibwona Primary School",         ({'isced:level': '1', 'name': u"Saint Mary's Kibwona Primary School"},
                                                      [primarySchoolStatement], 'primary ')),
      ("St.Clare Girls Primary School",               ({'isced:level': '1', 'name': u"Saint Clare Girls Primary School"},
                                                      [primarySchoolStatement], 'primary ')),
      ("St.clares Girls High School",                 ({'name': u"Saint Clare's Girls High School"}, [], '')),
     ## ("Stelizabeth Day and Boarding Primary School", ({'isced:level': '1', 'name': u"Saint Elizabeth Day and Boarding Primary School"},
     ##                                                 [primarySchoolStatement], 'primary ')),
      ("Saint Stevens Nursery And Primary School",    ({'isced:level': '0;1', 'name': u"Saint Steven's Nursery and Primary School"},
                                                      [primarySchoolStatement, nurserySchoolStatement], 'nursery and primary ')),
      ("Saint Aloysious Primary School",              ({'isced:level': '1', 'name': u"Saint Aloysius Primary School"},
                                                      [primarySchoolStatement], 'primary ')),
      ("St.Domnic Petta Primary School",              ({'isced:level': '1', 'name': u"Saint Dominic Petta Primary School"},
                                                      [primarySchoolStatement], 'primary ')),
      ("St . Lawrence Secondary School",              ({'isced:level': '2;3;4', 'name': u"Saint Lawrence Secondary School"},
                                                      [secondarySchoolStatement], 'secondary ')),
      ("Saint Lawrance Secondary School",             ({'isced:level': '2;3;4', 'name': u"Saint Lawrence Secondary School"},
                                                      [secondarySchoolStatement], 'secondary ')),
      ('Mubya C/U Primary School',                    ({'isced:level': '1',
                                                        'operator:wikidata': 'Q1723759',
                                                        'operator': 'Church of Uganda',
                                                        'religion': 'christian',
                                                        'denomination': 'anglican',
                                                        'name': u'Mubya Church of Uganda Primary School'},
                                                        [churchOfUgandaStatement, primarySchoolStatement], 'primary ')),
       ('Nanyonyi C/u Primary School',                 ({'isced:level': '1',
                                                        'operator:wikidata': 'Q1723759',
                                                        'operator': 'Church of Uganda',
                                                        'religion': 'christian',
                                                        'denomination': 'anglican',
                                                        'name': u'Nanyonyi Church of Uganda Primary School'},
                                                        [churchOfUgandaStatement, primarySchoolStatement], 'primary ')),
       ('Kibwe Cou Primary School',                    ({'isced:level': '1',
                                                        'operator:wikidata': 'Q1723759',
                                                        'operator': 'Church of Uganda',
                                                        'religion': 'christian',
                                                        'denomination': 'anglican',
                                                        'name': u'Kibwe Church of Uganda Primary School'},
                                                        [churchOfUgandaStatement, primarySchoolStatement], 'primary ')),
       ('Kiryandongo C.O.U Primary School',            ({'isced:level': '1',
                                                        'operator:wikidata': 'Q1723759',
                                                        'operator': 'Church of Uganda',
                                                        'religion': 'christian',
                                                        'denomination': 'anglican',
                                                        'name': u'Kiryandongo Church of Uganda Primary School'},
                                                        [churchOfUgandaStatement, primarySchoolStatement], 'primary ')),

      ("Uganda Matyr's Minor Seminary",               ({'name': u"Uganda Martyr's Minor Seminary"}, [], '')),

      ("Destiny Christian High School",               ({'religion': 'christian',
                                                        'name': u"Destiny Christian High School"}, [], '')),
      ("Buyodi Catholic Primary School",              ({'isced:level': '1',
                                                        'religion': 'christian',
                                                        'denomination': 'catholic',
                                                        'name': u"Buyodi Catholic Primary School"},
                                                        [primarySchoolStatement], 'primary ')),
      ("Irima Roman Catholic Primary School",         ({'isced:level': '1',
                                                        'religion': 'christian',
                                                        'denomination': 'roman_catholic',
                                                        'name': u"Irima Roman Catholic Primary School"},
                                                        [primarySchoolStatement], 'primary ')),
      ("Mwelelwe RCC Primary School",                 ({'isced:level': '1',
                                                        'religion': 'christian',
                                                        'denomination': 'roman_catholic',
                                                        'name': u"Mwelelwe Roman Catholic Church Primary School"},
                                                      [primarySchoolStatement], 'primary ')),
      ("Koome Buyana RC Primary School",              ({'isced:level': '1',
                                                        'religion': 'christian',
                                                        'denomination': 'roman_catholic',
                                                        'name': u"Koome Buyana Roman Catholic Primary School"},
                                                      [primarySchoolStatement], 'primary ')),

      ('Bushika SDA Primary School',                  ({'isced:level': '1',
                                                        'religion': 'christian',
                                                        'denomination': 'adventist',
                                                        'operator:wikidata': 'Q104319',
                                                        'operator': 'Seventh-day Adventist Church',
                                                        'name': u'Bushika Seventh-day Adventist Primary School'},
                                                      [seventhDayAdventistsStatement, primarySchoolStatement], 'primary ')),
      ('Bushika S.D.A Nursery And Primary School',    ({'isced:level': '0;1',
                                                        'religion': 'christian',
                                                        'denomination': 'adventist',
                                                        'operator:wikidata': 'Q104319',
                                                        'operator': 'Seventh-day Adventist Church',
                                                        'name': u'Bushika Seventh-day Adventist Nursery and Primary School'},
                                                      [seventhDayAdventistsStatement, primarySchoolStatement, nurserySchoolStatement], 'nursery and primary ')),
      ('Kabatsi Sda Primary School',                  ({'isced:level': '1',
                                                        'religion': 'christian',
                                                        'denomination': 'adventist',
                                                        'operator:wikidata': 'Q104319',
                                                        'operator': 'Seventh-day Adventist Church',
                                                        'name': u'Kabatsi Seventh-day Adventist Primary School'},
                                                      [seventhDayAdventistsStatement, primarySchoolStatement], 'primary ')),
      ('Mpodwe Seventh Day Adventist Primary School', ({'isced:level': '1',
                                                        'religion': 'christian',
                                                        'denomination': 'adventist',
                                                        'operator:wikidata': 'Q104319',
                                                        'operator': 'Seventh-day Adventist Church',
                                                        'name': u'Mpodwe Seventh-day Adventist Primary School'},
                                                      [seventhDayAdventistsStatement, primarySchoolStatement], 'primary ')),

     # ("Ishaka Adventist College",                    ({'name': u"Ishaka Adventist College"}, [], '')),
     # ("Matinza Baptist Primary School",              ({'isced:level': '1', 'name': u"Matinza Baptist Primary School"},
     #                                                 [primarySchoolStatement], 'primary ')),

      ("Luweero Islamic Primary School",              ({'isced:level': '1',
                                                        'religion': 'muslim',
                                                        'name': u"Luweero Islamic Primary School"},
                                                      [primarySchoolStatement], 'primary ')),
      ("Rwibaare Muslim Primary School",              ({'isced:level': '1',
                                                        'religion': 'muslim',
                                                        'name': u"Rwibaare Muslim Primary School"},
                                                      [primarySchoolStatement], 'primary ')),
      ('Lukabazi Muslim Primary School',              ({'isced:level': '1',
                                                        'religion': 'muslim',
                                                        'name': u'Lukabazi Muslim Primary School'},
                                                      [primarySchoolStatement], 'primary ')),
      ('Lango Quran Primary School',                  ({'isced:level': '1',
                                                        'religion': 'muslim',
                                                        'name': u'Lango Quran Primary School'},
                                                      [primarySchoolStatement], 'primary ')),
      ('Lango Quaran Primary School',                 ({'isced:level': '1',
                                                        'religion': 'muslim',
                                                        'name': u'Lango Quran Primary School'},
                                                      [primarySchoolStatement], 'primary ')),
      ('Tamula Moslem Primary School',                ({'isced:level': '1',
                                                        'religion': 'muslim',
                                                        'name': u'Tamula Moslem Primary School'},
                                                      [primarySchoolStatement], 'primary ')),
     # ("YMCA Mbale Vocation Institute",               ({'name': u"YMCA Mbale Vocation Institute"}, [], '')),
     # ("Young Men's Christian Association",           ({'name': u"Young Men's Christian Association"}, [], '')),
     # ("Ntungamo Polytechnic",                        ({'name': u"Ntungamo Polytechnic"}, [], '')),

      #('Lira School of Nursing and Midwifery',        ({'name': u''}, [], '')),
      #('Institute Of Health Promotion & Training School Of Nursing', ({'name': u'Institute of Health Promotion & Training School Of Nursing'}, [], '')),
      #('Institute Of Nursing Teaching and Vocational Studies', ({'name': u''}, [], '')),
      #('Onenga Nurses Training Academy',              ({'name': u'Onenga Nurses Training Academy'}, [], '')),

     # ("Good Samaritan Orphanage School",             ({'name': u"Good Samaritan Orphanage School"}, [], '')),
      ("Mission Orphan Nursery And Primary School",   ({'isced:level': '0;1', 'name': u"Mission Orphan Nursery and Primary School"},
                                                      [primarySchoolStatement, nurserySchoolStatement], 'nursery and primary ')),
      ("Mbale School Of The Deaf Day and Boarding Secondary School", ({'isced:level': '2;3;4', 'name': u"Mbale School of the Deaf Day and Boarding Secondary School"},
                                                      [secondarySchoolStatement], 'secondary ')),
      ("Nancy School For The Deaf",                   ({'name': u"Nancy School for the Deaf"}, [], '')),
     # ("Nabumali Training and Resource Centre for the Blind", ({'name': u"Nabumali Training and Resource Centre for the Blind"}, [], '')),
     # ("Alito Leper Primary School",                  ({'isced:level': '1', 'name': u"Alito Leper Primary School"},
     #                                                 [primarySchoolStatement], 'primary ')),

     # ("BISHOP CIPRIANO KIHANGIRE S.S",               ({'isced:level': '2;3;4', 'name': u"Bishop Cipriano Kihangire Secondary School"},
     #                                                 [secondarySchoolStatement], 'secondary ')),
     # ("Nelson Mandela Parents Primary School",       ({'isced:level': '1', 'name': u"Nelson Mandela Parents Primary School"},
     #                                                 [primarySchoolStatement], 'primary ')),
     # ("Saint Maria Goretti Secondary School",        ({'isced:level': '2;3;4', 'name': u"Saint Maria Goretti Secondary School"},
     #                                                 [secondarySchoolStatement], 'secondary ')),
     # ("Uganda Martyrs' Sembabule Secondary School",  ({'isced:level': '2;3;4', 'name': u"Uganda Martyrs' Sembabule Secondary School"},
     #                                                 [secondarySchoolStatement], 'secondary ')),
     # ("Dr. Aporu Okol Memorial Secondary School",    ({'isced:level': '2;3;4', 'name': u"Dr. Aporu Okol Memorial Secondary School"},
     #                                                 [secondarySchoolStatement], 'secondary ')),
     # ("Massimiliano Ochwa Memorial Secondary School",({'isced:level': '2;3;4', 'name': u"Massimiliano Ochwa Memorial Secondary School"},
     #                                                 [secondarySchoolStatement], 'secondary ')),
     # ("Abiasali Kuloba Memorial Vocation Institute", ({'name': u"Abiasali Kuloba Memorial Vocation Institute"}, [], '')),
     # ("AArc Bishop Jonathan Memorial College School",({'name': u"Arch Bishop Jonathan Memorial College School"}, [], '')),
     # ("Bishop Wandera Secondary School",             ({'isced:level': '2;3;4', 'name': u"Bishop Wandera Secondary School"},
     #                                                 [secondarySchoolStatement], 'secondary ')),
     # ("Louis Gregory Bahai Primary School",          ({'isced:level': '1', 'name': u"Louis Gregory Bahai Primary School"},
     #                                                 [primarySchoolStatement], 'primary ')),
     # ("Saint John Paul II College",                  ({'name': u"Saint John Paul II College"}, [], '')),
     # ("Saint John Paul II Memorial Secondary School",({'isced:level': '2;3;4', 'name': u"Saint John Paul II Memorial Secondary School"},
     #                                                 [secondarySchoolStatement], 'secondary ')),
     # ("Sir Samuel Baker Secondary School",           ({'isced:level': '2;3;4', 'name': u"Sir Samuel Baker Secondary School"},
     #                                                 [secondarySchoolStatement], 'secondary ')),
     # ("Mweeya Sengendo Memorial Primary School",     ({'isced:level': '1', 'name': u"Mweeya Sengendo Memorial Primary School"},
     #                                                 [primarySchoolStatement], 'primary ')),
     # ("John Kennedy Memorial School",                ({'name': u"John Kennedy Memorial School"}, [], '')),
      ("Joyce Sebuliba Memorial Primary School",      ({'isced:level': '1', 'name': u"Joyce Sebuliba Memorial Primary School"},
                                                      [primarySchoolStatement], 'primary ')),
     # ("Archibishop Yona Okoth Memorial Primary School", ({'isced:level': '1', 'name': u"Archbishop Yona Okoth Memorial Primary School"},
     #                                                 [primarySchoolStatement], 'primary ')),
     # ("Albert Cook Memorial Medical Laboratory Institute", ({'name': u"Albert Cook Memorial Medical Laboratory Institute"}, [], '')),
     # ("Joan Jordan Memorial School",                 ({'name': u"Joan Jordan Memorial School"}, [], '')),
     ]
noProblem = True
for input, output in io:
    print input
    if NameParser(input).parse() != output:
        print NameParser(input).parse()
        print output
        print
        noProblem = False
if noProblem: print 'All tests passed OK'
