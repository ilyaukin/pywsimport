from argparse import ArgumentParser

from suds.client import Client
from suds.servicedefinition import ServiceDefinition
from wsmodel import *


parser = ArgumentParser()
parser.add_argument("wsdl", help="WSDL to parse")
parser.add_argument("--file", help="Python client file to create/update")
parser.add_argument("--name", help="Logical name of the service")
args = parser.parse_args()

if not args.name:
    args.name = args.wsdl.split("/")[-2]

if not args.file:
    args.file = args.name + "_manager.py"

client = Client(args.wsdl)
client_name = args.name + "_suds_client"
module_model = ModuleModel(args.file, client_name)

client_method_name = "_" + args.name + "_client"
client_method_model = ClientMethodModel(client_method_name, client_name, args.wsdl, service_name=args.name)
module_model.append_method(client_method_model)

for service in client.wsdl.services:
    sd = ServiceDefinition(client.wsdl, service)
    for port in sd.ports:
        for method in port[1]:
            method_name = method[0]
            method_model = ServiceQueryMethodModel(method_name, client_method_name, service_name=args.name)
            # print(method_name)
            for param in method[1]:
                method_model.append_arg((param[0], sd.xlate(param[1])))
            module_model.append_method(method_model)

module_model.save()
