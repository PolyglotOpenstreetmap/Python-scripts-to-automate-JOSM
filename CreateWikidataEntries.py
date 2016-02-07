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
import org.openstreetmap.josm.data.osm.Node as Node
import org.openstreetmap.josm.data.osm.Way as Way
import org.openstreetmap.josm.data.osm.Relation as Relation
import org.openstreetmap.josm.data.osm.TagCollection as TagCollection
import org.openstreetmap.josm.data.osm.DataSet as DataSet
import org.openstreetmap.josm.tools.Utils as Utils
import org.openstreetmap.josm.tools.OpenBrowser as OpenBrowser
import org.openstreetmap.josm.tools.HttpClient as HttpClient
import org.openstreetmap.josm.gui.preferences.advanced.PrefEntry as PrefEntry
import org.openstreetmap.josm.actions.search.SearchAction as SearchAction
# import org.openstreetmap.josm.actions.UploadSelectionAction as UploadSelectionAction
import org.openstreetmap.josm.data.osm.Changeset as Changeset
import java.net.HttpURLConnection as HttpURLConnection
import java.net.URL as URL
import java.net.URLEncoder as URLEncoder
import java.net.CookieManager as CookieManager
import java.net.CookieHandler as CookieHandler
import java.io.InputStream as InputStream

import re, time, json, pprint

# uploadSelection = UploadSelectionAction()
# print dir(uploadSelection)

osm_account =        'Polyglot'
osm_import_account = 'Polyglot_Import'

latlonRE = re.compile(r'LatLon\[lat=(?P<lat>-*\d+(\.\d\d\d\d\d\d)?)\d*,lon=(?P<lon>-*\d+(\.\d\d\d\d\d\d)?)\d*\]')
PrimarySchoolRE = re.compile(r'\s[Pp]r*\\*(im|imary)*\.*\s*[Ss]chool')
NurseryAndPrimarySchoolRE = re.compile(r'.*\sN/\s*[Pp]r*(im|imary)*\.*\s*[Ss]chool')

cookieManager = CookieManager()
CookieHandler.setDefault(cookieManager)

def getMapView():
    if Main.main and Main.main.map:
        return Main.main.map.mapView
    else:
        return None

class DataType():
    def __init__(self, type='', value=''):
        self.type=type
        self.value=value
class EntityIdType(DataType):
    def __init__(self, value=''):
        self.type='entityid'
        self.value=value
    def asJSON(self):
        json='''{"value": {"entity-type": "item","numeric-id": %s},"type": "wikibase-entityid"}''' % (self.value[1:])
class PropertyIdType(DataType):
    def __init__(self, value=''):
        self.type='propertyid'
        self.value=value
    def asJSON(self):
        json='''"value","property":"%s","datavalue":''' % (self.value)
class NumericType(DataType):
    def __init__(self, value=''):
        self.type='numeric'
        self.value=value
class StringType(DataType):
    def __init__(self, value=''):
        self.type='string'
        self.value=value
class DateTimeType(DataType):
    def __init__(self, value=''):
        self.type='date'
        self.value=value
class CoordType(DataType):
    def __init__(self, value=''):
        self.type='coordinates'
        self.value=value
class URLType(DataType):
    def __init__(self, value=''):
        self.type='url'
        self.value=value

{"snaktype": "value","property": "'+claim['sourceproperty']+'",
"datavalue": {"value": "'+claim['source']+'","type": "string"},"datatype": "url"}
{"snaktype": "value","property": "P854",
"datavalue": {"value": "http://www.ubos.org","type": "string"},"datatype": "url"}

