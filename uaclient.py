#!/usr/bin/python3
"""Programa cliente UDP que abre un socket a un servidor."""
import sys
import socket
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import os
import hashlib
import time
import threading


class CheckIP():
    """Class to check if ip addess is correct."""

    def __init__(self):
        """Init the boolean."""
        self.ip_correct = True

    def check_ip(self, ip):
        """Check if ip is valid."""
        ip_valid = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '.']
        rango = list(range(256))
        self.ip_correct = True
        try:
            primero = int(ip.split('.')[0])
            segundo = int(ip.split('.')[1])
            tercero = int(ip.split('.')[2])
            cuarto = int(ip.split('.')[3])
            punto = 0
            for character in ip:
                if character not in ip_valid:
                    self.ip_correct = False
                if character == '.':
                    punto = punto + 1
            if punto != 3:
                self.ip_correct = False
            if primero < 127 or primero > 223:
                self.ip_correct = False
            else:
                if segundo not in rango:
                    self.ip_correct = False
                if tercero not in rango:
                    self.ip_correct = False
                if cuarto not in rango:
                    self.ip_correct = False
        except (IndexError, ValueError):
            self.ip_correct = False

        return self.ip_correct


class log_file():
    """Class to write in log file."""

    def __init__(self):
        """Import LOG_PATH of main."""
        from __main__ import LOG_PATH as log
        self.log = log

    def write_log(self, mess):
        """Write the message in file."""
        with open(self.log, 'a') as file_log:
            file_log.write(mess)

    def log_start_finish(self, estado):
        """Write in log file 'Starting' or 'Finishing'."""
        real_time = time.strftime('%Y-%m-%d %H:%M:%S',
                                  time.gmtime(time.time()))
        if estado == 'start':
            mess = (real_time + ' Starting...\r\n')
            self.write_log(mess)
        elif estado == 'finish':
            mess = (real_time + ' Finishing.\r\n')
            self.write_log(mess)

    def log_sent(self, ip, port, message):
        """Write in log file for send messages."""
        real_time = time.strftime('%Y-%m-%d %H:%M:%S',
                                  time.gmtime(time.time()))
        message = message.replace('\r\n', ' ')
        mess = (real_time + ' Sent to ' + ip + ':' + str(port) +
                ': ' + message + '\r\n')
        self.write_log(mess)

    def log_received(self, ip, port, message):
        """Write in log file for received messages."""
        real_time = time.strftime('%Y-%m-%d %H:%M:%S',
                                  time.gmtime(time.time()))
        message = message.replace('\r\n', ' ')
        mess = (real_time + ' Received from ' + ip + ':' + str(port) +
                ': ' + message + '\r\n')
        self.write_log(mess)

    def log_rtp(self, ip, port, audio):
        """Write in log file for send rtp audio."""
        real_time = time.strftime('%Y-%m-%d %H:%M:%S',
                                  time.gmtime(time.time()))
        mess = (real_time + ' Senting to ' + ip + ':' + str(port) +
                ' file: ' + audio + ' by RTP\r\n')
        self.write_log(mess)

    def conexion_refused_error(self, ip, port):
        """For ConnectionRefusedError."""
        real_time = time.strftime('%Y-%m-%d %H:%M:%S',
                                  time.gmtime(time.time()))
        mess = (real_time + ' Error: No server listening at ' + ip +
                ' port ' + str(port) + '\r\n')
        self.write_log(mess)


class SmallXMLHandler(ContentHandler):
    """Class to read .xml file."""

    def __init__(self):
        """Tag diccionary."""
        self.dicc = {}
        self.elemDict = {
                        "account": ["username", "passwd"],
                        "uaserver": ["ip", "puerto"],
                        "rtpaudio": ["puerto"],
                        "regproxy": ["ip", "puerto"],
                        "log": ["path"],
                        "audio": ["path"]
                        }

    def startElement(self, name, attrs):
        """Method to open tag."""
        if name in self.elemDict:
            for atributo in self.elemDict[name]:
                self.dicc[name + '_' + atributo] = attrs.get(atributo, "")

    def get_tags(self):
        """Method to return tag value."""
        return(self.dicc)


def send_message(reply):
    """Send messages."""
    print("Enviando:", reply)
    my_socket.send(bytes(reply, 'utf-8') + b'\r\n\r\n')
    log.log_sent(REGPROXY_IP, REGPROXY_PUERTO, reply)


def send_rtp(origen_ip, origen_puertortp):
    """Send multimedia content by RTP."""
    # Ejecutar y escuchar un string con lo que se ha de ejecutar en la shell
    aEjecutar = "./mp32rtp -i " + origen_ip + " -p " + origen_puertortp
    aEjecutar += " < " + AUDIO_PATH
    aEscuchar = "cvlc rtp://@" + origen_ip + ":" + origen_puertortp + '&'
    hcvlc = threading.Thread(target=os.system(aEscuchar))
    hmp3 = threading.Thread(target=os.system(aejecutar))
    hcvlc.start()
    hmp3.start()
    log.log_rtp(origen_ip, origen_puertortp, AUDIO_PATH)
    return aEscuchar + aejecutar


