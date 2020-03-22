#################################
##### Name: Ashley Beals
##### Uniqname: bealsa
#################################

from bs4 import BeautifulSoup
import requests
import json
import mapsecrets # file that contains your API key


CACHE_FILE_NAME = "cache.json"

def open_cache():
    try:
        cache_file = open(CACHE_FILE_NAME, 'r')
        cache_contents = cache_file.read()
        cache_dict = json.loads(cache_contents)
        cache_file.close()
    except:
        cache_dict = {}
    return cache_dict

def save_cache(cache_dict):
    fw = open(CACHE_FILE_NAME, "w")
    dumped_json_cache = json.dumps(cache_dict)
    fw.write(dumped_json_cache)
    fw.close()

def construct_unique_key(BASE_URL, params): #make a url as the cache key
    params_strings = []
    connector= "_"
    for k in params.keys():
        params_strings.append(f'{k}_{params[k]}')
    params_strings.sort()
    unique_key = BASE_URL + connector + connector.join(params_strings)
    return unique_key


def make_request(baseurl, params={}):
    response = requests.get(baseurl, params)
    return response.text

def make_request_with_cache(baseurl, params={}):
    request_key = baseurl
    if request_key in CACHE_DICT.keys():
        print("Using Cache")
        return CACHE_DICT[request_key]
    else:
        print("Fetching")
        CACHE_DICT[request_key] = make_request(request_key, params)
        save_cache(CACHE_DICT)
        return CACHE_DICT[request_key]

CACHE_DICT = open_cache()

class NationalSite:
    '''a national site

    Instance Attributes
    -------------------
    category: string
        the category of a national site (e.g. 'National Park', '')
        some sites have blank category.

    name: string
        the name of a national site (e.g. 'Isle Royale')

    address: string
        the city and state of a national site (e.g. 'Houghton, MI')

    zipcode: string
        the zip-code of a national site (e.g. '49931', '82190-0168')

    phone: string
        the phone of a national site (e.g. '(616) 319-7906', '307-344-7381')
    '''
    def __init__(self, category, name, address, zipcode, phone):

        self.category = category
        self.name = name
        self.address = address
        self.zipcode = zipcode
        self.phone = phone

    def info(self):
        return self.name + " (" + self.category +")" + ": " + self.address + " " + self.zipcode


def build_state_url_dict():
    ''' Make a dictionary that maps state name to state page url from "https://www.nps.gov"

    Parameters
    ----------
    None

    Returns
    -------
    dict
        key is a state name and value is the url
        e.g. {'michigan':'https://www.nps.gov/state/mi/index.htm', ...}
    '''

    url = 'https://www.nps.gov/index.htm'
    response = make_request_with_cache(url)
    soup = BeautifulSoup(response, 'html.parser')
    all_state_urls = soup.find_all('ul', class_="dropdown-menu SearchBar-keywordSearch")
    dict =  {}
    for state in all_state_urls:
        state_info = state.find_all('a')
        for state in state_info:
            dict[state.text.lower()] = "https://www.nps.gov" + state['href']
    return dict


def get_site_instance(site_url):
    '''Make an instances from a national site URL.

    Parameters
    ----------
    site_url: string
        The URL for a national site page in nps.gov

    Returns
    -------
    instance
        a national site instance
    '''

    response2 = make_request_with_cache(site_url)
    soup = BeautifulSoup(response2, 'html.parser')
    try:
        category = soup.find('span', class_='Hero-designation').text.strip()
    except:
        category = "No Category"
    try:
        name = soup.find('div', class_='Hero-titleContainer').find('a', class_='Hero-title').text.strip()
    except:
        name = "No Name"
    try:
        address = soup.find('p', class_='adr').find('span', itemprop='addressLocality').text  + ", " + soup.find('p', class_='adr').find('span', itemprop='addressRegion').text.strip()
    except:
        address = "No Address"
    try:
        zipcode = soup.find('p', class_='adr').find('span', class_='postal-code').text.strip()
    except:
        zipcode = "No Zipcode"
    try:
        phone = soup.find('span', class_='tel').text.strip()
    except:
        phone = "No Phone Number"

    national_site = NationalSite(category, name, address, zipcode, phone)

    return national_site


