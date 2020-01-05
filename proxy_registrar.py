#!/usr/bin/python3
"""Programa para un servidor de eco en UDP simple."""

import socketserver
import socket
import sys
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import time
import json
import random
import hashlib
from uaclient import log_file, CheckIP


class SIPRegisterHandler(socketserver.DatagramRequestHandler):
    """Server class."""

    dict_users = {}
    dict_passwd = {}
    dict_nonce = {}

    def add_user(self, sip_address, expires_value, server_puerto):
        """Add users to the dictionary."""
        IP_client, Port_client = self.client_address
        real_time = time.strftime('%Y-%m-%d %H:%M:%S',
                                  time.gmtime(time.time()))
        self.dict_users[sip_address] = (IP_client, str(server_puerto),
                                        real_time, str(expires_value))

        self.register2json()
        reply = (b"SIP/2.0 200 OK\r\n\r\n")
        self.wfile.write(reply)
        log.log_sent(IP_client, Port_client, reply.decode('utf-8'))
        print(self.dict_users)

    def delete_user(self, sip_address):
        """Delete users to the dictionary."""
        IP_client, Port_client = self.client_address
        try:
            del self.dict_users[sip_address]
            self.register2json()
            reply = (b'SIP/2.0 200 OK\r\n\r\n')
            self.wfile.write(reply)
            log.log_sent(IP_client, Port_client, reply.decode('utf-8'))
        except KeyError:
            self.wfile.write(b'SIP/2.0 404 User Not Found\r\n\r\n')
        print(self.dict_users)

    def expires_users(self):
        """Check if the users have expired, delete them of the dictionary."""
        users_list = list(self.dict_users)
        for user in users_list:
            expires_value = self.dict_users[user][3]
            real_time = time.strftime(
                                    '%Y-%m-%d %H:%M:%S',
                                    time.gmtime(time.time()))
            if expires_value < real_time:
                del self.dict_users[user]

    def register2json(self):
        """Create a .json file."""
        self.expires_users()
        with open('registered.json', "w") as json_file:
            json.dump(self.dict_users, json_file, indent=4)

    def json2registered(self):
        """if there is an .json file read from it."""
        try:
            with open('registered.json', 'r') as json_file:
                self.dict_users = json.load(json_file)
        except FileNotFoundError:
            pass

    def json2passwd(self):
        """Read .json file with the password of clients."""
        try:
            with open(DATABASE_PASSWDPATH, 'r') as json_file:
                self.dict_passwd = json.load(json_file)
        except FileNotFoundError:
            pass

    def re_mess(self, line, user):
        """Proxy function."""
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
            server_ip = self.dict_users[user][0]
            server_puerto = int(self.dict_users[user][1])
            try:
                my_socket.connect((server_ip, server_puerto))
                mens = line.split('\r\n\r\n')
                mens_proxy = mens[0] + '\r\nVia: SIP/2.0/UDP ' + SERVER_IP
                mens_proxy += ':' + str(SERVER_PUERTO) + '\r\n'
                mens_proxy += 'User-Agent: ' + SERVER_NAME + '\r\n\r\n'
                mens_proxy += mens[1]
                print("Enviando:", mens_proxy)
                my_socket.send(bytes(mens_proxy, 'utf-8') + b'\r\n\r\n')
                data = my_socket.recv(1024)
                print('Recibido -- ', data.decode('utf-8'))
                self.wfile.write(data)
            except ConnectionRefusedError:
                print('Conexion fallida con el servidor')
                log.conexion_refused_error(server_ip, server_puerto)

            print("Socket terminado.")

    def get_digest(self, user):
        """Get the digest with the passwords of dictionary."""
        digest = 0
        nonce = str(self.dict_nonce[user])
        if user in self.dict_passwd:
            passwd = self.dict_passwd[user]
            passwd = passwd[0]
            h = hashlib.md5(bytes(str(passwd) + '\r\n', 'utf-8'))
            h.update(bytes(nonce, 'utf-8'))
            digest = h.hexdigest()
        return digest

    def handle(self):
        """Proxy handler."""
        self.json2registered()
        self.json2passwd()
        self.expires_users()
        line = self.rfile.read()
        line = line.decode('utf-8')
        message_client = line.split('\r\n')
        print(message_client)
        cabecera = message_client[0].split(' ')
        print(cabecera)
        method = cabecera[0]
        sip_user = cabecera[1].split(':')
        sip = sip_user[0]
        version = cabecera[2]
        IP_client, Port_client = self.client_address
        log.log_received(IP_client, Port_client, line)
        if sip != 'sip' or version != 'SIP/2.0':
            reply = (b"SIP/2.0 400 Bad Request\r\n\r\n")
            self.wfile.write(reply)
            log.log_sent(IP_client, Port_client, reply.decode('utf-8'))
        else:
            if method == 'REGISTER':
                sip_address = sip_user[1]
                server_puerto = sip_user[2]
                try:
                    expires_value = int(message_client[1].split(': ')[1])
                except ValueError:
                    self.wfile.write(b"SIP/2.0 400 error\r\n\r\n")
                if expires_value == 0:
                    self.delete_user(sip_address)
                    print(self.dict_users)
                if len(message_client) == 4 and expires_value != 0:
                    nonce = random.randint(10**19, 10**20)
                    self.dict_nonce[sip_address] = nonce
                    reply = (b'SIP/2.0 401 Unauthorized\r\n')
                    reply += (b'WWW-Authenticate: Digest nonce="')
                    reply += ((bytes(str(nonce) + '"', 'utf-8')) + b'\r\n\r\n')
                    self.wfile.write(reply)
                    log.log_sent(IP_client, Port_client, reply.decode('utf-8'))
                elif len(message_client) == 5:
                    sip_digest = message_client[2].split('"')[1]
                    digest = self.get_digest(sip_address)
                    print(digest)
                    if sip_address in self.dict_nonce:
                        nonce = self.dict_nonce
                    if sip_digest == digest:
                        if expires_value > 0:
                            expires_value = expires_value + time.time()
                            gmtime = (time.gmtime(expires_value))
                            expires_value = time.strftime('%Y-%m-%d %H:%M:%S',
                                                          gmtime)
                            self.add_user(sip_address, expires_value,
                                          server_puerto)
                    else:
                        reply = (b'SIP/2.0 401 Unauthorized\r\n')
                        reply += (b'WWW-Authenticate: Digest nonce="')
                        reply += ((bytes(str(nonce) + '"', 'utf-8')) +
                                  b'\r\n\r\n')
                        self.wfile.write(reply)
                        log.log_sent(IP_client, Port_client,
                                     reply.decode('utf-8'))
            elif method == 'INVITE' or 'BYE' or 'ACK':
                user = sip_user[1]
                if user in self.dict_users:
                    self.re_mess(line, user)
                else:
                    reply = (b'SIP/2.0 404 User Not Found\r\n\r\n')
                    self.wfile.write(reply)
                    log.log_sent(IP_client, Port_client, reply.decode('utf-8'))
            else:
                reply = (b"SIP/2.0 405 Method Not Allowed\r\n\r\n")
                self.wfile.write(reply)
                log.log_sent(IP_client, Port_client, reply.decode('utf-8'))


