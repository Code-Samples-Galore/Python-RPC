import ssl
from xmlrpc.server import SimpleXMLRPCServer
from socketserver import ThreadingMixIn
import threading
import time
import os
import typer
from loguru import logger

from utils import generate_self_signed_cert, Data, convert_value_from_xmlrpc, convert_value_for_xmlrpc

# Ensure logs directory exists
logs_dir = "logs"
os.makedirs(logs_dir, exist_ok=True)

# Configure loguru logger
logger.add(os.path.join(logs_dir, "xmlrpc_server.log"), rotation="1 MB", level="INFO")

app = typer.Typer(help="XML-RPC Server - Start HTTP and/or HTTPS servers")

class ThreadedXMLRPCServer(ThreadingMixIn, SimpleXMLRPCServer):
    """Threaded XML-RPC server with custom dispatch for kwargs support"""
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, allow_none=True, use_builtin_types=True, logRequests=False)
        logger.info(f"Initialized XML-RPC server on {args[0]}")

    def _dispatch(self, method, params):
        """Custom dispatch method to handle Data objects for args and kwargs support"""
        try:
            # Handle introspection methods specially - don't wrap their results
            if method.startswith('system.'):
                return super()._dispatch(method, params)

            # Get the function
            func = self.funcs.get(method)
            if func is None:
                # Try to get from instance
                if self.instance is not None:
                    func = getattr(self.instance, method, None)

            if func is None:
                error_msg = f'Method "{method}" is not supported!'
                logger.error(error_msg)
                return Data(response_code=404, error=error_msg).__dict__

            # Process parameters to extract Data objects and convert types
            args = []
            kwargs = {}

            for param in params:
                # Check if this is a Data object (serialized as dict with _is_data_object marker)
                if isinstance(param, dict) and param.get('_is_data_object', False):
                    # This is a Data object - extract args and kwargs and convert types
                    data_args = param.get('args', ())
                    data_kwargs = param.get('kwargs', {})
                    # Convert string representations back to int/float
                    converted_args = [convert_value_from_xmlrpc(arg) for arg in data_args]
                    converted_kwargs = {k: convert_value_from_xmlrpc(v) for k, v in data_kwargs.items()}
                    args.extend(converted_args)
                    kwargs.update(converted_kwargs)
                    logger.debug(f"Unpacked Data object: args={converted_args}, kwargs={converted_kwargs}")
                else:
                    # Regular parameter - convert if needed
                    converted_param = convert_value_from_xmlrpc(param)
                    args.append(converted_param)

            # Call function with unpacked args and kwargs
            if kwargs:
                logger.debug(f"Calling {method} with args={args}, kwargs={kwargs}")
                result = func(*args, **kwargs)
            else:
                logger.debug(f"Calling {method} with args={args}")
                result = func(*args)

            # Always wrap the result in a successful Data object with result attribute
            # Convert int/float results to strings for XML-RPC transmission
            return Data(response_code=200, result=result).__dict__

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error in dispatch for method {method}: {error_msg}")
            return Data(response_code=400, error=error_msg).__dict__

class MathFunctions:
    """Simple math functions for XML-RPC testing"""

    def add(self, x, y):
        result = x + y
        logger.debug(f"add({x}, {y}) = {result}")
        return result

    def subtract(self, x, y):
        result = x - y
        logger.debug(f"subtract({x}, {y}) = {result}")
        return result

    def multiply(self, x, y):
        result = x * y
        logger.debug(f"multiply({x}, {y}) = {result}")
        return result

    def divide(self, x, y):
        if y == 0:
            logger.warning(f"Division by zero attempted: {x} / {y}")
            raise ValueError("Cannot divide by zero")
        result = x / y
        logger.debug(f"divide({x}, {y}) = {result}")
        return result

