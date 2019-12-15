#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Clase para un servidor de eco en UDP simple."""

import socketserver
import sys
import os
from xml.sax import make_parser
from xml.sax.handler import ContentHandler


class SmallXMLHandler(ContentHandler):


    def __init__(self):
        self.dicc = {}
        self.elemDict = {
                        "account": ["username", "passwd"],
                        "uaserver": ["ip", "puerto"],
                        "rtpaudio": ["puerto"],
                        "regproxy": ["ip","puerto"],
                        "log": ["path"],
                        "audio": ["path"]
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


class SIPHandler(socketserver.DatagramRequestHandler):
    """Echo server class."""

    def handle(self):

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
            sip = cabecera[1].split(':')
            opcion = sip[1]
            sip =sip[0]
            version = cabecera[2]
            if sip != 'sip' or version != 'SIP/2.0':
                request = (b"SIP/2.0 400 Bad Request\r\n\r\n")
                self.wfile.write(request)
            else:
                if method == 'INVITE':
                    request = (b'SIP/2.0 100 Trying \r\n\r\n')
                    request = (request + b'SIP/2.0 180 Ringing\r\n\r\n')
                    request = (request + b'SIP/2.0 200 OK\r\n\r\n')
                    self.wfile.write(request)
                    origen_ip = message_client[3].split(' ')[1]
                    origen_puerto = message_client[6].split(' ')[1]
                    print(origen_ip)
                    print(origen_puerto)
                    sdp = ('Content-Type: application/sdp\r\n\r\n' +
                       'v=0\r\n' + 'o=' + ACCOUNT_USERNAME + ' ' + UASERVER_IP +
                       '\r\n' + 's=session\r\n' + 't=0\r\n' +
                       'm=audio ' + str(RTPAUDIO_PUERTO + ' RTP\r\n\r\n'))
                    self.wfile.write(bytes(sdp, 'utf-8'))

                if method == 'BYE':
                    request = (b"SIP/2.0 200 OK\r\n\r\n")
                    self.wfile.write(request)
                if method == 'ACK':
                    request = (b'ACK SIP/2.0')
                    self.wfile.write(request)
                else:
                    print('pepe: ' + method + 'adios')
                    request = (b"SIP/2.0 405 Method Not Allowed\r\n\r\n")
                    self.wfile.write(request)



if __name__ == "__main__":
    # Constantes. Fichero xml por la shell
    try:
        CONFIG = sys.argv[1]
    except (IndexError, ValueError):
        sys.exit('Usage: python3 uaserver.py config')

    #Con el manejador, creo un diccionario 'config' con el fichero xml
    parser = make_parser()
    cHandler = SmallXMLHandler()
    parser.setContentHandler(cHandler)
    parser.parse(open(CONFIG))
    config = cHandler.get_tags()
    #Cojo lo valores que me hacen falta para conectar con el cliente
    ACCOUNT_USERNAME = config['account_username']
    ACCOUNT_PASSWD = config['account_passwd']
    UASERVER_IP= config['uaserver_ip']
    UASERVER_PUERTO = int(config['uaserver_puerto'])
    RTPAUDIO_PUERTO = config['rtpaudio_puerto']
    REGPROXY_IP = config['regproxy_ip']
    REGPROXY_PUERTO = int(config['regproxy_puerto'])
    #LOG_PATH = config['log_path']
    #LOG_AUDIO = config['log_audio']


    proxy = socketserver.UDPServer((UASERVER_IP, UASERVER_PUERTO), SIPHandler)

    print("Lanzando servidor UDP de eco...")
    try:
        proxy.serve_forever()
    except KeyboardInterrupt:
        print("Finalizado servidor")
