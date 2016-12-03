import xml.etree.ElementTree as ET
from collections import defaultdict
from collections import Counter
import codecs
import json
import pprint
import re

osm_file = open("new_york_sample.osm", "r")

street_type_re = re.compile(r'\S+\.?$', re.IGNORECASE)
freq = defaultdict(int)

def print_sorted_dict(d):
    keys = d.keys()
    keys = sorted(keys, key=lambda s: s.lower())
    for k in keys:
        v = d[k]
        print "%s: %d" % (k, v) 

def count_street_types(osmfile):
    '''Count the occurance of each street type'''
    
    for event, elem in ET.iterparse(osmfile):
        if (elem.tag == "tag") and (elem.attrib['k'] == "addr:street"):
            m = street_type_re.search(elem.attrib['v'])  
            if m:
                street_type = m.group()
                freq[street_type] += 1
    return print_sorted_dict(freq)
    
count_street_types(osm_file) 


#=======================================================================#
# Modify the street names and save it to attribute v

osm_file = "new_york_sample.osm"
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)


mapping = {"Ave": "Avenue",
           "ave": "Avenue",
           "avenue": "Avenue",
           "Broadwat": "Broadway",
           "CIRCLE": "Circle",
           "DRIVE": "Drive",
           "drive": "Drive",
           "LANE": "Lane",
           "Rd": "Road",
           "ROAD": "Road",
           "St": "Street",
           "St.": "Street"
            }

def update_name(name, mapping): 
    
    '''change according to the mapping above, 
    and modify all the alphabet avenues'''

    old = name.split(' ')[-1]
    keep = name.split(' ')[:-1]
    new = []
    if old in mapping.keys():
        new.append(mapping[old])
        return ' '.join(keep + new)
    elif keep == ['Avenue']:
        return ' '.join(re.findall("\S+", name)[::-1])
    else:
        return name

def change_street_names(element): 
    if (element.tag == "tag") and (element.attrib['k'] == "addr:street"):
        element.attrib['v'] = update_name(element.attrib['v'], mapping)
        return element.attrib['v']
			

def change_zip_code(element):
    '''Remove all the State abbreviations in zip codes'''
    
    if element.tag == 'way' or element.tag == 'node':
        for sub in element:
            if sub.get('k') == 'addr:postcode':
                if sub.get('v').startswith('NY'):
                    sub.attrib['v'] = sub.attrib['v'][-5:]
									

def change_timestamp(elem):
    '''Find and keep only the year of each timestamp'''
		
    import datetime, dateutil.parser
    if elem.tag == "node" or elem.tag == "way":
        for att in elem.attrib.keys():
            if att == 'timestamp':
                d = dateutil.parser.parse(elem.attrib['timestamp'])
                year = int(d.strftime('%Y'))
                elem.attrib['timestamp'] = int(year)
								
								
lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

CREATED = ["version", "changeset", "timestamp", "user", "uid"]

def shape_element(elem):
    '''Form a node for each entry, organize different types of info into dict format'''
    
    node = {}
    created = {}
    address ={}
    
    if elem.tag == "node" or elem.tag == "way":
        for att in elem.attrib.keys():
            node['type'] = elem.tag
            
            # Create sub-dict 'created' within node
            if att in CREATED:
                created[att] = elem.attrib[att]
                node['created'] = created
            
            # Create list 'pos' within dict 'created'
            elif elem.attrib[att] == elem.get('lat') or elem.get('lon'):
                pos = []
                pos.append(float(elem.get('lat')))
                pos.append(float(elem.get('lon')))
                node['pos'] = pos
                
            # Add other items into node, such as 'id', 'visible', etc.
            else:
                node[att] = elem.attrib[att]
                
        for sub in elem: 
            if sub.tag == 'tag':
                # Ignore all problematic characters
                if problemchars.search(sub.get('k')):
                    pass 
                
                # Ignore the tags that have colons after 'addr:'
                elif sub.get('k').startswith('addr:'):
                    if lower_colon.search(sub.get('k')[5:]):
                        pass
                    
                    # Add all the arributes of 'addr:' into dict
                    else:
                        address[sub.get('k')[5:]] = sub.get('v')
                        node['address'] = address
                
                # Add other series of tags into dict 
                # In nyc there are tiger, nycdoitt, and gnis systems
                elif lower_colon.search(sub.get('k')):
                    title = sub.get('k').split(':')[0]
                    node[title] = {}
                    node[title][sub.get('k').split(':')[-1]] = sub.get('v')
                    
                # Add other individual tags such as 'building', 'ele'
                # 'height' for buildings,'sport', 'source' for 'leisure'
                else:
                    node[sub.get('k')] = sub.get('v')
            
            # Add node references
            elif sub.tag == 'nd':
                refs = []
                refs.append(sub.get('ref'))
                node['node_refs'] = refs
             
        return node		
			
			
			
def process_map(file_in, pretty = False):

    file_out = "new_york_sample_output.json"
    data = []
    with codecs.open(file_out, "w") as output:
        for _, element in ET.iterparse(file_in):
            
            # Update street names in 'v' attributes
            change_street_names(element)
            
            # Modify problematic zip codes
            change_zip_code(element)
            
            # Modify timestamps into parseable forms
            change_timestamp(element)
            
            # Organize attributes and format the dataset
            elem = shape_element(element)
            
            if elem:
                data.append(elem)
                if pretty:
                    output.write(json.dumps(elem, indent=2)+"\n")
                else:
                    output.write(json.dumps(elem) + "\n")
    return data
	
	
#=======================================================================#

process_map('new_york_sample.osm', pretty = False)