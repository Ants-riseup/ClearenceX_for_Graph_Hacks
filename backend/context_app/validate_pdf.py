"""Credential-free parser process with Unix memory/CPU limits and parent timeout."""
import sys
from pypdf import PdfReader

if __name__ == '__main__':
    if sys.platform != 'win32':
        import resource
        resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 ** 2, 512 * 1024 ** 2))
        resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
    reader = PdfReader(sys.argv[1], strict=True)
    if reader.is_encrypted or not 1 <= len(reader.pages) <= 25:
        raise SystemExit(2)