def register_functions(server):
    """Register functions with the XML-RPC server"""
    logger.info("Registering XML-RPC functions")

    # Register math functions
    math_functions = MathFunctions()
    server.register_instance(math_functions)

    # Enable introspection functions
    server.register_introspection_functions()

    logger.info("Successfully registered math functions and introspection")

def start_http_server(host="localhost", port=8000):
    """Start HTTP XML-RPC server"""
    try:
        logger.info(f"Starting HTTP XML-RPC server on {host}:{port}")

        server = ThreadedXMLRPCServer((host, port))
        register_functions(server)

        logger.success(f"HTTP XML-RPC server started successfully on {host}:{port}")
        logger.info("Server is ready to accept connections")

        server.serve_forever()
    except OSError as e:
        logger.error(f"Failed to start HTTP server on {host}:{port}: {e}")
        raise
    except KeyboardInterrupt:
        logger.info("HTTP server shutdown requested")
    except Exception as e:
        logger.error(f"Unexpected error in HTTP server: {e}")
        raise
    finally:
        logger.info("HTTP server stopped")

def start_https_server(host="localhost", port=8443):
    """Start HTTPS XML-RPC server"""
    try:
        logger.info(f"Starting HTTPS XML-RPC server on {host}:{port}")

        # Generate self-signed certificate if it doesn't exist
        cert_file = "server.crt"
        key_file = "server.key"

        if not os.path.exists(cert_file) or not os.path.exists(key_file):
            logger.info("SSL certificate not found, generating self-signed certificate")
            generate_self_signed_cert()
            logger.success("Self-signed certificate generated successfully")
        else:
            logger.info("Using existing SSL certificate")

        server = ThreadedXMLRPCServer((host, port))
        register_functions(server)

        # Create SSL context
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(cert_file, key_file)

        # Wrap the server socket with SSL
        server.socket = context.wrap_socket(server.socket, server_side=True)

        logger.success(f"HTTPS XML-RPC server started successfully on {host}:{port}")
        logger.info("Server is ready to accept secure connections")

        server.serve_forever()
    except OSError as e:
        logger.error(f"Failed to start HTTPS server on {host}:{port}: {e}")
        raise
    except ssl.SSLError as e:
        logger.error(f"SSL configuration error: {e}")
        raise
    except KeyboardInterrupt:
        logger.info("HTTPS server shutdown requested")
    except Exception as e:
        logger.error(f"Unexpected error in HTTPS server: {e}")
        raise
    finally:
        logger.info("HTTPS server stopped")

@app.command()
def http(host: str = "localhost", port: int = 8000):
    """Start HTTP XML-RPC server"""
    logger.info(f"HTTP server command invoked with host={host}, port={port}")
    start_http_server(host, port)

@app.command()
def https(host: str = "localhost", port: int = 8443):
    """Start HTTPS XML-RPC server"""
    logger.info(f"HTTPS server command invoked with host={host}, port={port}")
    start_https_server(host, port)

@app.command()
def both(
    http_host: str = "localhost",
    http_port: int = 8000,
    https_host: str = "localhost",
    https_port: int = 8443
):
    """Start both HTTP and HTTPS servers"""
    logger.info(f"Starting both servers - HTTP on {http_host}:{http_port}, HTTPS on {https_host}:{https_port}")

    # Start both servers in separate threads
    http_thread = threading.Thread(target=start_http_server, args=(http_host, http_port), daemon=True)
    https_thread = threading.Thread(target=start_https_server, args=(https_host, https_port), daemon=True)

    try:
        http_thread.start()
        https_thread.start()

        logger.success("Both HTTP and HTTPS servers started successfully")
        logger.info("Press Ctrl+C to stop both servers")

        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutdown signal received for both servers")
        print("\nShutting down servers...")
    except Exception as e:
        logger.error(f"Error running both servers: {e}")
        raise
    finally:
        logger.info("Both servers stopped")

@logger.catch
def main():
    """Main entry point for the XML-RPC server application"""
    typer.echo("Starting XML-RPC server application...")
    app()

if __name__ == "__main__":
    main()