class SmallXMLHandler(ContentHandler):
    """Class to read .xml file."""

    def __init__(self):
        """Tag diccionary."""
        self.dicc = {}
        self.elemDict = {
                        "server": ["name", "ip", "puerto"],
                        "database": ["path", "passwdpath"],
                        "rtpaudio": ["puerto"],
                        "log": ["path"]
                        }

    def startElement(self, name, attrs):
        """Method to open tag."""
        if name in self.elemDict:
            for atributo in self.elemDict[name]:
                self.dicc[name + '_' + atributo] = attrs.get(atributo, "")

    def get_tags(self):
        """Method to return tag value."""
        return(self.dicc)


if __name__ == "__main__":
    # Constantes. Fichero xml por la shell
    try:
        CONFIG = sys.argv[1]
    except (IndexError, ValueError):
        sys.exit('Usage: python3 proxy_registrar.py config')

    # Creo un objeto para evaluar la direccion IP
    CHECKIP = CheckIP()

    # Con el manejador, creo un diccionario 'config' con el fichero xml
    parser = make_parser()
    cHandler = SmallXMLHandler()
    parser.setContentHandler(cHandler)
    parser.parse(open(CONFIG))
    config = cHandler.get_tags()
    # Cojo lo valores que me hacen falta para conectar con el cliente
    SERVER_NAME = config['server_name']
    SERVER_IP = config['server_ip']
    SERVER_PUERTO = int(config['server_puerto'])
    DATABASE_PATH = config['database_path']
    DATABASE_PASSWDPATH = config['database_passwdpath']
    LOG_PATH = config['log_path']

    try:
        if SERVER_IP == '' or SERVER_IP == 'localhost':
            SERVER_IP = '127.0.0.1'
        if not CHECKIP.check_ip(SERVER_IP):
            sys.exit('IP no valida en el fichero de configuración')
    except (IndexError, ValueError):
        sys.exit('Usage: python3 proxy_registar.py config.')

    # Creo el log
    log = log_file()

    proxy = socketserver.UDPServer((SERVER_IP, SERVER_PUERTO),
                                   SIPRegisterHandler)

    try:
        print('Server ' + SERVER_NAME + ' listening at port ' +
              str(SERVER_PUERTO) + '...')
        estado = 'start'
        log.log_start_finish(estado)
        proxy.serve_forever()
    except KeyboardInterrupt:
        estado = 'finish'
        log.log_start_finish(estado)
        print("Finalizado servidor")
