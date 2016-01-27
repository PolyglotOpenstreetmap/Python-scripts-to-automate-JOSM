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
import java.net.URL as URL
import java.net.URLEncoder as URLEncoder
import re, time

def getMapView():
    if Main.main and Main.main.map:
        return Main.main.map.mapView
    else:
        return None

latlonRE = re.compile(r'LatLon\[lat=(?P<lat>-*\d+(\.\d\d\d\d\d\d)?)\d*,lon=(?P<lon>-*\d+(\.\d\d\d\d\d\d)?)\d*\]')
QinJSONRE = re.compile(r'"title":"(?P<qid>Q\d+)"')
mv = getMapView()
baseurl = 'https://www.wikidata.org/w/'


if mv and mv.editLayer and mv.editLayer.data:
    selectedElements = mv.editLayer.data.getSelected()
    
    if not(selectedElements):
        JOptionPane.showMessageDialog(Main.parent, "Please select an element")
    else:
        for element in selectedElements:
            housenumber = str(element.get('addr:housenumber'))
            street = str(element.get('addr:street'))
            district = str(element.get('addr:district'))
            county = str(element.get('addr:county'))
            subcounty = str(element.get('addr:subcounty'))
            city = str(element.get('addr:city'))
            parish = str(element.get('addr:parish'))
            amenity = str(element.get('amenity'))
            isced_level = str(element.get('isced:level'))
            operator_type = str(element.get('operator:type'))
            name = str(element.get('name'))
            wikidata = str(element.get('wikidata'))
            print name
            print operator_type
            print isced_level
            print amenity
            print county
            print subcounty
            print district
            print city
            print parish
            print street + ' ' + housenumber
            print wikidata
            level = ''; instanceof = 'Q3914' # school
            if 'Prim' in name:
                isced = '1'
                instanceof = 'Q9842' # primary school
                level = 'primary '
            elif 'Nurser' in name:
                isced = '0'
                instanceof = 'Q1076052' # Nursery school
                level = 'nursery '
            elif 'Sec' in name or 'High' or 'College' in name:
                isced = '2;3;4'
                instanceof = 'Q159334' # secondary school
                level = 'secondary '
                
                
            params  = '?action=wbsearchentities&search=' + URLEncoder.encode(name, "UTF-8") + '&language=en&format=json'
            url = baseurl + 'api.php' + params
            r1 = HttpClient.create(URL(url), "GET")
            r2 = r1.setHeader("Content-Type", "application/x-www-form-urlencoded").connect().fetchContent()
            #print dir(r2)
            print r2
            Q_school = QinJSONRE.search(r2)
            print Q_school
            if not(Q_school):

                districtStatement = ''
                if district:
                    params  = '?action=wbsearchentities&search=' + district + '%20District&language=en&format=json'
                    url = baseurl + 'api.php' + params
                    r1 = HttpClient.create(URL(url), "GET")
                    r2 = r1.setHeader("Content-Type", "application/x-www-form-urlencoded").connect().fetchContent()
                    #print dir(r2)
                    print r2
                    Q_district = QinJSONRE.search(r2)
                    print Q_district
                    if Q_district:
                        print Q_district.group('qid')
                        districtStatement = 'LAST\tP131\t' + Q_district.group('qid') + '\tS854\t"http://www.ubos.org"'
                #print dir(zip)
                if city and not(city=='None'):
                    schoolInCityStatement = '''\nLAST\tDen\t"''' + level + ''' school in ''' + city + ''', Uganda"'''
                else:
                    schoolInCityStatement = '''\nLAST\tDen\t"''' + level + ''' school in Uganda"'''
                m=latlonRE.match(str(element.getCoor()))
                coordStatement = ''
                if m:
                    coordStatement = '''\nLAST\tP625\t@''' + m.group('lat') + '''/''' + m.group('lon') + '''\tS854\t"https://www.openstreetmap.org/node/''' + str(element.getId()) + '''"'''
                result = '''CREATE
LAST\tLen\t"''' + name + '''"''' + schoolInCityStatement + '''
LAST\tP31\t''' + instanceof + '''\tS854\t"http://www.ubos.org"
LAST\tP17\tQ1036\tS854\t"http://www.ubos.org"
LAST\tP969\t"''' + parish + ''', ''' + city + ''', ''' + subcounty + ''', ''' +county + ''', ''' + district + '''"\tS854\t"http://www.ubos.org"
''' + districtStatement + coordStatement
                print result
                Utils.copyToClipboard(result)
                # user    = 'Polyglot'
                # passw   = ''
                # baseurl = 'https://www.wikidata.org/w/'
                # params  = '?action=login&lgname=%s&lgpassword=%s&format=json'% (user,passw)
                # url = baseurl +'api.php'+params
                # Login request
                # r1 = HttpClient.create(URL(url), "POST")
                # print r1
                # r2 = r1.connect().getContent()
                # print r2
                #token = r1.json()['login']['token']
                #params2 = params+'&lgtoken=%s'% token

                # Confirm token; should give "Success"
                #r2 = requests.post(baseurl+'api.php'+params2,auth=(authu,authp),cookies=r1.cookies)

                qs_url = 'http://tools.wmflabs.org/wikidata-todo/quick_statements.php?list=' + URLEncoder.encode(result, "UTF-8") + '&doit'
                OpenBrowser.displayUrl(qs_url)
                
                found = False
                for i in range(19, 0, -1):
                    time.sleep(i/3)
                    params  = '?action=wbsearchentities&search=' + URLEncoder.encode(name, "UTF-8") + '&language=en&format=json'
                    url = baseurl + 'api.php' + params
                    r1 = HttpClient.create(URL(url), "GET")
                    r2 = r1.setHeader("Content-Type", "application/x-www-form-urlencoded").connect().fetchContent()
                    #print dir(r2)
                    print i, r2
                    Q_school = QinJSONRE.search(r2)
                    if Q_school:
                        print Q_school.group('qid')
                        break
                    else:
                        print 'not found yet'

                break
            else:
                print 'already in Wikidata'
        newSchool = Node(element)
        newSchool.put('wikidata', Q_school.group('qid'))
        newSchool.put('isced:level', isced)

        CommandsList=[Command.ChangeCommand( element, newSchool)]
        Main.main.undoRedo.add(Command.SequenceCommand("Add wikidata and isced:level tags to school", CommandsList))




