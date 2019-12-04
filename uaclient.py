#!/usr/bin/python3
"""
Programa cliente UDP que abre un socket a un servidor
"""
import sys
import socket
from xml.sax import make_parser
from xml.sax.handler import ContentHandler

class SmallXMLHandler(ContentHandler):

    def __init__(self):
        self.dicc = {}
        self.elemDict = {
                        "account": ["username", "pass"],
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


if __name__ == "__main__":
# Constantes. Fichero xml, metodo a usar y opcion de cada metodo
    try:
        CONFIG = sys.argv[1]
        METHOD  = sys.argv[2]
        OPCION = sys.argv[3]
    except (IndexError, ValueError):
        sys.exit('Usage: client.py config method opcion ')

# Con el manejador, creo un diccionario 'config' con el fichero xml
    parser = make_parser()
    cHandler = SmallXMLHandler()
    parser.setContentHandler(cHandler)
    parser.parse(open(CONFIG))
    config = cHandler.get_tags()

# Compruebo que metodo me ha Introducido el cliente por la shell y elaboro el mensaje
    account_username = config['account_username']
    uaserver_puerto = config['uaserver_puerto']
    uaserver_ip = config['uaserver_ip']
    rtpaudio_puerto = config['rtpaudio_puerto']
    if METHOD == 'REGISTER':
        LINES = (METHOD + ' sip:'+ account_username + ':'+ uaserver_puerto + ' SIP/2.0 ' + 'Expires: '+ OPCION)
    elif METHOD == 'INVITE':
        LINES = (METHOD + ' sip:'+ OPCION + ' SIP/2.0\r\n\r\n')
        LINES = LINES + ('Content-Type: application/sdp\r\n\r\n')
        LINES = LINES + ('v=0\r\n\r\n')
        LINES = LINES + ('o=' + account_username + ' ' + uaserver_ip + '\r\n\r\n')
        LINES = LINES + ('s=misesion\r\n\r\n')
        LINES = LINES + ('t=0\r\n\r\n')
        LINES = LINES + ('m=' + 'audio ' + rtpaudio_puerto + ' RTP')
    elif METHOD == 'BYE':
        print("bye")
    else:
        print("no vale")


    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
        regproxy_ip = config['regproxy_ip']
        regproxy_puerto = int(config['regproxy_puerto'])
        my_socket.connect((regproxy_ip, regproxy_puerto))
        print("Enviando:", LINES)
        my_socket.send(bytes(LINES, 'utf-8') + b'\r\n\r\n')
        data = my_socket.recv(1024)
        print('Recibido -- ', data.decode('utf-8'))

    print("Socket terminado.")
