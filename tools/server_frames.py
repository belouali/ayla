import http.server, os, sys
ROOT=os.path.dirname(os.path.abspath(__file__))
class H(http.server.SimpleHTTPRequestHandler):
    def __init__(self,*a,**k): super().__init__(*a,directory=ROOT,**k)
    def do_POST(self):
        n=int(self.headers.get('Content-Length',0)); data=self.rfile.read(n)
        if self.path.startswith('/frame/'):
            parts=self.path.split('/')
            if len(parts)==4:
                sub,idx=parts[2],int(parts[3]); d=os.path.join(ROOT,'frames_'+sub); os.makedirs(d,exist_ok=True)
                open(os.path.join(d,'f%05d.'%idx+('png' if sub=='ui' else 'jpg')),'wb').write(data)
            else:
                idx=int(parts[2]); open(os.path.join(ROOT,'frames','f%05d.jpg'%idx),'wb').write(data)
        self.send_response(200); self.send_header('Content-Length','2'); self.end_headers(); self.wfile.write(b'ok')
    def log_message(self,*a): pass
http.server.ThreadingHTTPServer(('127.0.0.1',8765),H).serve_forever()
