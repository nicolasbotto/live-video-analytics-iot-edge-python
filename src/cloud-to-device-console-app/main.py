import json
from os import path
import pathlib
import logging
from builtins import input
import ssl
import urllib.request
from azure.iot.hub import IoTHubRegistryManager
from azure.iot.hub.models import CloudToDeviceMethod, CloudToDeviceMethodResult

def urlToText(url):
    url = url.replace(path.sep, '/')
    resp = urllib.request.urlopen(url, context=ssl._create_unverified_context())
    return resp.read()

class GraphManager:
    
    def __init__(self):
        with open('appsettings.json', 'r') as settings_file:
            config_data = settings_file.read()

        config = json.loads(config_data)
        
        with open('operations.json') as ops_file:
            ops_data = ops_file.read()

        self.ops = json.loads(ops_data)

        self.device_id = str(config['deviceId'])
        self.module_id = str(config['moduleId'])
        self.generic_methods = [
            'GraphTopologyList',
            'GraphInstanceList',
            'GraphInstanceActivate',
            'GraphInstanceDeactivate',
            'GraphInstanceDelete',
            'GraphInstanceGet',
            'GraphInstanceSet',
            'GraphTopologyDelete',
            'GraphTopologyGet']
        self.api_version = '1.0'

        self.registry_manager = IoTHubRegistryManager(str(config['IoThubConnectionString']))

        for i,j in enumerate(self.ops['operations'], start=1):
            
            self.invocation_proxy(j['opName'], j['opParams'])

    def invocation_proxy(self, method_name, payload):
        if method_name=='GraphTopologySet':
            self.graph_topology_set(payload)
        
        if method_name in self.generic_methods:
            self.generic_call(method_name, payload)

        if method_name=='WaitForInput':
            print(payload['message'])
            input()

    
    def invoke_module_method(self, method_name, payload):

        module_method = CloudToDeviceMethod(
            method_name=method_name,
            payload=payload,
            response_timeout_in_seconds=30)
        
        print("\n-----------------------  Request: % s  --------------------------------------------------\n"% method_name)
        print(json.dumps(payload, indent=4))
        
        resp = self.registry_manager.invoke_device_module_method(self.device_id, self.module_id, module_method)
        
        print("\n---------------  Response: % s - Status: % s  ---------------\n"%(method_name, resp.status))

        if resp.payload is not None:
            print(json.dumps(resp.payload, indent=4))

    def graph_topology_set(self, op_parameters):
        if op_parameters is None:
            logging.info('Operation parameters missing')
            raise Exception

        if op_parameters.get('topologyUrl') is not None:
            topologyJsonString = urlToText(op_parameters['topologyUrl'])
        elif op_parameters.get('topologyFile') is not None:
            fpath = 'file://' + path.join(pathlib.Path(__file__).parent.absolute(), op_parameters['topologyFile'])
            topologyJsonString = urlToText(fpath)
        else:
            logging.info('Neither topologyUrl nor topologyFile specified')

        topology = json.loads(topologyJsonString)

        return self.invoke_module_method('GraphTopologySet', topology)

    def generic_call(self, method_name, op_parameters):
        if op_parameters is None:
            logging.info('Operation parameters missing')
            raise Exception
        
        # make sure '@apiVersion' comes first. Not sure if,
        # necessary, but at least to maintain convention.
        op_parameters['@apiVersion'] = self.api_version
        #
        return self.invoke_module_method(method_name, op_parameters)


if __name__ == '__main__':
    manager = GraphManager()