class WikidataItem():
    def __init__(self, itemData=''):
        if itemData:
            self.item=json.loads(itemData)
        else:
            self.item = {}
    def addLabel(self, lang, label):
        self.item.setdefault('labels', {})
        self.item['labels'].setdefault(lang, label)
    def addDescription(self, lang, description):
        self.item.setdefault('descriptions', {})
        self.item['descriptions'].setdefault(lang, description)
    def addAlias(self, lang, alias):
        self.item.setdefault('aliases', {})
        self.item['aliases'].setdefault(lang, []).append(alias)
    def addClaim(self, property, value, sourceproperty='', source='', rank='normal'):
        self.item.setdefault('claims', [])
        claim ={'property': property,
                'value':    value,
                'rank':     rank
               }
        if sourceproperty and source:
            claim['sourceproperty'] = sourceproperty
            claim['source'] = source
        self.item['claims'].append(claim)
    def addCoordinates(self, property, lat, lon, sourceproperty='', source='', rank='normal'):
        self.item.setdefault('claims', [])
        claim ={'property': property,
                'lat':    lat,
                'lon':    lon,
                'rank':     rank
               }
        if sourceproperty and source:
            claim['sourceproperty'] = sourceproperty
            claim['source'] = source
        self.item['claims'].append(claim)
    def asJSON(self):
        json='{'
        comma1 = ''
        for group in self.item:
            # print group 
            json+=comma1 + '"' + group + '":'
            comma2 = ''
            if group in ['claims']:
                json+='['
                for claim in self.item[group]:
                    json+=comma2 + '{"mainsnak":{"snaktype":"value","property":"'+ claim['property'] +'","datavalue":{"value": {"entity-type": "item","numeric-id": '+ claim['value'][1:] +'},"type": "wikibase-entityid"}},"type":"statement","rank":"'+claim['rank']+'"'
                    if 'sourceproperty' in claim and 'source' in claim:
                        json+=',"references":[{"snaks":{"'+claim['sourceproperty']+'":[{"snaktype": "value","property": "'+claim['sourceproperty']+'","datavalue": {"value": "'+claim['source']+'","type": "string"},"datatype": "url"}]}}]'
                    if not(comma2): comma2 = ','
                    json+='}'
                json+=']'
            else:
                json+='{'
                comma4 = ''
                for lang in self.item[group]:
                    print 'lang'
                    print lang
                    if group in ['aliases']:
                        comma3 = ''
                        for item in self.item[group][lang]:
                            json+=comma3 + '"' + lang + '":{"language":"' + lang + '","value":"' + item + '"}'
                            if not(comma3): comma3 = ','
                    else:
                        json+=comma4 + '"' + lang + '":{"language":"' + lang + '","value":"' + self.item[group][lang] + '"}'
                    if not(comma4): comma4 = ','
                json+='}'
            if not(comma1): comma1 = ','

        json+='}'
        return json
        # print json
        # pprint.pprint(json)

