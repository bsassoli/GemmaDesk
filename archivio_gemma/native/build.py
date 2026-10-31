"""Build the PDF extractor, embedding worker and native launcher."""
from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import shlex
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RUNTIME = ROOT / 'runtime/llama-b11658'
OBJECTS = HERE / 'obj'
OBJECTS.mkdir(exist_ok=True)
MACOS = sys.platform == 'darwin'


def flags(variable, option):
    if variable in os.environ:
        return shlex.split(os.environ[variable])
    if MACOS:
        # Homebrew's MuPDF ships no pkg-config file.
        prefix = subprocess.check_output(['brew', '--prefix', 'mupdf'], text=True).strip()
        return [f'-I{prefix}/include'] if option == '--cflags' else [f'-L{prefix}/lib', '-lmupdf']
    return shlex.split(subprocess.check_output(['pkg-config', option, 'mupdf'], text=True))


cflags = flags('MUPDF_CFLAGS', '--cflags')
ldflags = flags('MUPDF_LIBS', '--libs')
core = 'common drop pdf layout publication notes model model-layout math math-layout reconstruct edits book kepub epub zip reader'.split()
if MACOS:
    # POSIX mode alone hides the socket flags and path APIs these sources need.
    source_flags = ['-D_DARWIN_C_SOURCE']
    extract_link = ['-lz', '-lc++', '-lm', '-pthread']
    libraries = ('libllama.0.6.0.dylib', 'libmtmd.0.6.0.dylib',
                 'libggml-base.0.26.0.dylib', 'libggml.0.26.0.dylib')
    embed_link = ['-Wl,-rpath,@loader_path/../../runtime/llama-b11658']
else:
    source_flags = ['-D_POSIX_C_SOURCE=200809L']
    extract_link = ['-Wl,--disable-new-dtags,-rpath,$ORIGIN/lib', '-lz', '-lstdc++', '-lm', '-pthread']
    libraries = ('libllama.so.0.6.0', 'libmtmd.so.0.6.0',
                 'libggml-base.so.0.26.0', 'libggml.so.0.26.0')
    embed_link = [f'-Wl,-rpath-link,{RUNTIME}', '-Wl,--disable-new-dtags,-rpath,$ORIGIN/../../runtime/llama-b11658']


def compile_one(name):
    subprocess.run(['cc', '-std=c17', '-O2', *source_flags,
                    f'-I{HERE / "src"}', *cflags, '-c', str(HERE / 'src' / f'{name}.c'),
                    '-o', str(OBJECTS / f'{name}.o')], check=True)


with ThreadPoolExecutor(max_workers=min(8, os.cpu_count() or 1)) as pool:
    list(pool.map(compile_one, core))
subprocess.run(['cc', '-std=c17', '-O2', *(source_flags if MACOS else []), f'-I{HERE / "src"}', *cflags,
                str(HERE / 'extract.c'), *[str(OBJECTS / f'{n}.o') for n in core],
                *ldflags, *extract_link, '-o', str(HERE / 'extract')], check=True)
subprocess.run(['c++', '-std=c++17', '-O2', f'-I{ROOT / "native/include"}',
                str(HERE / 'embed.cpp'),
                *[str(RUNTIME / n) for n in libraries],
                *embed_link, '-o', str(HERE / 'embed')], check=True)
subprocess.run(['cc', '-std=c17', '-O2', '-Wall', '-Wextra', '-Werror',
                str(HERE / 'launcher.c'), '-o', str(ROOT / 'GemmaDesk')], check=True)
