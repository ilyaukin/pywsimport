import ast
from astmonkey import visitors
import os


class ModuleModel(object):
    def __init__(self, filename, client_name='client'):
        if os.path.exists(filename):
            self.module = ast.parse(open(filename).read())
        else:
            self.module = ast.Module(body=[
                ast.ImportFrom(
                    module='suds.client',
                    names=[ast.alias(name='Client', asname=None)],
                    level=None),
                ast.Assign(
                    targets=[ast.Name(id=client_name, ctx=ast.Load())],
                    value=ast.Name(id="None", ctx=ast.Load()))
            ])

        self.fn_list = []
        for node in ast.iter_child_nodes(self.module):
            if isinstance(node, ast.FunctionDef):
                self.fn_list.append(node.name)

        self.filename = filename

    def append_method(self, method_model):
        if method_model.method_name in self.fn_list:
            pass
            # TODO Modify existing method if necessary
        else:
            method_body = method_model.body()
            fd = ast.FunctionDef(name=method_model.method_name,
                                 args=ast.arguments(
                                     args=[ast.Name(id=arg[0], ctx=ast.Param()) for arg in method_model.args],
                                     defaults=[],
                                     vararg=None,
                                     kwarg=None),
                                 body=method_body,
                                 decorator_list=[])
            method_pydoc = method_model.pydoc()
            if method_pydoc:
                fd.body = [ast.Expr(value=ast.Str("\n    ".join([""] + method_pydoc + [""])))] + fd.body
            self.module.body.append(fd)

    def save(self):
        class MyVisitor(visitors.SourceGeneratorNodeVisitor):
            def _super(self):
                return super(MyVisitor, self)

            def visit_Import(self, node):
                self._super().visit_Import(node)
                self._imports = True

            def visit_ImportFrom(self, node):
                self._super().visit_ImportFrom(node)
                self._imports = True

            def visit(self, node):
                if not hasattr(node, 'lineno'):
                    if isinstance(node, ast.FunctionDef):
                        self.newline(node)
                        self.newline(node)
                    if getattr(self, '_imports', False) and \
                            not isinstance(node, (ast.ImportFrom, ast.Import)):
                        self.newline(node)
                        self._imports = False

                self._super().visit(node)

            def visit_Expr(self, node):
                # pydoc formatting
                if isinstance(node.value, ast.Str):
                    self.newline()
                    self.write('"""')
                    self.write(node.value.s)
                    self.write('"""')
                    return
                self._super().visit_Expr(node)

        f = open(self.filename, 'w+')
        visitor = MyVisitor(' ' * 4)
        visitor.visit(self.module)
        f.writelines(visitor.result)
        # f.write(visitors.to_source(self.module))


class MethodModel(object):
    def __init__(self, method_name):
        self.method_name = method_name
        self.args = []

    def append_arg(self, arg):
        self.args.append(arg)

    def body(self):
        return [ast.Pass()]

    def pydoc(self):
        return []


class ServiceQueryMethodModel(MethodModel):
    def __init__(self, method_name, client_method_name, service_name='service'):
        super(ServiceQueryMethodModel, self).__init__(method_name)
        self.client_method_name = client_method_name
        self.service_name = service_name

    def pydoc(self):
        s = ["Send {0} to {1}".format(self.method_name, self.service_name)]
        for arg in self.args:
            s.append(":param {0}: {1}".format(arg[0], arg[1]))
        s.append(":return: query result as is")
        return s

    def body(self):
        return \
            [ast.Return(value=ast.Call(
                func=ast.Attribute(
                    value=ast.Attribute(
                        value=ast.Call(
                            func=ast.Name(id=self.client_method_name, ctx=ast.Load()),
                            args=[],
                            keywords=[],
                            starargs=None,
                            kwargs=None
                        ),
                        attr="service",
                        ctx=ast.Load()),
                    attr=self.method_name,
                    ctx=ast.Load()
                ),
                args=[ast.Name(id=arg[0], ctx=ast.Load()) for arg in self.args],
                keywords=[],
                starargs=None,
                kwargs=None))]


class ClientMethodModel(MethodModel):
    def __init__(self, method_name, client_name, wsdl, service_name='service'):
        super(ClientMethodModel, self).__init__(method_name)
        self.client_name = client_name
        self.wsdl = wsdl
        self.service_name = service_name

    def pydoc(self):
        return ["Make connection to {0} (lazy init)".format(self.service_name),
                ":return: suds client with connection to {0}".format(self.service_name)]

    def body(self):
        return \
            [ast.Global(names=[self.client_name]),
             ast.If(
                 test=ast.UnaryOp(op=ast.Not(), operand=ast.Name(id=self.client_name, ctx=ast.Load())),
                 body=[ast.Assign(
                     targets=[ast.Name(id=self.client_name, ctx=ast.Load())],
                     value=ast.Call(
                         func=ast.Name(id="Client", ctx=ast.Load()),
                         args=[ast.Str(self.wsdl)],
                         keywords=[],
                         starargs=None,
                         kwargs=None
                     ))],
                 orelse=[]
             ),
             ast.Return(value=ast.Name(id=self.client_name, ctx=ast.Load()))]