class Wikidata():
    '''Class to interact with Wikidata'''

    def __init__(self):
        self.url = 'https://www.wikidata.org/w/api.php'
        self.client = None
        self.cookies = None
        self.editToken = None
        
    def getCookies(self):
        self.cookies = cookieManager.getCookieStore().getCookies()

    def setCookies(self):
        if self.cookies:
            for self.cookie in self.cookies:
                # print self.cookie.getName(), self.cookie.getValue()
                self.client.setHeader(self.cookie.getName(), self.cookie.getValue())

    def setParams(self, format='json', action='', lgname='', lgpassword='', lgtoken='', language='', search='',
                        id='', entity='', property='', new='', data='', meta='', type='', token='', summary=''):
        self.params=''
        if format: self.params+='&format=' + format
        if action: self.params+='&action=' + action
        if language: self.params+='&language=' + language
        if lgname: self.params+='&lgname=' + URLEncoder.encode(lgname, "UTF-8")
        if lgpassword: self.params+='&lgpassword=' + URLEncoder.encode(lgpassword, "UTF-8")
        if lgtoken: self.params+='&lgtoken=' + URLEncoder.encode(lgtoken, "UTF-8")
        if search: self.params+='&search=' + URLEncoder.encode(search, "UTF-8")
        if id: self.params+='&id=' + URLEncoder.encode(id, "UTF-8")
        if entity: self.params+='&entity=' + URLEncoder.encode(entity, "UTF-8")
        if property: self.params+='&property=' + property
        if meta: self.params+='&meta=' + meta
        if type: self.params+='&type=' + type
        if new: self.params+='&new=' + new
        if data: self.params+='&data=' + URLEncoder.encode(data, "UTF-8")
        if summary: self.params+='&summary=' + URLEncoder.encode(summary, "UTF-8")
        if token: self.params+='&token=' + URLEncoder.encode(token, "UTF-8")

    def connect(self):
        self.client = HttpClient.create(URL(self.url), "POST")
        self.client.setRequestBody(self.params)
        self.client.setHeader("Content-Type", "application/x-www-form-urlencoded")
        self.client.setHeader("User-Agent", "Polyglot's JOSM Bot (runs in Java Openstreetmap Editor, developed from scratch in Jython)")
        self.setCookies()
        self.httpConnection = self.client.connect()
        self.getCookies()
        pprint.pprint(self.cookies)
        self.content = json.loads(self.httpConnection.fetchContent())
        # print self.httpConnection.getHeaderFields()
        # print 'content: ' + self.content['login']['result']
        pprint.pprint(self.content)
        if 'login' in self.content:
            self.login = self.content['login']
            if 'result' in self.login:
                result = self.login['result']
                print 'result: ', result
        return self.content
        
    def login(self, user = '', passw = ''):
        if user:     Main.pref.put("wikidata.username", user)
        if passw:    Main.pref.put("wikidata.password", passw)
        self.user  = Main.pref.get("wikidata.username")
        # print self.user
        self.passw = Main.pref.get("wikidata.password")
        if not(self.user and self.passw):
            print "No username or password supplied nor stored in settings"
            return
        self.setParams(action='login', lgname=self.user, lgpassword=self.passw)
        self.connect()
        if self.content['login']['result'] == 'NeedToken':
            print 'Confirming login using token'
            self.token = self.content['login']['token']
            self.params += '&lgtoken=' + self.token
            # print self.params
            return self.connect()

    def search(self, lang ='en', valueOrDescription = ''):
        self.setParams(action='wbsearchentities', search=valueOrDescription, language=lang)
        self.connect()
        self.result = self.client.connect().fetchContent()
        return json.loads(self.result)

    def fetchPropertyForItem(self, qid, property):
        self.setParams(action='wbgetclaims', entity=qid, property=property)
        self.connect()
        # print self.params
        self.result = self.client.connect().fetchContent()
        # print self.result
        return json.loads(self.result)

    def fetchCoordinates(self, qid):
        return self.fetchPropertyForItem(qid, 'P625')

    def requestEditToken(self, requestedTokens=''):
        if not(self.editToken):
            self.setParams(action='query', meta='tokens', type=requestedTokens)
            self.connect()
            if ('query'     in self.content and
                'tokens'    in self.content['query'] and
                'csrftoken' in self.content['query']['tokens']):
                self.editToken=self.content['query']['tokens']['csrftoken']
                # pprint.pprint(self.editToken)

    def createNewItem(self, data):
        self.requestEditToken()
        self.setParams(action='wbeditentity', new='item', data=data, token=self.editToken)
        print 'Parameters:'
        pprint.pprint(self.params)
        self.connect()
        # print self.content
        return self.content

    def createClaims(self, qid, data):
        self.requestEditToken()
        # print data
        self.setParams(action='wbeditentity', id=qid, data=data, token=self.editToken)
        print 'Parameters:'
        pprint.pprint(self.params)
        self.connect()
        # print self.content
        return self.content

wd=Wikidata()
# wd.login(user = "Polyglot", passw = "")
login = wd.login()

mv = getMapView()

