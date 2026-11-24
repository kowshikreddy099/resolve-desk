import json
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from urllib.error import HTTPError
from urllib.request import Request, build_opener, ProxyHandler
import server
from resolver import analyze

class ResolverTests(unittest.TestCase):
    def test_routing(self):
        for text, team in [
            ('My invoice was overcharged','Billing'),('The courier lost our parcel','Delivery'),
            ('Password reset link expired','Account access'),('Dashboard crashes on opening','Technical support'),
            ('Device is defective and cracked','Product quality'),('My card has unauthorized charges','Account security'),
            ('I need someone to help me please','Manual review'),('refund courier','Manual review')]:
            with self.subTest(text=text):
                self.assertEqual(analyze(text)['team'],team)
        self.assertEqual(analyze('My account was hacked')['priority'],'High')

    def test_http_lifecycle(self):
        with tempfile.TemporaryDirectory() as folder:
            server.DATABASE=folder+'/test.sqlite'
            server.initialize()
            with server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler) as http:
                threading.Thread(target=http.serve_forever,daemon=True).start()
                def call(path, body=None):
                    request=Request(f'http://127.0.0.1:{http.server_port}/api/'+path,
                        data=None if body is None else json.dumps(body).encode(),
                        headers={'Content-Type':'application/json'})
                    try:
                        with build_opener(ProxyHandler({})).open(request) as response:
                            return response.status,json.load(response)
                    except HTTPError as error:
                        return error.code,json.load(error)
                try:
                    text={'text':'My card was charged twice'}
                    self.assertEqual(call('analyze',text)[1]['team'],'Billing')
                    with ThreadPoolExecutor(4) as pool:
                        results=list(pool.map(lambda _:call('cases',text),range(4)))
                    self.assertEqual(sorted(status for status,_ in results),[200,200,200,201])
                    cases=call('cases')[1]
                    self.assertEqual(len(cases),1)
                    cid=cases[0]['id']
                    update={'version':1,'status':'Resolved','team':'Billing','note':'Verified reversal.'}
                    self.assertEqual(call('update/'+cid,update)[0],200)
                    self.assertEqual(call('update/'+cid,update)[0],409)
                    self.assertEqual(call('cases')[1][0]['status'],'Resolved')
                    self.assertEqual(len(call('history/'+cid)[1]),2)
                    self.assertEqual(call('cases',{'text':'x'})[0],400)
                finally:
                    http.shutdown()

