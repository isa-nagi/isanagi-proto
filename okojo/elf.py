import struct


class NotElfFileError(ValueError):
    pass


class ElfHeader(object):
    CLASS_NONE, CLASS_32, CLASS_64 = 0, 1, 2
    DATA_NONE, DATA_2LSB, DATA_2MSB = 0, 1, 2
    ei_key = (
        'ei_mag',
        'ei_class',
        'ei_data',
        'ei_version',
        'ei_osabi',
        'ei_abiversion',
        'ei_pad',
        'ei_nindent',
    )
    e_key = (
        'e_type',
        'e_machine',
        'e_version',
        'e_entry',
        'e_phoff',
        'e_shoff',
        'e_flags',
        'e_ehsize',
        'e_phentsize',
        'e_phnum',
        'e_shentsize',
        'e_shnum',
        'e_shstrndx',
    )

    def __init__(self):
        pass


class ProgramHeader(object):
    PT = ('NULL', 'LOAD', 'DYNAMIC', 'INTERP', 'NOTE', 'SHLIB', 'PHDR', 'TLS',
          'LOOS', 'HIOS', 'LOPROC', 'HIPROC', )
    PF = ('X', 'W', 'R', 'MASKOS', 'MASKPROC')
    p_key_32 = (
        'p_type',
        'p_offset',
        'p_vaddr',
        'p_paddr',
        'p_filesz',
        'p_memsz',
        'p_flags',
        'p_align',
    )
    p_key_64 = (
        'p_type',
        'p_flags',
        'p_offset',
        'p_vaddr',
        'p_paddr',
        'p_filesz',
        'p_memsz',
        'p_align',
    )

    def __init__(self):
        pass


class SectionHeader(object):
    SHT = ('NULL', 'PROGBITS', 'SYMTAB', 'STRTAB', 'RELA', 'HASH', 'DYNAMIC',
           'NOTE', 'NOTIBS', 'REL', 'SHLIB', 'DYNSYM', 'LOPROC', 'HIPROC',
           'LOUSER', 'HIUSER')
    SHF = ('WRITE', 'ALLOC', 'EXECINSTR', 'MASKPROC')
    sh_key = (
        'sh_name',
        'sh_type',
        'sh_flags',
        'sh_addr',
        'sh_offset',
        'sh_size',
        'sh_link',
        'sh_info',
        'sh_addralign',
        'sh_entsize',
    )

    def __init__(self):
        self.name = str()


class SymbolTable(object):
    STT = ('NOTYPE', 'OBJECT', 'FUNC', 'SECTION', 'FILE', 'LOPROC', 'HIPROC')
    STB = ('LOCAL', 'GLOBAL', 'WEAK', 'LOPROC', 'HIPROC')
    STV = ('DEFAULT', 'INTERNAL', 'HIDDEN', 'PROTECTED')
    st_key_32 = (
        'st_name',
        'st_value',
        'st_size',
        'st_info',
        'st_other',
        'st_shndx',
    )
    st_key_64 = (
        'st_name',
        'st_info',
        'st_other',
        'st_shndx',
        'st_value',
        'st_size',
    )

    def __init__(self):
        self.sh = None
        self.name = str()

    @property
    def st_type(self):
        return self.st_info % 16

    @property
    def st_bind(self):
        return self.st_info // 16


