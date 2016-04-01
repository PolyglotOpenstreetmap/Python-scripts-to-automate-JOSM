#!/bin/jython
'''

This code is released under the GNU General
Public License v2 or later.

The GPL v3 is accessible here:
http://www.gnu.org/licenses/gpl.html

The GPL v2 is accessible here:
http://www.gnu.org/licenses/old-licenses/gpl-2.0.html

It comes with no warranty whatsoever.

This code illustrates how to use Jython to:
* work with selected items or how to process all the primitives of a certain kind (node, way, relation)

'''
from javax.swing import JOptionPane
from org.openstreetmap.josm import Main
import org.openstreetmap.josm.command as Command
import org.openstreetmap.josm.data.projection.Projection as Projection
import org.openstreetmap.josm.data.osm.OsmPrimitive  as OsmPrimitive
import org.openstreetmap.josm.data.osm.Node as Node
import org.openstreetmap.josm.data.osm.Way as Way
import org.openstreetmap.josm.data.osm.Relation as Relation
import org.openstreetmap.josm.data.osm.TagCollection as TagCollection
import org.openstreetmap.josm.data.osm.DataSet as DataSet
import org.openstreetmap.josm.tools.Utils as Utils
import org.openstreetmap.josm.tools.OpenBrowser as OpenBrowser
import org.openstreetmap.josm.tools.HttpClient as HttpClient
import org.openstreetmap.josm.tools.Geometry as Geometry
import org.openstreetmap.josm.gui.preferences.advanced.PrefEntry as PrefEntry
import org.openstreetmap.josm.actions.search.SearchAction as SearchAction
# import org.openstreetmap.josm.actions.UploadSelectionAction as UploadSelectionAction
import org.openstreetmap.josm.data.osm.Changeset as Changeset
import org.openstreetmap.josm.tools.OpenBrowser as OpenBrowser
import java.net.URLEncoder as URLEncoder

import re, time, pprint, json

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
from org.wikidata.wdtk.wikibaseapi import ApiConnection
from org.wikidata.wdtk.util import WebResourceFetcherImpl
from org.wikidata.wdtk.wikibaseapi import ApiConnection
from org.wikidata.wdtk.wikibaseapi import LoginFailedException
from org.wikidata.wdtk.wikibaseapi import WikibaseDataEditor
from org.wikidata.wdtk.wikibaseapi import WikibaseDataFetcher
from org.wikidata.wdtk.wikibaseapi.apierrors import MediaWikiApiErrorException
from com.fasterxml.jackson.databind import ObjectMapper

def getMapView():
    if Main.main and Main.main.map:
        return Main.main.map.mapView
    else:
        return None

class BotSettings():
    USERNAME = Main.pref.get("wikidata.username")
    PASSWORD = Main.pref.get("wikidata.password")
    EDIT_AS_BOT = False


WD_QrefRE = re.compile(r'^([Qq]\d+)$')
WD_PrefRE = re.compile(r'^([Pp]\d+)$')

siteIri = ""
NEWITEM = ItemIdValue.NULL
mapper = ObjectMapper()

osm_account =        'Polyglot'
osm_import_account = 'Polyglot_Import'

dummyNode = Node()
dummyWay = Way()
dummyRelation = Relation()

class WbSearchEntitiesAction:
    def __init__(self, connection, siteUri):
        self.connection = connection
        self.siteIri = siteUri
    # def WbSearchEntities(properties):
        # return WbSearchEntities(self, properties.ids, properties.sites, properties.titles, properties.props, properties.languages, properties.sitefilter)

    def WbSearchEntities(self, searchString, props=None, language='en', sitefilter=None):
        parameters = {ApiConnection.PARAM_ACTION: "wbsearchentities"}

        if searchString == None:
            raise IllegalArgumentException("Please provide a string to search for")
        else:
            parameters["search"] = searchString

        if props:
            parameters["props"] = props

        if language:
            parameters["language"] = language

        if sitefilter:
            parameters["sitefilter"] = sitefilter

        parameters[ApiConnection.PARAM_FORMAT] = "json"

        itemDocuments = {}

        response = self.connection.sendRequest("POST",parameters)

        root = mapper.readTree(response)
        return json.loads(root.toString())

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
                               Andrew      |
                               Edward
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
        (re.compile(r'''(?uxi)\bR\.*C\.*C\.*\b'''),                 'Roman Catholic Church'), #RCC or R.C.C.
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
							
