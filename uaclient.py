#!/usr/bin/python3
"""
Programa cliente UDP que abre un socket a un servidor
"""
import sys
import socket
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import os
import hashlib


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

def send_message(request):
    """Enviar mensajes."""
    print("Enviando:", request)
    my_socket.send(bytes(request, 'utf-8') + b'\r\n\r\n')


def send_rtp(origen_ip, origen_puertortp):
    """Enviar y escuchar el contenido multimedia mediante RTP."""
    # aEjecutar es un string con lo que se ha de ejecutar en la shell
    aEjecutar = "./mp32rtp -i " + origen_ip + " -p " + origen_puertortp
    aEjecutar += " < " + AUDIO_PATH
    print("Vamos a ejecutar", aEjecutar)

    os.system(aEjecutar)


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
    ACCOUNT_USERNAME = config['account_username']
    ACCOUNT_PASSWD = config['account_passwd']
    UASERVER_IP = config['uaserver_ip']
    UASERVER_PUERTO = config['uaserver_puerto']
    RTPAUDIO_PUERTO = config['rtpaudio_puerto']
    REGPROXY_IP = config['regproxy_ip']
    REGPROXY_PUERTO = int(config['regproxy_puerto'])
    LOG_PATH = config['log_path']
    AUDIO_PATH = config['audio_path']

# Creo el log


# Envio los mensajes segun el metodo
    if METHOD == 'REGISTER':
        LINES = (METHOD + ' sip:'+ ACCOUNT_USERNAME + ':'+ UASERVER_PUERTO + ' SIP/2.0 ' + 'Expires: '+ OPCION)
    elif METHOD == 'INVITE':
        LINES = (METHOD + ' sip:'+ OPCION + ' SIP/2.0\r\n\r\n')
        LINES = LINES + ('Content-Type: application/sdp\r\n\r\n')
        LINES = LINES + ('v=0\r\n\r\n')
        LINES = LINES + ('o=' + ACCOUNT_USERNAME + ' ' + UASERVER_IP + '\r\n\r\n')
        LINES = LINES + ('s=misesion\r\n\r\n')
        LINES = LINES + ('t=0\r\n\r\n')
        LINES = LINES + ('m=audio ' + RTPAUDIO_PUERTO  + ' RTP')
    elif METHOD == 'BYE':
        LINES = (METHOD + ' sip:' + OPCION + ' SIP/2.0')
    else:
        LINES = (METHOD + ' sip:' + OPCION + ' SIP/2.0')

# Conecto con el servidor
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
        my_socket.connect((REGPROXY_IP, REGPROXY_PUERTO))
        send_message(LINES) # Envio el mensaje
        data = my_socket.recv(1024)
        reply  = data.decode('utf-8')
        print('Recibido -- ', reply)

        # Enviamos la autorización al proxy registrar.
        if reply.split('\r\n\r\n')[0] == 'SIP/2.0 401 Unauthorized':
            authenticate = reply.split('\r\n\r\n')[1]
            nonce = authenticate.split('"')[1]
            h = hashlib.md5(bytes(ACCOUNT_PASSWD  + '\r\n', 'utf-8'))
            h.update(bytes(nonce, 'utf-8'))
            digest = h.hexdigest()
            LINE = (METHOD + ' sip:'+ ACCOUNT_USERNAME + ':'+
                UASERVER_PUERTO + ' SIP/2.0 ' + 'Expires: '+ OPCION + '\r\n\r\n')
            LINE += ('Authorization: Digest response="' + digest + '"')

            send_message(LINE)
            data = my_socket.recv(1024)
            reply = data.decode('utf-8')
        # Enviamos el mensaje ACK.
        elif reply.split('\r\n\r\n')[2] == 'SIP/2.0 200 OK':
            LINE = ('ACK' + ' sip:' + OPCION + ' SIP/2.0')
            send_message(LINE)
            # Del sdp de la otra maquina sacamos su ip y su puerto
            sdp = reply.split('\r\n\r\n')[4].split('\r\n')
            origen_ip = sdp[1].split(' ')[1]
            origen_puertortp = sdp[4].split(' ')[1]
            # Hago el envio de multimedia por RTP
            send_rtp(origen_ip, origen_puertortp)


    print("Socket terminado.")
