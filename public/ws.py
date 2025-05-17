import socket
import asyncio as a
import binascii as b
import random as r
from collections import namedtuple
import re
import struct
import ssl

OP_CONT = const(0x0)
OP_TEXT = const(0x1)
OP_BYTES = const(0x2)
OP_CLOSE = const(0x8)
OP_PING = const(0x9)
OP_PONG = const(0xa)

CLOSE_OK = const(1000)
CLOSE_GOING_AWAY = const(1001)
CLOSE_PROTOCOL_ERROR = const(1002)
CLOSE_DATA_NOT_SUPPORTED = const(1003)
CLOSE_BAD_DATA = const(1007)
CLOSE_POLICY_VIOLATION = const(1008)
CLOSE_TOO_BIG = const(1009)
CLOSE_MISSING_EXTN = const(1010)
CLOSE_BAD_CONDITION = const(1011)

URL_RE = re.compile(r'(wss|ws)://([A-Za-z0-9-\.]+)(?:\:([0-9]+))?(/.+)?')
URI = namedtuple('URI', ('protocol', 'hostname', 'port', 'path'))

class AsyncWebsocketClient:
    def __init__(self, ms_delay_for_read: int = 5):
        self._open = False
        self.delay_read = ms_delay_for_read
        self._lock_for_open = a.Lock()
        self.sock = None

    async def open(self, new_val: bool = None):
        await self._lock_for_open.acquire()
        if new_val is not None:
            if not new_val and self.sock:
                self.sock.close()
                self.sock = None
            self._open = new_val
        to_return = self._open
        self._lock_for_open.release()
        return to_return

    async def close(self):
        return await self.open(False)

    def urlparse(self, uri):
        match = URL_RE.match(uri)
        if match:
            protocol, host, port, path = match.group(1), match.group(2), match.group(3), match.group(4)
            if protocol not in ['ws', 'wss']:
                raise ValueError('Scheme {} is invalid'.format(protocol))
            if port is None:
                port = (80, 443)[protocol == 'wss']
            return URI(protocol, host, int(port), path)

    async def a_readline(self):
        line = None
        while line is None:
            line = self.sock.readline()
            await a.sleep_ms(self.delay_read)
        return line

    async def a_read(self, size: int = None):
        if size == 0:
            return b''
        chunks = []
        while True:
            bts = self.sock.read(size)
            await a.sleep_ms(self.delay_read)
            if bts is None:
                continue
            if len(bts) == 0:
                break
            chunks.append(bts)
            size -= len(bts)
            if size is None or size == 0:
                break
        return b''.join(chunks)

    async def handshake(self, uri, headers=[], keyfile=None, certfile=None, cafile=None, cert_reqs=0):
        if self.sock:
            self.close()
        self.sock = socket.socket()
        self.uri = self.urlparse(uri)
        ai = socket.getaddrinfo(self.uri.hostname, self.uri.port)
        addr = ai[0][4]
        self.sock.connect(addr)
        self.sock.setblocking(False)
        if self.uri.protocol == 'wss':
            cadata = None
            if cafile is not None:
                with open(cafile, 'rb') as f:
                    cadata = f.read()
            self.sock = ssl.wrap_socket(
                self.sock, server_side=False,
                key=keyfile, cert=certfile,
                cert_reqs=cert_reqs,
                cadata=cadata,
                server_hostname=self.uri.hostname
            )
        def send_header(header, *args):
            self.sock.write(header % args + '\r\n')
        key = b.b2a_base64(bytes(r.getrandbits(8) for _ in range(16)))[:-1]
        send_header(b'GET %s HTTP/1.1', self.uri.path or '/')
        send_header(b'Host: %s:%s', self.uri.hostname, self.uri.port)
        send_header(b'Connection: Upgrade')
        send_header(b'Upgrade: websocket')
        send_header(b'Sec-WebSocket-Key: %s', key)
        send_header(b'Sec-WebSocket-Version: 13')
        send_header(b'Origin: http://{hostname}:{port}'.format(hostname=self.uri.hostname, port=self.uri.port))
        for keyh, value in headers:
            send_header(b'%s: %s', keyh, value)
        send_header(b'')
        line = await self.a_readline()
        header = line[:-2]
        if not header.startswith(b'HTTP/1.1 101 '):
            raise Exception(header)
        while header:
            line = await self.a_readline()
            header = line[:-2]
        return await self.open(True)

    async def read_frame(self, max_size=None):
        byte1, byte2 = struct.unpack('!BB', await self.a_read(2))
        fin = bool(byte1 & 0x80)
        opcode = byte1 & 0x0f
        mask = bool(byte2 & (1 << 7))
        length = byte2 & 0x7f
        if length == 126:
            length, = struct.unpack('!H', await self.a_read(2))
        elif length == 127:
            length, = struct.unpack('!Q', await self.a_read(8))
        if mask:
            mask_bits = await self.a_read(4)
        try:
            data = await self.a_read(length)
        except MemoryError:
            self.close(code=CLOSE_TOO_BIG)
            return True, OP_CLOSE, None
        if mask:
            data = bytes(b ^ mask_bits[i % 4] for i, b in enumerate(data))
        return fin, opcode, data

    def write_frame(self, opcode, data=b''):
        fin = True
        mask = True
        length = len(data)
        byte1 = 0x80 | opcode
        byte2 = 0x80
        if length < 126:
            byte2 |= length
            self.sock.write(struct.pack('!BB', byte1, byte2))
        elif length < (1 << 16):
            byte2 |= 126
            self.sock.write(struct.pack('!BBH', byte1, byte2, length))
        elif length < (1 << 64):
            byte2 |= 127
            self.sock.write(struct.pack('!BBQ', byte1, byte2, length))
        else:
            raise ValueError()
        mask_bits = struct.pack('!I', r.getrandbits(32))
        self.sock.write(mask_bits)
        data = bytes(b ^ mask_bits[i % 4] for i, b in enumerate(data))
        self.sock.write(data)

    async def recv(self):
        while await self.open():
            try:
                fin, opcode, data = await self.read_frame()
            except Exception as ex:
                print('Exception in recv while reading frame:', ex)
                await self.open(False)
                return
            if not fin:
                raise NotImplementedError()
            if opcode == OP_TEXT:
                return data.decode('utf-8')
            elif opcode == OP_BYTES:
                return data
            elif opcode == OP_CLOSE:
                await self.open(False)
                return
            elif opcode == OP_PONG:
                continue
            elif opcode == OP_PING:
                try:
                    self.write_frame(OP_PONG, data)
                    continue
                except Exception as ex:
                    print('Error sending pong frame:', ex)
                    await self.open(False)
                    return
            elif opcode == OP_CONT:
                raise NotImplementedError(opcode)
            else:
                raise ValueError(opcode)

    async def send(self, buf):
        if not await self.open():
            return
        if isinstance(buf, str):
            opcode = OP_TEXT
            buf = buf.encode('utf-8')
        elif isinstance(buf, bytes):
            opcode = OP_BYTES
        else:
            raise TypeError()
        self.write_frame(opcode, buf)
