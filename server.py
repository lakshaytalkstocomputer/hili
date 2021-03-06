#!/usr/bin/env python
"""
Test:
curl -X POST -H "Authentication: KEY" -H "Content-Type: application/json" --data '{"foo":"bar"}' http://127.0.0.1:8888
"""

import os
import json
import base64
import hashlib
import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer

parser = argparse.ArgumentParser(description='A simple server to receive and save JSON data')
parser.add_argument('FILE', type=str, help='File to save received data')
parser.add_argument('UPLOAD_DIR', type=str, help='Directory to save uploaded files')
parser.add_argument('-p', '--port', type=int, dest='PORT', default=8888, help='Port for server')
parser.add_argument('-k', '--key', type=str, dest='KEY', default=None, help='Secret key to authenticate clients')
args = parser.parse_args()


class JSONRequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        auth_key = self.headers.get('Authentication')
        if args.KEY and args.KEY != auth_key:
            self.send_response(401)
            self.end_headers()
            self.wfile.write(b'unauthorized')
            return

        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        # Get data
        self.data_string = self.rfile.read(int(self.headers['Content-Length']))
        self.send_response(200)
        self.end_headers()

        data = self.data_string.decode('utf8')
        data = json.loads(data)

        # If a file is included, save it and save only the filename
        if 'file' in data:
            # Assume that data is base64 encoded
            b64 = base64.b64decode(data['file']['data'])

            # Generate file name by hashing file data
            # and extension based on specified content type
            fname = hashlib.sha1(b64).hexdigest()
            ext = data['file']['type'].split('/')[-1]
            fname = '{}.{}'.format(fname, ext)
            with open(os.path.join(args.UPLOAD_DIR, fname), 'wb') as f:
                f.write(b64)

            # Remove original data,
            # save only filename
            del data['file']['data']
            data['file']['name'] = fname

        # Save data
        with open(args.FILE, 'a') as f:
            f.write(json.dumps(data) + '\n')

        # Response
        self.wfile.write(b'ok')
        return

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain; charset=utf-8')
        self.end_headers()

        with open(args.FILE, 'r') as f:
            data = [json.loads(l) for l in f.readlines()]

        text = []
        for d in data:
            item = []
            for k, v in d.items():
                item.append('{}:\t{}'.format(k, v).encode('utf8'))
            text.append(b'\n'.join(item))
        self.wfile.write(b'\n\n'.join(text[::-1]))


if __name__ == '__main__':
    print('Running on port', args.PORT)
    server = HTTPServer(('localhost', args.PORT), JSONRequestHandler)
    server.serve_forever()

