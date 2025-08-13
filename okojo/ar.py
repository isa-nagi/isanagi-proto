import io
import struct


class NotArchiveFileError(ValueError):
    pass


class ArchiveFile(object):
    key = (
        'fname',
        'timestamp',
        'uid',
        'gid',
        'fmode',
        'fsize',
    )

    def __init__(self):
        self.fname = str()
        self.timestamp = '0'
        self.uid = '0'
        self.gid = '0'
        self.fmode = 777
        self.fsize = 0
        self.true_fname = None
        self.data = None


class ArchiveObject():
    def __init__(self, f):
        if isinstance(f, str):
            f = open(f, 'rb')
        self.f = f.read()
        self.gh = None
        self._lookup = None
        self.files = list()

    @classmethod
    def is_archive(cls, f):
        if isinstance(f, str):
            f = open(f, 'rb')
        f.seek(0)
        buf = f.read(8)
        if buf != b"!<arch>\x0a":
            return False
        f.seek(0)
        return True

    def read_all(self):
        self.read_global_header()
        self.read_file_header()

    def read_global_header(self):
        gheader = self.f[0:8]
        if gheader != b"!<arch>\x0a":
            raise NotArchiveFileError('binary is not Archive file: {}'.format(gheader))
        self.gh = gheader

    def read_file_header(self):
        offset = 8
        while True:
            binary = self.f[offset:offset + 60]
            st = struct.unpack('16s12s6s6s8s10sBB', binary)
            if bytes(st[-2:]) != b'\x60\x0a':
                raise NotArchiveFileError('binary is not Archive file: offset {}={}'.format(
                    offset + 58, ''.join(f"\\x{s:02x}" for s in st[-2:])))
            arf = ArchiveFile()
            for i, k in enumerate(ArchiveFile.key):
                setattr(arf, k, st[i].rstrip())
            fname = arf.fname.decode()
            fsize = int(arf.fsize, 10)

            if fname == '/':
                self.files.append(arf)
            elif fname == '//':
                self._lookup = self.f[offset + 60:offset + 60 + fsize].decode()
                self.files.append(arf)
            elif fname[0] == '/':
                self.files.append(arf)
            else:
                arf.true_fname = arf.fname.decode().rstrip('/')
                self.files.append(arf)
            data = self.f[offset + 60:offset + 60 + fsize]
            arf.data = io.BytesIO(data)

            offset += 60 + fsize
            if (offset % 2) == 1:
                offset += 1
            if offset >= len(self.f):
                break

    def read_symbol(self, offset):
        for i in range(offset, len(self._lookup)):
            if self._lookup[i] in ('\0', '/'):
                fname = self._lookup[offset:i]
                return fname
        return ""

    def write(self, f):
        binary = b''
        binary += self.gh
        offset = len(self.gh)
        for af in self.files:
            binary += '{:<16s}{:<12s}{:<6s}{:<6s}{:<8s}{:<10s}'.format(
                af.fname.decode(), af.timestamp.decode(),
                af.uid.decode(), af.gid.decode(),
                af.fmode.decode(), af.fsize.decode(),
            ).encode()
            binary += b'\x60\x0a'
            af.data.seek(0)
            data = af.data.read()
            binary += data
            offset += 60 + len(data)
            if (offset % 2) == 1:
                binary += b'\x0a'
        f.write(binary)