class ElfObject():
    EH = ElfHeader
    PH = ProgramHeader
    SH = SectionHeader
    ST = SymbolTable

    def __init__(self, f):
        if isinstance(f, str):
            f = open(f, 'rb')
        self.f = f.read()
        self.e_indent = None
        self.elf_header = None
        self.program_headers = list()
        self.section_headers = list()
        self.symbol_tables = list()

    @property
    def eh(self):
        return self.elf_header

    @property
    def phs(self):
        return self.program_headers

    @property
    def shs(self):
        return self.section_headers

    @property
    def sts(self):
        return self.symbol_tables

    @classmethod
    def is_elf(cls, f):
        if isinstance(f, str):
            f = open(f, 'rb')
        f.seek(0)
        buf = f.read(4)
        if buf != b'\x7fELF':
            return False
        f.seek(0)
        return True

    def read_all(self):
        self.read_elf_header()
        self.read_program_headers()
        self.read_section_headers()
        self.read_symbol_tables()

    def read_elf_header(self):
        binary = self.f[0:64]
        e_indent = struct.unpack('<4sBBBBBBBBBBBB', binary[0:16])
        elf_header = ElfHeader()
        for i, k in enumerate(elf_header.ei_key):
            setattr(elf_header, k, e_indent[i])
        if elf_header.ei_mag != b'\x7fELF':
            raise NotElfFileError('binary is not ELF file: %s' % elf_header.ei_mag)
        if elf_header.ei_class == elf_header.CLASS_32:
            if elf_header.ei_data == elf_header.DATA_2MSB:
                e_values = struct.unpack('>HHLLLLLHHHHHH', binary[16:52])
            else:
                e_values = struct.unpack('<HHLLLLLHHHHHH', binary[16:52])
        elif elf_header.ei_class == elf_header.CLASS_64:
            if elf_header.ei_data == elf_header.DATA_2MSB:
                e_values = struct.unpack('>HHLQQQLHHHHHH', binary[16:64])
            else:
                e_values = struct.unpack('<HHLQQQLHHHHHH', binary[16:64])
        else:
            raise ValueError('ELF file is invalid class')
        for i, k in enumerate(elf_header.e_key):
            setattr(elf_header, k, e_values[i])
        self.elf_header = elf_header
        return self.elf_header

    def read_program_headers(self):
        elf_header = self.elf_header
        f_idx = elf_header.e_phoff
        phs = list()
        for ph_idx in range(elf_header.e_phnum):
            binary = self.f[f_idx:f_idx + elf_header.e_phentsize]
            f_idx += elf_header.e_phentsize
            ph = ProgramHeader()
            if elf_header.ei_class == elf_header.CLASS_32:
                if elf_header.ei_data == elf_header.DATA_2MSB:
                    ph_values = struct.unpack('>LLLLLLLL', binary)
                else:
                    ph_values = struct.unpack('<LLLLLLLL', binary)
                for i, k in enumerate(ph.p_key_32):
                    setattr(ph, k, ph_values[i])
            elif elf_header.ei_class == elf_header.CLASS_64:
                if elf_header.ei_data == elf_header.DATA_2MSB:
                    ph_values = struct.unpack('>LLQQQQQQ', binary)
                else:
                    ph_values = struct.unpack('<LLQQQQQQ', binary)
                for i, k in enumerate(ph.p_key_64):
                    setattr(ph, k, ph_values[i])
            phs.append(ph)
        self.program_headers = phs
        return self.program_headers

    def read_section_headers(self):
        elf_header = self.elf_header
        f_idx = elf_header.e_shoff
        shs = list()
        for sh_idx in range(elf_header.e_shnum):
            binary = self.f[f_idx:f_idx + elf_header.e_shentsize]
            f_idx += elf_header.e_shentsize
            if elf_header.ei_class == elf_header.CLASS_32:
                if elf_header.ei_data == elf_header.DATA_2MSB:
                    sh_values = struct.unpack('>LLLLLLLLLL', binary)
                else:
                    sh_values = struct.unpack('<LLLLLLLLLL', binary)
            elif elf_header.ei_class == elf_header.CLASS_64:
                if elf_header.ei_data == elf_header.DATA_2MSB:
                    sh_values = struct.unpack('>LLQQQQLLQQ', binary)
                else:
                    sh_values = struct.unpack('<LLQQQQLLQQ', binary)
            sh = SectionHeader()
            for i, k in enumerate(sh.sh_key):
                setattr(sh, k, sh_values[i])
            shs.append(sh)
        # read 'section name table' section, and set true name
        shstrtab_sh = shs[elf_header.e_shstrndx]
        f_idx = shstrtab_sh.sh_offset
        binary = self.f[f_idx:f_idx + shstrtab_sh.sh_size]
        for sh in shs:
            offset = sh.sh_name
            for i in range(offset, len(binary)):
                if binary[i] == b'\x00' or binary[i] == 0:
                    break
            sh.name = binary[offset:i].decode()
        self.section_headers = shs
        return self.section_headers

    def read_symbol_tables(self):
        elf_header = self.elf_header
        shs = self.section_headers
        st_shs = list()
        for i, sh in enumerate(shs):
            if sh.sh_type == SectionHeader.SHT.index('SYMTAB'):
                st_shs.append(sh)
                break
        sts = list()
        for sh in st_shs:
            f_idx = sh.sh_offset
            for sti in range(sh.sh_size // sh.sh_entsize):
                binary = self.f[f_idx:f_idx + sh.sh_entsize]
                f_idx += sh.sh_entsize
                if elf_header.ei_class == elf_header.CLASS_32:
                    if elf_header.ei_data == elf_header.DATA_2MSB:
                        st_values = struct.unpack('>LLLBBH', binary)
                    else:
                        st_values = struct.unpack('<LLLBBH', binary)
                    st_key = SymbolTable.st_key_32
                elif elf_header.ei_class == elf_header.CLASS_64:
                    if elf_header.ei_data == elf_header.DATA_2MSB:
                        st_values = struct.unpack('>LBBHQQ', binary)
                    else:
                        st_values = struct.unpack('<LBBHQQ', binary)
                    st_key = SymbolTable.st_key_64
                st = SymbolTable()
                for i, k in enumerate(st_key):
                    setattr(st, k, st_values[i])
                st.sh = sh
                sts.append(st)
        # read 'symbol name table' section, and set true name
        for st in sts:
            ststrtab_sh = shs[st.sh.sh_link]
            f_idx = ststrtab_sh.sh_offset
            binary = self.f[f_idx:f_idx + ststrtab_sh.sh_size]
            f_idx += ststrtab_sh.sh_size
            offset = st.st_name
            if offset == 0:
                st.name = ''
            else:
                for i in range(offset, len(binary)):
                    if binary[i] == b'\x00' or binary[i] == 0:
                        break
                st.name = binary[offset:i].decode()
        self.symbol_tables = sts
        return self.symbol_tables

    def write(self, f):
        binary = b''
        # elf header
        elf_header = self.elf_header
        args = [getattr(self.eh, k) for k in self.eh.ei_key] + [0, 0, 0, 0, 0]
        binary += struct.pack('<4sBBBBBBBBBBBB', *args)
        args = [getattr(self.eh, k) for k in self.eh.e_key]
        if elf_header.ei_class == elf_header.CLASS_32:
            if elf_header.ei_data == elf_header.DATA_2MSB:
                binary += struct.pack('>HHLLLLLHHHHHH', *args)
            else:
                binary += struct.pack('<HHLLLLLHHHHHH', *args)
        elif elf_header.ei_class == elf_header.CLASS_64:
            if elf_header.ei_data == elf_header.DATA_2MSB:
                binary += struct.pack('>HHLQQQLHHHHHH', *args)
            else:
                binary += struct.pack('<HHLQQQLHHHHHH', *args)
        # program headers
        for ph_idx in range(elf_header.e_phnum):
            ph = self.program_headers[ph_idx]
            if elf_header.ei_class == elf_header.CLASS_32:
                args = [getattr(ph, k) for k in ph.p_key_32]
                if elf_header.ei_data == elf_header.DATA_2MSB:
                    ph_values = struct.pack('>LLLLLLLL', *args)
                else:
                    ph_values = struct.pack('<LLLLLLLL', *args)
                binary += ph_values
            elif elf_header.ei_class == elf_header.CLASS_64:
                args = [getattr(ph, k) for k in ph.p_key_64]
                if elf_header.ei_data == elf_header.DATA_2MSB:
                    ph_values = struct.pack('>LLQQQQQQ', *args)
                else:
                    ph_values = struct.pack('<LLQQQQQQ', *args)
                binary += ph_values
        # section data
        binary += self.f[len(binary):elf_header.e_shoff]
        # section headers
        for sh_idx in range(elf_header.e_shnum):
            sh = self.section_headers[sh_idx]
            args = [getattr(sh, k) for k in sh.sh_key]
            if elf_header.ei_class == elf_header.CLASS_32:
                if elf_header.ei_data == elf_header.DATA_2MSB:
                    sh_values = struct.pack('>LLLLLLLLLL', *args)
                else:
                    sh_values = struct.pack('<LLLLLLLLLL', *args)
            elif elf_header.ei_class == elf_header.CLASS_64:
                if elf_header.ei_data == elf_header.DATA_2MSB:
                    sh_values = struct.pack('>LLQQQQLLQQ', *args)
                else:
                    sh_values = struct.pack('<LLQQQQLLQQ', *args)
            binary += sh_values
        f.write(binary)
