#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Clase para un servidor de eco en UDP simple."""

import socketserver
import sys
import os
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
from proxy_registrar import CheckIP
from uaclient import log_file, SmallXMLHandler, CheckIP


class SIPHandler(socketserver.DatagramRequestHandler):
    """Server class."""

    RTP_dict = {}

    def handle(self):
        """Server handler."""
        line = self.rfile.read()
        line = line.decode('utf-8')
        message_client = line.split('\r\n')
        print(message_client)
        cabecera = message_client[0].split(' ')
        method = cabecera[0]
        sip = cabecera[1].split(':')
        opcion = sip[1]
        sip = sip[0]
        version = cabecera[2]
        IP_client, Port_client = self.client_address
        log.log_received(IP_client, Port_client, line)
        if sip != 'sip' or version != 'SIP/2.0':
            reply = (b"SIP/2.0 400 Bad Request\r\n\r\n")
            self.wfile.write(reply)
        else:
            if method == 'INVITE':
                reply = (b'SIP/2.0 100 Trying \r\n\r\n')
                reply = (reply + b'SIP/2.0 180 Ringing\r\n\r\n')
                reply = (reply + b'SIP/2.0 200 OK\r\n')
                self.wfile.write(reply)
                log.log_sent(IP_client, Port_client, reply.decode('utf-8'))
                origen_ip = message_client[6].split(' ')[1]
                origen_puertortp = message_client[9].split(' ')[1]
                self.RTP_dict['origen_usernam'] = (origen_ip, origen_puertortp)
                sdp = ('Content-Type: application/sdp\r\n\r\n' + 'v=0\r\n' +
                       'o=' + ACCOUNT_USERNAME + ' ' + UASERVER_IP + '\r\n' +
                       's=session\r\n' + 't=0\r\n' + 'm=audio ' +
                       str(RTPAUDIO_PUERTO + ' RTP\r\n\r\n'))
                self.wfile.write(bytes(sdp, 'utf-8'))
                log.log_sent(IP_client, Port_client, sdp)

            elif method == 'ACK':
                origen_ip = self.RTP_dict['origen_usernam'][0]
                o_puertortp = self.RTP_dict['origen_usernam'][1]
                # aEjecutar es un string para ejecutar en la shell
                aEjecutar = "./mp32rtp -i " + origen_ip + " -p " + o_puertortp
                aEjecutar += " < " + AUDIO_PATH
                print("Vamos a ejecutar", aEjecutar)
                log.log_rtp(origen_ip, o_puertortp, AUDIO_PATH)
                os.system(aEjecutar)

            elif method == 'BYE':
                reply = (b"SIP/2.0 200 OK\r\n\r\n")
                self.wfile.write(reply)
                log.log_sent(IP_client, Port_client, reply.decode('utf-8'))

            else:
                reply = (b"SIP/2.0 405 Method Not Allowed\r\n\r\n")
                self.wfile.write(reply)
                log.log_sent(IP_client, Port_client, reply.decode('utf-8'))


if __name__ == "__main__":
    # Constantes. Fichero xml por la shell
    try:
        CONFIG = sys.argv[1]
    except (IndexError, ValueError):
        sys.exit('Usage: python3 uaserver.py config')

    # Creo un objeto para evaluar la direccion IP
    CHECKIP = CheckIP()

    # Con el manejador, creo un diccionario 'config' con el fichero xml
    parser = make_parser()
    cHandler = SmallXMLHandler()
    parser.setContentHandler(cHandler)
    parser.parse(open(CONFIG))
    config = cHandler.get_tags()
    # Cojo lo valores que me hacen falta para conectar con el cliente
    ACCOUNT_USERNAME = config['account_username']
    ACCOUNT_PASSWD = config['account_passwd']
    UASERVER_IP = config['uaserver_ip']
    UASERVER_PUERTO = int(config['uaserver_puerto'])
    RTPAUDIO_PUERTO = config['rtpaudio_puerto']
    REGPROXY_IP = config['regproxy_ip']
    REGPROXY_PUERTO = int(config['regproxy_puerto'])
    LOG_PATH = config['log_path']
    AUDIO_PATH = config['audio_path']

    if UASERVER_IP == '' or UASERVER_IP == 'localhost':
        SERVER_IP = '127.0.0.1'
    if not CHECKIP.check_ip(UASERVER_IP):
        sys.exit('IP no valida en el fichero de configuración')

    # Creo el objeto de la clase log, para escribir en el fichero
    log = log_file()

    server = socketserver.UDPServer((UASERVER_IP, UASERVER_PUERTO), SIPHandler)

    try:
        print('Listening...')
        estado = 'start'
        log.log_start_finish(estado)
        server.serve_forever()
    except KeyboardInterrupt:
        estado = 'finish'
        log.log_start_finish(estado)
        print("Finalizado servidor")