def get_sites_for_state(state_url):
    '''Make a list of national site instances from a state URL.

    Parameters
    ----------
    state_url: string
        The URL for a state page in nps.gov

    Returns
    -------
    list
        a list of national site instances
    '''

    response = make_request_with_cache(state_url)
    soup = BeautifulSoup(response, 'html.parser') 
    state_sites = soup.find('ul', id='list_parks').find_all('h3')

    site_urls = []
    national_sites = []

    for site in state_sites:
        site_info = site.find_all('a')[0]['href']
        full_url = "http://nps.gov"+site_info+"index.htm"
        site_urls.append(full_url)

    for site in site_urls:
        national = get_site_instance(site)
        national_sites.append(national)

    return national_sites


def print_national_site(national_sites):
    '''Obtain national site instance, format, and print.

    Parameters
    ----------

    Returns
    -------
    '''
    for i in range(len(national_sites)):
        print(f"[{i+1}] {national_sites[i].info()}")



def get_nearby_places(site_object):
    '''Obtain API data from MapQuest API.

    Parameters
    ----------
    site_object: object
        an instance of a national site

    Returns
    -------
    dict
        a converted API return from MapQuest API
    '''

    response = make_request_with_cache('http://www.mapquestapi.com/search/v2/radius', params = {"key": mapsecrets.CONSUMER_KEY, "origin":site_object.zipcode, "radius":10, "maxMatches":10, "ambiguities":"ignore",
    "outFormat": "json"})
    return json.loads(response)


def print_nearby_places(dictionary):
    '''Obtain dictionary of nearby places, format each place and print.

    Parameters
    ----------
    dict

    Returns
    -------

    '''
    list = dictionary['searchResults']

    for dict in list:
        try:
            if dict['name'] != '':
                name = dict['name']
            else:
                name = "No name"
        except ValueError:
            name = "No name"
        try:
            if dict['fields']['group_sic_code_name'] != '':
                category = dict['fields']['group_sic_code_name']
            else:
                category = "No category"
        except ValueError:
            category = "No category"
        try:
            if dict['fields']['address'] != '':
                address = dict['fields']['address']
            else:
                address = 'No address'
        except ValueError:
            address = "No address"
        try:
            if dict['fields']['city'] != '':
                city = dict['fields']['city']
            else:
                city = 'No city'
        except ValueError:
            city = "No city"

        print(f"- {name} ({category}): {address}, {city}")


if __name__ == "__main__":

    #CACHE_DICT = open_cache()
    has_ended = False
    state_dictionary = build_state_url_dict()

    while not has_ended:
        search = input('Enter a state name (e.g. Michigan, michigan) or exit: ')
        if search != 'exit':
            try:

                state_url = state_dictionary[search.lower()]
                national_site = get_sites_for_state(state_url)
                print('--------------------------------------')
                print('List of national sites in ',search)
                print('--------------------------------------')
                print_national_site(national_site)

                while not has_ended:
                    search_number = input('Choose the number for detail search or "exit" or "back": ')
                    if search_number == "back":
                        break
                    elif search_number == "exit":
                        has_ended = True
                    else:
                        try:
                            places = get_nearby_places(national_site[int(search_number)-1])
                            print('--------------------------------------')
                            print('Places near ', ((national_site)[int(search_number)-1]).name)
                            print('--------------------------------------')
                            print_nearby_places(places)
                        except:
                            print("[Error] Invalid input")
                            print(" ")
            except:
                print("[Error] Enter a proper state name")
                print(" ")
        else:
            has_ended = True
