#!/usr/bin/python3
"""
Clase (y programa principal) para un servidor de eco en UDP simple
"""

import socketserver
import socket
import sys
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import time
import json

class SIPRegisterHandler(socketserver.DatagramRequestHandler):
    """Echo server class."""

    dict_users = {}

    def add_user(self, sip_address, expires_value, server_puerto):
        """Add users to the dictionary. Sip address + ip + expires"""
        IP_client, Port_client = self.client_address
        self.dict_users[sip_address] = IP_client + ' ' + str(server_puerto)\
                                        + ' Expires: ' + str(expires_value)


        self.wfile.write(b"SIP/2.0 200 OK\r\n\r\n")

    def delete_user(self, sip_address):
        """Delete users to the dictionary."""
        try:
            del self.dict_users[sip_address]
            self.wfile.write(b'SIP/2.0 200 OK\r\n\r\n')
        except KeyError:
            self.wfile.write(b'SIP/2.0 404 User Not Found\r\n\r\n')

    def expires_users(self):
        """Check if the users have expired, delete them of the dictionary."""
        users_list = list(self.dict_users)
        for user in users_list:
            expires_value = self.dict_users[user].split(': ')[1]
            real_time = time.strftime(
                                    '%Y-%m-%d %H:%M:%S',
                                    time.gmtime(time.time()))
            if expires_value < real_time:
                del self.dict_users[user]

    def register2json(self):
        """Create a .json file"""
        with open('registered.json', "w") as json_file:
            json.dump(self.dict_users, json_file, indent=4)

    def json2registered(self):
        """if there is an .json file read from it"""
        try:
            with open('registered.json', 'r') as json_file:
                self.dict_users = json.load(json_file)
        except FileNotFoundError:
            pass

    def re_mess(self, server_puerto, line):
        # Creamos el socket, lo configuramos y lo atamos a un servidor/puerto
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
            my_socket.connect((server_ip, server_puerto))
            print("Enviando:", line)
            my_socket.send(bytes(line, 'utf-8') + b'\r\n\r\n')
            data = my_socket.recv(1024)
            print('Recibido -- ', data.decode('utf-8'))
            self.wfile.write(data)
        print("Socket terminado.")

    def handle(self):

        self.json2registered()
        self.expires_users()
        line = self.rfile.read()
        line = line.decode('utf-8')
        message_client = line.split('\r\n\r\n')
        print(message_client)
        cabecera = message_client[0].split(' ')
        method = cabecera[0]

        if method == 'INVITE': #Cojo los valores de SDP
            origen = message_client[3].split(' ')
            origen_username = origen[0].split('=')[1]
            origen_ip = origen[1]
            puerto_audio = message_client[6].split(' ')[1]

        sip_user = cabecera[1].split(':')
        sip = sip_user[0]
        version = cabecera[2]
        if sip != 'sip' or version != 'SIP/2.0':
            request = (b"SIP/2.0 400 Bad Request\r\n\r\n")
            self.wfile.write(request)
        else:
            if method == 'REGISTER':
                sip_address = sip_user[1]
                server_puerto = sip_user[2]
                try:
                    expires_value = int(cabecera[4])
                except ValueError:
                    self.wfile.write(b"SIP/2.0 400 error\r\n")
                if expires_value == 0:
                    self.delete_user(sip_address)
                elif expires_value > 0:
                    expires_value = expires_value + time.time()
                    expires_value = time.strftime(
                                                '%Y-%m-%d %H:%M:%S',
                                                time.gmtime(expires_value))
                    self.add_user(sip_address, expires_value, server_puerto)
                    request = request = (b"SIP/2.0 200 OK\r\n\r\n")
                    self.wfile.write(request)
                print(self.dict_users)
                self.register2json()

            if method == 'INVITE':
                user = sip_user[1]
                server_puerto = int((self.dict_users[user]).split(' ')[1])
                if user in self.dict_users:
                    self.re_mess(server_puerto, line)
                else:
                    self.wfile.write('SIP/2.0 404 User Not Found\r\n\r\n')

            else:
                request = (b"SIP/2.0 405 Method Not Allowed\r\n\r\n")
                self.wfile.write(request)



class SmallXMLHandler(ContentHandler):

    def __init__(self):
        self.dicc = {}
        self.elemDict = {
                        "server": ["name", "ip", "puerto"],
                        "database": ["path", "passwdpath"],
                        "rtpaudio": ["puerto"],
                        "log": ["path"]
                        }

    def startElement(self, name, attrs):
        """
        Método que se llama cuando se abre una etiqueta
        """
        if name in self.elemDict:
            for atributo in self.elemDict[name]:
                self.dicc[name +'_'+ atributo] = attrs.get(atributo, "")

    def get_tags(self):
        return(self.dicc)


if __name__ == "__main__":
    # Constantes. Fichero xml por la shell
    try:
        CONFIG = sys.argv[1]
    except (IndexError, ValueError):
        sys.exit('Usage: python3 proxy_registrar.py config')

    # Con el manejador, creo un diccionario 'config' con el fichero xml
    parser = make_parser()
    cHandler = SmallXMLHandler()
    parser.setContentHandler(cHandler)
    parser.parse(open(CONFIG))
    config = cHandler.get_tags()
    #Cojo lo valores que me hacen falta para conectar con el cliente
    server_ip = config['server_ip']
    server_puerto = int(config['server_puerto'])

    proxy = socketserver.UDPServer((server_ip, server_puerto), SIPRegisterHandler)


    print("Lanzando servidor UDP de eco...")
    try:
        proxy.serve_forever()
    except KeyboardInterrupt:
        print("Finalizado servidor")