if __name__ == "__main__":
    # Constantes. Fichero xml, metodo a usar y opcion de cada metodo
    try:
        CONFIG = sys.argv[1]
        METHOD = sys.argv[2]
        OPCION = sys.argv[3]
    except (IndexError, ValueError):
        sys.exit('Usage: client.py config method opcion ')

    # Creo un objeto para evaluar la direccion IP
    CHECKIP = CheckIP()

    # Con el manejador, creo un diccionario 'config' con el fichero xml
    parser = make_parser()
    cHandler = SmallXMLHandler()
    parser.setContentHandler(cHandler)
    parser.parse(open(CONFIG))
    config = cHandler.get_tags()

    # Compruebo que metodo se ha introducido por la shell y elaboro el mensaje
    ACCOUNT_USERNAME = config['account_username']
    ACCOUNT_PASSWD = config['account_passwd']
    UASERVER_IP = config['uaserver_ip']
    UASERVER_PUERTO = config['uaserver_puerto']
    RTPAUDIO_PUERTO = config['rtpaudio_puerto']
    REGPROXY_IP = config['regproxy_ip']
    REGPROXY_PUERTO = int(config['regproxy_puerto'])
    LOG_PATH = config['log_path']
    AUDIO_PATH = config['audio_path']

    if REGPROXY_IP == '' or REGPROXY_IP == 'localhost':
        REGPROXY_IP = '127.0.0.1'
    if UASERVER_IP == '' or UASERVER_IP == 'localhost':
        MY_IP = '127.0.0.1'
    if not CHECKIP.check_ip(REGPROXY_IP) or not CHECKIP.check_ip(UASERVER_IP):
        sys.exit('IP no valida en el fichero de configuración')

    # Creo el log
    log = log_file()
    estado = 'start'
    log.log_start_finish(estado)

    # Envio los mensajes segun el metodo
    if METHOD == 'REGISTER':
        LINES = (METHOD + ' sip:' + ACCOUNT_USERNAME + ':' + UASERVER_PUERTO +
                 ' SIP/2.0\r\n' + 'Expires: ' + OPCION)
    elif METHOD == 'INVITE':
        LINES = (METHOD + ' sip:' + OPCION + ' SIP/2.0\r\n')
        LINES = LINES + ('Content-Type: application/sdp\r\n\r\n')
        LINES = LINES + ('v=0\r\n')
        LINES = LINES + ('o=' + ACCOUNT_USERNAME + ' ' + UASERVER_IP + '\r\n')
        LINES = LINES + ('s=misesion\r\n')
        LINES = LINES + ('t=0\r\n')
        LINES = LINES + ('m=audio ' + RTPAUDIO_PUERTO + ' RTP')
    elif METHOD == 'BYE':
        LINES = (METHOD + ' sip:' + OPCION + ' SIP/2.0')
    else:
        LINES = (METHOD + ' sip:' + OPCION + ' SIP/2.0')

    # Conecto con el servidor
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
        try:
            my_socket.connect((REGPROXY_IP, REGPROXY_PUERTO))
            send_message(LINES)  # Envio el mensaje
            data = my_socket.recv(1024)
            reply = data.decode('utf-8')
            print('Recibido -- ', reply)
        except ConnectionRefusedError:
            log.conexion_refused_error(REGPROXY_IP, REGPROXY_PUERTO)
            estado = 'finish'
            log.log_start_finish(estado)
            sys.exit('Error: No server listening at ' + REGPROXY_IP +
                     ' port ' + str(REGPROXY_PUERTO))

        # Enviamos la autorización al proxy registrar.
        if reply.split('\r\n')[0] == 'SIP/2.0 401 Unauthorized':
            authenticate = reply.split('\r\n')[1]
            nonce = authenticate.split('"')[1]
            h = hashlib.md5(bytes(ACCOUNT_PASSWD + '\r\n', 'utf-8'))
            h.update(bytes(nonce, 'utf-8'))
            digest = h.hexdigest()
            LINE = (METHOD + ' sip:' + ACCOUNT_USERNAME + ':' +
                    UASERVER_PUERTO + ' SIP/2.0\r\n' + 'Expires: ' + OPCION +
                    '\r\n')
            LINE += ('Authorization: Digest response="' + digest + '"')
            send_message(LINE)
            data = my_socket.recv(1024)
            reply = data.decode('utf-8')
            log.log_received(REGPROXY_IP, REGPROXY_PUERTO, reply)
        # Enviamos el mensaje ACK.
        elif METHOD == 'INVITE':
            try:
                ok = 'SIP/2.0 200 OK'
                if reply.split('\r\n\r\n')[2].split('\r\n')[0] == ok:
                    LINE = ('ACK' + ' sip:' + OPCION + ' SIP/2.0')
                    send_message(LINE)
                    # Del sdp de la otra maquina sacamos su ip y su puerto
                    sdp = reply.split('\r\n\r\n')[3].split('\r\n')
                    origen_ip = sdp[1].split(' ')[1]
                    origen_puertortp = sdp[4].split(' ')[1]
                    # Hago el envio de multimedia por RTP
                    send_rtp(origen_ip, origen_puertortp)
            except Exception:
                sys.exit('')

    print("Socket terminado.")
