#!python
import os, sys, datetime
import jmespath
import requests
import json

from akamai.edgegrid import EdgeGridAuth, EdgeRc

PAPI_HEADERS = {
    'accept': 'application/json',
    'PAPI-Use-Prefixes': "true"
}

DUMP_FOLDER = 'temp'

class akamaiClient():

    def __init__(self):

        edgerc = EdgeRc('~/.edgerc')
        default_section = 'default'
        self.baseurl = 'https://{}'.format(edgerc.get(default_section, 'host'))

        self.session = requests.Session()
        self.session.auth = EdgeGridAuth.from_edgerc(edgerc, default_section)

    def get_item_list(self,api_path='',headers={},datapath='',params=None):

        url = self.baseurl + api_path

        response = self.session.get(url, headers = headers, params = params)

        result = response.status_code
        print("Result: {}".format(result))
        raw_response_data = response.json()
        response_data = []

        if result == 200:
            response_data = jmespath.search(datapath, raw_response_data)
            # logger.debug("Successful response data: {}".format(response_data))

        else:
            print("Encountered error in response: {}".format(response_data))

        return response_data

    
def dump_json(dataset,base_name='',output_folder='.'):

        now = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = "{}_{}.json".format(now,base_name)
        output_folder = os.path.abspath(output_folder)
        filepath = os.path.join(output_folder,filename)

        encoder = json.JSONEncoder()
        encoded_json = encoder.encode(dataset)
        loaded_json = json.loads(encoded_json)
        with open(filepath,"w") as f:
            json.dump(loaded_json,f)

        return filepath

def list_property_groups(akamai_client:akamaiClient):

    api_path = '/papi/v1/groups'
    datapath = 'groups.items'
    results = akamai_client.get_item_list(
        api_path = api_path,
        datapath = datapath,
        headers = PAPI_HEADERS
    )

    filepath = dump_json(results,base_name='PropertyGroups',output_folder=DUMP_FOLDER)
    print("Dumped JSON file: {}".format(filepath))

    return results

def list_properties(akamai_client:akamaiClient,contract_id=None):

    api_path = '/papi/v1/properties'
    datapath = 'properties.items'
    full_results = []

    group_list = list_property_groups(akamai_client)

    for group in group_list:

        params = {
            'groupId': group['groupId'],
            'contractId': contract_id
        }

        results = akamai_client.get_item_list(
            api_path = api_path,
            datapath = datapath,
            headers = PAPI_HEADERS,
            params = params
        )

        full_results.extend(results)

    filepath = dump_json(full_results,base_name='Properties',output_folder=DUMP_FOLDER)
    print("Dumped JSON file: {}".format(filepath))

    return full_results

if __name__ == "__main__":

    contract_id = sys.argv[1]
    client = akamaiClient()

    property_list = list_properties(client, contract_id = contract_id)
