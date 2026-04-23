import ssl
import os
import sys
import datetime
from django.core.management.commands.runserver import Command as RunserverCommand
from django.core.servers.basehttp import WSGIRequestHandler, WSGIServer
from django.utils import autoreload

class SecureHTTPServer(WSGIServer):
    def __init__(self, address, handler_cls, certfile, keyfile, ipv6=False):
        super().__init__(address, handler_cls, ipv6=ipv6)
        
        # Modern SSL implementation for Python 3.12+
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(certfile, keyfile)
        
        # wrap_socket is now a method of the context
        self.socket = context.wrap_socket(self.socket, server_side=True)

class Command(RunserverCommand):
    help = "Run a Django development server over HTTPS"

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument('--certificate', default=None, help="Path to the SSL certificate")
        parser.add_argument('--key', default=None, help="Path to the SSL key")

    def handle(self, *args, **options):
        self.certfile = options.get('certificate')
        self.keyfile = options.get('key')
        
        # Try to find default certificates if not provided
        if not self.certfile or not self.keyfile:
            # Look for django-sslserver's default certs
            try:
                import sslserver
                base_path = os.path.dirname(sslserver.__file__)
                if not self.certfile:
                    self.certfile = os.path.join(base_path, 'certs', 'development.crt')
                if not self.keyfile:
                    self.keyfile = os.path.join(base_path, 'certs', 'development.key')
            except ImportError:
                pass

        if not self.certfile or not os.path.exists(self.certfile):
            raise ValueError(f"Certificate file not found: {self.certfile}")
        if not self.keyfile or not os.path.exists(self.keyfile):
            raise ValueError(f"Key file not found: {self.keyfile}")

        super().handle(*args, **options)

    def inner_run(self, *args, **options):
        # Override the server creation to use our SecureHTTPServer
        from django.conf import settings
        
        threading = options['use_threading']
        shutdown_message = options.get('shutdown_message', '')
        quit_command = 'CTRL-BREAK' if os.name == 'nt' else 'CONTROL-C'

        self.stdout.write("Validating models...\n\n")
        self.check(display_num_errors=True)
        self.stdout.write((
            "%(started_at)s\n"
            "Django version %(version)s, using settings %(settings)r\n"
            "Starting development server at https://%(addr)s:%(port)s/\n"
            "Using SSL certificate: %(cert)s\n"
            "Using SSL key: %(key)s\n"
            "Quit the server with %(quit_command)s.\n"
        ) % {
            "started_at": datetime.datetime.now().strftime('%B %d, %Y - %X'),
            "version": self.get_version(),
            "settings": settings.SETTINGS_MODULE,
            "addr": self.addr,
            "port": self.port,
            "quit_command": quit_command,
            "cert": self.certfile,
            "key": self.keyfile,
        })

        # Set up the server
        try:
            handler = self.get_handler(*args, **options)
            server = SecureHTTPServer(
                (self.addr, int(self.port)),
                WSGIRequestHandler,
                self.certfile,
                self.keyfile,
                ipv6=self.use_ipv6
            )
            server.set_app(handler)
            server.serve_forever()
        except OSError as e:
            # Port is probably in use
            error_code = e.errno
            if error_code == 10048:
                self.stderr.write("Error: That port is already in use.\n")
            else:
                self.stderr.write(str(e))
            os._exit(1)
        except KeyboardInterrupt:
            if shutdown_message:
                self.stdout.write(shutdown_message)
            sys.exit(0)