districtIds={}
mv = getMapView()

if mv and mv.editLayer and mv.editLayer.data:
    selectedElements = mv.editLayer.data.getSelected()
    
    if not(selectedElements):
        JOptionPane.showMessageDialog(Main.parent, "Please select an element")
    else:
        WebResourceFetcherImpl.setUserAgent("Polyglot's JOSM Bot based on WDTK")
        connection = ApiConnection.getWikidataApiConnection()
        wbde = WikibaseDataEditor(connection, siteIri)
        if (BotSettings.USERNAME != None):
            connection.login(BotSettings.USERNAME, BotSettings.PASSWORD)
        print "###################################################################3"
        print 'logged in: '+str(connection.loggedIn) + ' as '+connection.getCurrentUser()
        wbsea = WbSearchEntitiesAction(connection, siteIri)
        noNewSchools = True
        coordStatements = {}  
        for element in selectedElements:    
            if element.getType()==dummyNode.getType(): type='node'
            if element.getType()==dummyWay.getType(): type='way'
            if element.getType()==dummyRelation.getType(): type='relation'

            Q_school = ''; tagsToSet = {}; extraWDStatements = []

            housenumber = street = district = county = subcounty = parish = city = amenity = isced_level = operator_type = name = wikidata = admin_level = reltype = administrativeRegion = description = ''
            if element.hasKey('name'): name = str(element.get('name'))
            if (not(name) or 
                  name=='Primary School' or
                  name=='Secondary School' or
                  name=='Nursery School' or
                  name=='Vocational School' or
                  name=='School' or
                  name.find('rphanage')>0):
                print 'Skipping school with nondescript name'
                continue
            print name
            tagsToSet, extraWDStatements, level = NameParser(name).parse()
            name = tagsToSet['name']
            print name
            # t
            if element.hasKey('addr:housenumber'): housenumber = str(element.get('addr:housenumber'))
            if element.hasKey('addr:street'): street = str(element.get('addr:street'))
            if element.hasKey('addr:district'): district = str(element.get('addr:district'))
            if element.hasKey('addr:county'): county = str(element.get('addr:county'))
            if element.hasKey('addr:subcounty'): subcounty = str(element.get('addr:subcounty'))
            if element.hasKey('addr:parish'): parish = str(element.get('addr:parish'))
            if element.hasKey('addr:city'): city = str(element.get('addr:city'))
            if element.hasKey('amenity'): amenity = str(element.get('amenity'))
            if element.hasKey('isced:level'): isced_level = str(element.get('isced:level'))
            if element.hasKey('operator:type'): operator_type = str(element.get('operator:type'))
            if element.hasKey('wikidata'): wikidata = str(element.get('wikidata'))
            if element.hasKey('admin_level'): admin_level = str(element.get('admin_level'))
            if element.hasKey('type'): reltype = str(element.get('type'))
            if element.hasKey('created_by'): administrativeRegion = str(element.get('created_by'))
            print name
            print operator_type
            print isced_level
            print amenity
            print county
            print subcounty
            print district
            print parish
            print city
            print street + ' ' + housenumber
            print wikidata
            print admin_level
            print reltype
            print administrativeRegion

            if reltype == 'boundary':
                if admin_level == '4':
                    description = 'district of Uganda'
                    extraWDStatements.append(buildStatement(NEWITEM, instanceOf, "Q3539870", ubosReference))
                    extraWDStatements.append(buildStatement(NEWITEM, administrativeRegionProperty, administrativeRegion, ubosReference))
                elif admin_level == '6':
                    description = 'county of Uganda'
                    extraWDStatements.append(buildStatement(NEWITEM, instanceOf, "Q5177124", ubosReference))
                    extraWDStatements.append(buildStatement(NEWITEM, administrativeRegionProperty, administrativeRegion, ubosReference))
                elif admin_level == '8':
                    description = 'sub-county of Uganda'
                    extraWDStatements.append(buildStatement(NEWITEM, instanceOf, "Q7630601", ubosReference))
                    extraWDStatements.append(buildStatement(NEWITEM, administrativeRegionProperty, administrativeRegion, ubosReference))
                elif admin_level == '9':
                    description = 'parish of Uganda'
                    extraWDStatements.append(buildStatement(NEWITEM, instanceOf, "Q22683078", ubosReference))
                    extraWDStatements.append(buildStatement(NEWITEM, administrativeRegionProperty, administrativeRegion, ubosReference))
                elif admin_level == '10':
                    description = 'village or city in Uganda'
                    extraWDStatements.append(buildStatement(NEWITEM, instanceOf, "Q486972", ubosReference)) # human settlement
                    extraWDStatements.append(buildStatement(NEWITEM, administrativeRegionProperty, administrativeRegion, ubosReference))

            if not(description):
                if city and not(city=='None'):
                    description = level + 'school in ' + city + ', Uganda'
                else:
                    description = level + 'school in Uganda'
                print description
            itemDocuments = wbsea.WbSearchEntities(searchString=name)
            pprint.pprint(itemDocuments)
            notFound = True
            if 'success' in itemDocuments and itemDocuments['search']:
                for res in itemDocuments['search']:
                    print res
                    if 'description' in res and res['description'] == description:
                        print res['description']
                        Q_school = res['id']
                        notFound = False
                        print Q_school + ' already in Wikidata'
            if notFound:
                if district:
                    if district in districtIds:
                        Q_district = districtIds[district]
                    else:
                        itemDocuments = wbsea.WbSearchEntities(language ='en', searchString = district+ ' District')
                        pprint.pprint(itemDocuments)
                        print('+++++++++++++++++District++++++++++++++')
                        if itemDocuments['success'] and itemDocuments['search']:
                            Q_district = itemDocuments['search'][0]['id']
                            districtIds[district] = Q_district
                            extraWDStatements.append(buildStatement(NEWITEM, administrativeRegionProperty, Datamodel.makeWikidataItemIdValue(Q_district), ubosReference))
                ### wi.addClaim('P969', city + ', ' + parish + ', ' + subcounty + ', ' + county + ', ' + district, 'P248', "Q22679902") # street address
                if wikidata:
                    # print dir(ItemIdValue)
                    itemid = wikidata[1:]
                else:
                    itemid = NEWITEM
                itemDocumentForSchool = (ItemDocumentBuilder.forItemId(itemid)
                                                            .withLabel(name, "en")
                                                            .withDescription(description, "en"))
                # print '++++++++++++++++++++++++++++++++++++++++++++++++++'
                # pprint.pprint(extraWDStatements)
                extraWDStatements.append(countryUgandaStatement)
                # pprint.pprint(extraWDStatements)

                for extraStatement in extraWDStatements:
                    itemDocumentForSchool.withStatement(extraStatement)
                itemDocumentForSchool = itemDocumentForSchool.build()
                newItem = wbde.createItemDocument(itemDocumentForSchool, "Importing schools in Uganda from www.ubos.org")
                # newItemId = newItem.getItemId()
                # print newItemId
            found = False
            for i in range(2, 0, -1):
                time.sleep(i/11.0)
                itemDocuments = wbsea.WbSearchEntities(searchString = name)
                if 'success' in itemDocuments and itemDocuments['search']:
                    for res in itemDocuments['search']:
                        print res
                        if 'description' in res and res['description'] == description:
                            Q_school = res['id']
                            print Q_school
                            if type=='node':
                                newSchool = Node(element)
                            elif type=='way':
                                newSchool = Way(element)
                            else:
                                newSchool = Relation(element)
                            dirty =False
                            if newSchool.get('wikidata') != Q_school:
                                newSchool.put('wikidata', Q_school); dirty=True
                            for tag in tagsToSet:
                                if tagsToSet[tag]: newSchool.put(tag, tagsToSet[tag]); dirty=True
                            if dirty:
                                CommandsList=[Command.ChangeCommand( element, newSchool)]
                                Main.main.undoRedo.add(Command.SequenceCommand("Add wikidata and isced:level tags to school", CommandsList))
                            found = True
                            break
                    if found: break
                else:
                    print 'not found yet'
            if element.isNew(): noNewSchools=False
            if Q_school:
                wbdf = WikibaseDataFetcher.getWikidataDataFetcher()
                wikidataCoords = wbdf.getEntityDocument(Q_school)
                # print dir(wikidataCoords)
                pprint.pprint(wikidataCoords)
                hasCoords = wikidataCoords.hasStatement("P625")
                print('++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
                print(hasCoords)
                # wikidataCoords = wbsea.wbGetEntities(ids=Q_school,props="P625")
                # wikidataCoords = wd.fetchCoordinates(Q_school)

                if not(hasCoords):
                    lon = lat = None
                    if type=='node':
                        latlon = element.getCoor()
                        lon = str(latlon.getX())
                        lat = str(latlon.getY())
                    elif type=='way':
                        latlon= mv.getProjection().eastNorth2latlon(Geometry.getCentroid(element.getNodes()))
                        lon = str(latlon.getX())
                        lat = str(latlon.getY())
                    
                    #m=latlonRE.match(str(coor))
                    #print 'match: ', m, 'new: ', element.isNew()
                    if not(element.isNew()) and lon and lat:# and m:
                        print 'Coordinates not yet present in Wikidata, building up coordStatements'
                        coordStatement = Q_school + '\tP625\t@' + lat[:7] + '/' + lon[:7] + '\tS854\t"https://www.openstreetmap.org/' + type + '/' + str(element.getId()) + '"\n'
                        coordStatements[Q_school] = coordStatement
                    # pprint.pprint(coordStatements)
                else:
                    print 'Coordinates already present in Wikidata'

        if coordStatements:
            number = 0; qs_url=''; doit = '&doit'
            for coordStatement in coordStatements:
                print coordStatements[coordStatement]
                qs_url += URLEncoder.encode(coordStatements[coordStatement], "UTF-8")
                if number > 8:
                    OpenBrowser.displayUrl('http://tools.wmflabs.org/wikidata-todo/quick_statements.php?list=' + qs_url + doit)
                    number = 0; qs_url=''
                else:
                    number+=1
            if qs_url:
                OpenBrowser.displayUrl('http://tools.wmflabs.org/wikidata-todo/quick_statements.php?list=' + qs_url + doit)
        if noNewSchools:
            print 'switching to regular account'
            if not(Main.pref.get("osm-server.username") == osm_account):
                Main.pref.put("osm-server.username", osm_account)
                JOptionPane.showMessageDialog(Main.parent, "Switched back to regular OSM account, please upload the usual way")
        else:
            print 'switching to import account and selecting all new schools'
            Main.pref.put("osm-server.username", osm_import_account)
            SearchAction.search('amenity new (school | kindergarten | university | college)',SearchAction.SearchMode.fromCode('R'))
            Utils.copyToClipboard('''import=yes
url=https://wiki.openstreetmap.org/wiki/WikiProject_Uganda/Import_Uganda_Bureau_Of_Statistics_Education_Facilities
source=www.ubos.org''')
            JOptionPane.showMessageDialog(Main.parent, "Switched to IMPORT OSM account, please upload selection. (new schools are selected automatically) url= has been copied to the clipboard for convenience")
