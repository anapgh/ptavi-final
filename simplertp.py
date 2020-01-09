from bitstring import BitArray
import socket
import random

_bps_dict = {'0001': 32000, '0010': 40000, '0011': 48000, '0100':56000,
            '0101': 64000, '0110': 80000, '0111': 96000, '1000': 112000,
            '1001': 128000, '1010': 160000, '1011': 192000, '1100': 224000,
            '1101': 256000, '1110': 320000}

_sample_rate_dict = {'00': 44100, '01': 48000, '10': 32000}

def send_rtp_packet(number, header, payload, ip, port, packets_in_payload):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
        my_socket.connect((ip, port))
        if (number == 0):
            number = 100000000
        try:
            for i in range(number):
                packet = BitArray()
                packet.append(header.version)
                packet.append(header.pad_flag)
                packet.append(header.ext_flag)
                packet.append(header.cc)
                packet.append(header.marker)
                packet.append(header.payload_type)
                packet.append(BitArray(uint = header.seq_number, length = 16))
                packet.append(BitArray(uint = header.timestamp, length = 32))
                packet.append(header.ssrc)
                packet.append(header.csrc)
                if header.ext_flag.bin == '1':
                    print('aqui va la extension')
                print('Tamaño de la cabecera RTP: ' + str(len(packet.bin)))
                # Cuantos paquetes mp3 metemos en el mismo paquete RTP
                for j in range(packets_in_payload):
                    payload._take_mp3_frame()
                    packet.append(BitArray(bin = payload.frame))
                packetBytes = packet.tobytes()
                my_socket.send(packetBytes)
                header._next(payload.frameTimeMs)
        except IndexError:
            pass


class RtpPayloadMp3:  # En principio para MP3

    def set_audio(self, file_path):
        with open(file_path, "rb") as file:
            bytes = file.read()
            self.bits = BitArray(bytes).bin
            self.header_index = self.bits.find('11111111111')

    def _take_mp3_frame(self):

        header = self.bits[self.header_index:self.header_index+32]
        frame_sync = header[0:11]
        version = header[11:13]
        layer = header[13:15]
        protection = header[15]
        bitrate = header[16:20]
        sampling = header[20:22]
        padding = header[22]
        private = header[23]
        channel = header[24:26]
        modeext = header[26:28]
        copyright = header[28]
        original = header[29]
        emphasis = header[30:]

        # Se asume que es version 1 layer 3 (mp3)
        bps = _bps_dict[bitrate]
        sample_rate = _sample_rate_dict[sampling]

        # 144 * bit rate / sample rate * 8 (el 144 es en bytes)
        frame_length = int(144 * 8 * (bps/sample_rate))
        # tiempo por frame en milisegundos
        self.frameTimeMs = int(144/sample_rate * 1000 * 8)
        next_mp3_header_index = self.header_index + frame_length
        self.frame = self.bits[self.header_index:next_mp3_header_index]
        self.header_index = next_mp3_header_index


class RtpHeader:

    def __init__(self):
        self.seq_number = random.randint(1, 10000)  # Aleatorio
        self.timestamp = random.randint(1, 10000)  # Aleatorio

    def set_header(self, version=2, pad_flag=0, ext_flag=0, cc=0, marker=0, payload_type=90, ssrc=1000):
        self.version = BitArray(uint = version, length = 2)
        self.pad_flag = BitArray(uint = pad_flag, length = 1)
        self.ext_flag = BitArray(uint = ext_flag, length = 1)
        self.cc = BitArray(uint = cc, length = 4)
        self.marker = BitArray(uint = marker, length = 1)
        self.payload_type = BitArray(uint = payload_type, length = 7)
        self.ssrc = BitArray(uint = ssrc, length = 32)
        self.csrc = BitArray()

    # def setVersion(self, version):
    #     self.version = BitArray(uint = version, length = 2)
    #
    # def setPaddingFlag(self, pad_flag):
    #     self.pad_flag = BitArray(uint = pad_flag, length = 1)
    #
    # def setExtensionFlag(self, ext_flag):
    #     self.ext_flag = BitArray(uint = ext_flag, length = 1)
    #
    # def setCsrcCount(self, cc):
    #     self.cc = BitArray(uint = cc, length = 4)
    #
    # def setMarker(self, marker):
    #     self.marker = BitArray(uint = marker, length = 1)
    #
    # def setPayloadType(self, payload_type):
    #     self.payload_type = BitArray(uint = marker, length = 7)
    #
    # def setSSRC(self, ssrc):
    #     self.ssrc = BitArray(uint = ssrc, length = 32)

    def setSequenceNumber(self, seq_number):
        self.seq_number = seq_number

    def setTimestamp(self, timestamp):
        self.timestamp = timestamp

    def setCSRC(self, csrcValues):
        for i in range(len(csrcValues)):
            self.csrc.append(BitArray(uint = csrcValues[i], length = 32))

    def _next(self, frameTimeMs):
        self.seq_number += 1
        # Calcular siguiente timestamp
        self.timestamp += int(8000 * (frameTimeMs/1000))


if __name__ == "__main__":
    print("main function")
