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

for sd in client.sd:
    t_map = dict()
    class_model_map = dict()
    for t in [t[0] for t in sd.types]:
        if isinstance(t, Complex):
            t_map[t.qname] = t
    for port in sd.ports:
        for method in port[1]:
            method_name = method[0]
            method_model = ServiceQueryMethodModel(method_name, client_method_name, service_name=args.name)
            for param in method[1]:
                param_type = param[1]
                qname = param_type.type
                type_name_with_prefix = str(param_type.root.get('type'))

                def get_attr_name(t):
                    if t[0].isattr():
                        return '_%s' % t[0].name
                    return t[0].name

                def add_class_model(qname, type_name_with_prefix):
                    global class_model, t_map
                    if qname in t_map:
                        class_model = class_model_map.get(qname)
                        if not class_model:
                            class_model = ComplexTypeClassModel(
                                str(qname[0]),
                                [get_attr_name(t) for t in t_map[qname].resolve()],
                                client_method_name,
                                type_name_with_prefix
                            )
                            class_model_map[qname] = class_model
                            for t in [t[0] for t in t_map[qname].children()]:
                                add_class_model(t.type, str(t.root.get('type')))

                add_class_model(qname, type_name_with_prefix)

                method_model.append_arg((param[0], type_name_with_prefix, param_type.nillable))
            module_model.append_method(method_model)
    for class_model in class_model_map.values():
        module_model.append_class(class_model)

module_model.save()
