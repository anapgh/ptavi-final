#!/usr/bin/python3
"""
Clase (y programa principal) para un servidor de eco en UDP simple
"""

import socketserver
import sys
from xml.sax import make_parser
from xml.sax.handler import ContentHandler

class SIPRegisterHandler(socketserver.DatagramRequestHandler):
    """Echo server class."""

    def handle(self):
        for line in self.rfile:
            message_client = line.decode('utf-8')
            print(message_client)

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
