from argparse import ArgumentParser

from suds.client import Client
from suds.servicedefinition import ServiceDefinition
from suds.xsd.sxbasic import Complex
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
module_model = ManagerModuleModel(args.file, client_name)

client_method_name = "_" + args.name + "_client"
client_method_model = ClientMethodModel(client_method_name, client_name, args.wsdl, service_name=args.name)
module_model.append_method(client_method_model)

for service in client.wsdl.services:
    sd = ServiceDefinition(client.wsdl, service)
    t_map = dict()
    class_model_map = dict()
    for t in [t[0] for t in sd.types]:
        if isinstance(t, Complex):
            t_map[t.name] = t
    for port in sd.ports:
        for method in port[1]:
            method_name = method[0]
            method_model = ServiceQueryMethodModel(method_name, client_method_name, service_name=args.name)
            for param in method[1]:
                param_type = param[1]
                type_name = param_type.type[0]
                qname = str(sd.xlate(param_type))

                def add_class_model(type_name, qname):
                    global class_model, t_map
                    if type_name in t_map:
                        class_model = class_model_map.get(type_name)
                        if not class_model:
                            class_model = ComplexTypeClassModel(
                                type_name,
                                [str(t[0].name) for t in t_map[type_name].children()],
                                client_method_name,
                                qname
                            )
                            class_model_map[type_name] = class_model
                            for t in [t[0] for t in t_map[type_name].children()]:
                                add_class_model(t.type[0], str(sd.xlate(t)))

                add_class_model(type_name, qname)

                method_model.append_arg((param[0], qname))
            module_model.append_method(method_model)
    for class_model in class_model_map.values():
        module_model.append_class(class_model)

module_model.save()
