import unittest
from wsmodel import ServiceQueryMethodModel, ClientMethodModel


class MethodModelTest(unittest.TestCase):
    def test_query_method_model_body(self):
        s = ServiceQueryMethodModel('foo', 'bar')
        from astmonkey import visitors
        body = s.body()
        assert len(body) == 1
        assert visitors.to_source(body[0]) == 'return bar().service.foo()'

    def test_client_method_model_body(self):
        s = ClientMethodModel('', 'foo', 'http://foo')
        from astmonkey import visitors
        body = s.body()
        assert len(body) == 3
        assert visitors.to_source(body[0]) == 'global foo'
        assert visitors.to_source(body[1]) == 'if (not foo):\n    foo = Client(\'http://foo\')'
        assert visitors.to_source(body[2]) == 'return foo'
