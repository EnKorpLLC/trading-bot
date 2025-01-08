from http.server import HTTPServer, SimpleHTTPRequestHandler
import os

def run_server():
    # Change to the frontend directory
    os.chdir('frontend')
    
    # Create server
    server_address = ('', 3000)
    httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
    
    print('Starting server on port 3000...')
    print('Open http://localhost:3000 in your browser')
    httpd.serve_forever()

if __name__ == '__main__':
    run_server() 