if mv and mv.editLayer and mv.editLayer.data:
    selectedElements = mv.editLayer.data.getSelected()
    
    if not(selectedElements):
        JOptionPane.showMessageDialog(Main.parent, "Please select an element")
    else:
        noNewSchools = True
        coordStatements = {}  
        for element in selectedElements:    
            Q_school = ''
            wi=WikidataItem()
            housenumber = street = district = county = subcounty = parish = city = amenity = isced_level = operator_type = name = wikidata = ''
            print dir(element)
            if element.hasKey('name'): name = str(element.get('name'))
            if name=='Primary School' or name=='Secondary School' or name=='Nursery School':
                print 'Skipping school with nondescript name'
                continue
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
            if 'Prim' in name and ('Nurser' in name or 'Kinderga' in name):
                isced = '0;1'
                wi.addClaim('P31', 'Q9842', 'P854', "http://www.ubos.org")                  # primary school
                wi.addClaim('P31', 'Q1076052', 'P854', "http://www.ubos.org")               # nursery school
                level = 'primary and nursery '
            elif 'Prim' in name:
                isced = '1'
                wi.addClaim('P31', 'Q9842', 'P854', "http://www.ubos.org")                  # primary school
                level = 'primary '
            elif 'kindergarten' in amenity or 'Nurser' in name or 'Kinderga' in name:
                isced = '0'
                wi.addClaim('P31', 'Q1076052', 'P854', "http://www.ubos.org")               # nursery school
                level = 'nursery '
            elif 'Sec' in name or 'High' in name or 'College' in name:
                isced = '2;3;4'
                wi.addClaim('P31', 'Q159334', 'P854', "http://www.ubos.org")                # secondary school
                level = 'secondary '
            else:
                wi.addClaim('P31', 'Q3914', 'P854', "http://www.ubos.org")                  # school
                isced = ''; level = ''

            if city and not(city=='None'):
                description = level + 'school in ' + city + ', Uganda'
            else:
                description = level + 'school in Uganda'
            result = wd.search(valueOrDescription = name)
            print '==================='
            print description
            # pprint.pprint(result)
            if result['success'] and result['search']:
                for res in result['search']:
                    # print res
                    if 'description' in res and res['description'] == description:
                        print res['description']
                        Q_school = res['id']
                        print Q_school + ' already in Wikidata'

            else:
                wi.addLabel('en', name)
                
                if district:
                    result = wd.search(lang ='en', valueOrDescription = district+ ' District')
                    print('+++++++++++++++++District++++++++++++++')
                    pprint.pprint(result)
                    if result['success'] and result['search']:
                        Q_district = result['search'][0]['id']
                        print Q_district
                        wi.addClaim('P131', Q_district, 'P854', "http://www.ubos.org") # administrative region, district of Uganda
                wi.addDescription('en', description)
                wi.addClaim('P17', 'Q1036', 'P854', "http://www.ubos.org") # country Uganda
                # wi.addClaim('P969', city + ', ' + parish + ', ' + subcounty + ', ' + county + ', ' + district, 'P854', "http://www.ubos.org") # street address
                # pprint.pprint(wi.asJSON())
                print(wd.createNewItem(data=wi.asJSON()))
            found = False
            for i in range(12, 0, -1):
                time.sleep(i/11.0)
                result = wd.search(valueOrDescription = name)
                # pprint.pprint(result)
                if result['success'] and result['search']:
                    for res in result['search']:
                        print res
                        if 'description' in res and res['description'] == description:
                            Q_school = res['id']
                            print Q_school
                            newSchool = Node(element)
                            dirty =False
                            if newSchool.get('wikidata') != Q_school:
                                newSchool.put('wikidata', Q_school); dirty=True
                            if not(isced_level) and isced and newSchool.get('isced:level') != isced_level:
                                newSchool.put('isced:level', isced); dirty=True
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
                wikidataCoords = wd.fetchCoordinates(Q_school)
                print wikidataCoords
                if not(wikidataCoords['claims']):
                    m=latlonRE.match(str(element.getCoor()))
                    print 'match: ', m, 'new: ', element.isNew()
                    if not(element.isNew()) and m:
                        print 'Coordinates not yet present in Wikidata, building up coordStatements'
                        coordStatement = Q_school + '''\tP625\t@''' + m.group('lat') + '''/''' + m.group('lon') + '''\tS854\t"https://www.openstreetmap.org/node/''' + str(element.getId()) + '''"\n'''
                        coordStatements[Q_school] = coordStatement
                    pprint.pprint(coordStatements)
                else:
                    print 'Coordinates already present in Wikidata'

        if coordStatements:
            number = 0; qs_url=''
            for coordStatement in coordStatements:
                print coordStatements[coordStatement]
                qs_url += URLEncoder.encode(coordStatements[coordStatement], "UTF-8")
                if number > 4:
                    OpenBrowser.displayUrl('http://tools.wmflabs.org/wikidata-todo/quick_statements.php?list=' + qs_url)# + '&doit')
                    number = 0; qs_url=''
                else:
                    number+=1
            if qs_url:
                OpenBrowser.displayUrl('http://tools.wmflabs.org/wikidata-todo/quick_statements.php?list=' + qs_url + '&doit')
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
