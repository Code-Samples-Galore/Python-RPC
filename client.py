import os
import xmlrpc.client
import ssl
import typer
from loguru import logger

from utils import Data, convert_value_from_xmlrpc

# Ensure logs directory exists
logs_dir = "logs"
os.makedirs(logs_dir, exist_ok=True)

# Configure loguru logger
logger.add(os.path.join(logs_dir, "client.log"), rotation="1 MB", level="INFO")

app = typer.Typer(help="XML-RPC Client - Call math functions on XML-RPC servers")

class DataServerProxy(xmlrpc.client.ServerProxy):
    """ServerProxy that automatically wraps arguments in Data for non-system methods."""

    class _Method:
        def __init__(self, send, name):
            self.__send = send
            self.__name = name

        def __call__(self, *args, **kwargs):
            logger.debug("DataServerProxy._Method.__call__: method={}, args={}, kwargs={}", self.__name, args, kwargs)

            # Don't wrap system/introspection calls
            if self.__name.startswith("system."):
                logger.debug("System method detected: {}, passing args as-is", self.__name)
                return self.__send(self.__name, args)

            # If the first argument is already a Data object, pass as-is
            if args and isinstance(args[0], Data):
                logger.debug("Data object detected as first argument, passing as-is: {}", args[0])
                return self.__send(self.__name, args)

            # Otherwise, wrap all args/kwargs in a Data object
            data_obj = Data(*args, **kwargs)
            logger.debug("Created Data object: {}", data_obj)
            logger.debug("Sending to server: method={}, data={}", self.__name, data_obj)

            result = self.__send(self.__name, (data_obj,))
            logger.debug("Received result from server: {}", result)
            return result

        def __getattr__(self, name):
            full_name = f"{self.__name}.{name}"
            logger.debug("DataServerProxy._Method.__getattr__: creating method {}", full_name)
            return DataServerProxy._Method(self.__send, full_name)

    def __getattr__(self, name):
        # Prevent infinite recursion by checking for internal attributes first
        if name.startswith('_'):
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

        logger.debug("DataServerProxy.__getattr__: creating method {}", name)
        return DataServerProxy._Method(self._ServerProxy__request, name)

    def __init__(self, uri, **kwargs):
        logger.debug("Initializing DataServerProxy with uri={}, kwargs={}", uri, kwargs)
        super().__init__(uri, **kwargs)
        logger.info("DataServerProxy initialized for {}", uri)

class XMLRPCClient:
    """XML-RPC client supporting both HTTP and HTTPS with kwargs support"""

    def __init__(self, server_url, verify_ssl=False):
        """
        Initialize client

        Args:
            server_url: URL of the XML-RPC server
            verify_ssl: Whether to verify SSL certificates (False for self-signed)
        """
        logger.debug("Initializing XMLRPCClient with server_url={}, verify_ssl={}", server_url, verify_ssl)
        self.server_url = server_url

        if server_url.startswith('https://') and not verify_ssl:
            # Create SSL context that doesn't verify certificates (for self-signed)
            logger.debug("Creating SSL context for HTTPS with disabled certificate verification")
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            self.proxy = DataServerProxy(server_url, context=context, allow_none=True, use_builtin_types=True)
        else:
            logger.debug("Creating standard proxy for HTTP")
            self.proxy = DataServerProxy(server_url, allow_none=True, use_builtin_types=True)

        logger.info("XMLRPCClient initialized for {}", server_url)

    def test_connection(self, verbose: bool = True):
        """Test connection to server"""
        logger.debug("Testing connection to {}", self.server_url)
        try:
            # Use introspection to test connection since it's enabled
            methods = self.proxy.system.listMethods()
            if verbose:
                print(f"✓ Connected to {self.server_url}")
                print(f"Available methods: {', '.join(methods)}")
            logger.success("Connection test successful for {}", self.server_url)
            return True
        except Exception as e:
            if verbose:
                print(f"✗ Failed to connect to {self.server_url}: {e}")
            logger.error("Connection test failed for {}: {}", self.server_url, e)
            return False

    def _print_result(self, operation, result):
        """Helper method to print results from Data objects"""
        logger.debug("_print_result called with operation={}, result={}", operation, result)
        if isinstance(result, dict) and result.get('_is_data_object', False):
            response_code = result.get('response_code', 'unknown')
            actual_result = result.get('result')
            error = result.get('error')

            if error:
                print(f"{operation} - Code: {response_code}, Error: {error}")
                logger.warning("Operation {} returned error: {} (Code: {})", operation, error, response_code)
            else:
                print(f"{operation} = {actual_result} (Code: {response_code})")
                logger.info("Operation {} successful: {} (Code: {})", operation, actual_result, response_code)
        else:
            print(f"{operation} = {result}")
            logger.info("Operation {} returned: {}", operation, result)

    def _return_result(self, result):
        logger.debug("_return_result called with result={}", result)
        if isinstance(result, dict) and result.get('_is_data_object', False):
            response_code = result.get('response_code', 'unknown')
            actual_result = result.get('result')
            error = result.get('error')

            if error:
                logger.error("Server returned error: {} (Code: {})", error, response_code)
                raise Exception(f"Error: {error} (Code: {response_code})")
            else:
                # Convert string representations back to int/float for final result
                converted_result = convert_value_from_xmlrpc(actual_result)
                logger.debug("Converted result from {} to {}", actual_result, converted_result)
                return converted_result
        else:
            # Convert direct results as well
            converted_result = convert_value_from_xmlrpc(result)
            logger.debug("Converted direct result from {} to {}", result, converted_result)
            return converted_result

    def call_math_function(self, operation: str, x: float, y: float):
        """Call a math function on the server"""
        logger.debug("call_math_function: operation={}, x={}, y={}", operation, x, y)
        try:
            # Arguments are automatically wrapped in Data by DataServerProxy
            result = getattr(self.proxy, operation)(x=x, y=y)

            self._print_result(f"{operation}({x}, {y})", result)
            actual_result = self._return_result(result)
            logger.success("Math function {}({}, {}) completed successfully: {}", operation, x, y, actual_result)
            return actual_result
        except Exception as e:
            print(f"Error calling {operation}({x}, {y}): {e}")
            logger.error("Error calling {}({}, {}): {}", operation, x, y, e)
            return None

def get_client(url: str) -> XMLRPCClient:
    """Get a configured client for the given URL"""
    client = XMLRPCClient(url, verify_ssl=False)
    if not client.test_connection(verbose=False):
        raise typer.Exit(1)
    return client

@app.command()
def add(
    x: float,
    y: float,
    url: str = typer.Option("http://localhost:8000", help="Server URL"),
):
    """Add two numbers"""
    client = get_client(url)
    client.call_math_function("add", x, y)

@app.command()
def subtract(
    x: float,
    y: float,
    url: str = typer.Option("http://localhost:8000", help="Server URL"),
):
    """Subtract y from x"""
    client = get_client(url)
    client.call_math_function("subtract", x, y)

@app.command()
def multiply(
    x: float,
    y: float,
    url: str = typer.Option("http://localhost:8000", help="Server URL"),
):
    """Multiply two numbers"""
    client = get_client(url)
    client.call_math_function("multiply", x, y)

@app.command()
def divide(
    x: float,
    y: float,
    url: str = typer.Option("http://localhost:8000", help="Server URL"),
):
    """Divide x by y"""
    client = get_client(url)
    client.call_math_function("divide", x, y)

@app.command()
def list_methods(
    url: str = typer.Option("http://localhost:8000", help="Server URL")
):
    """List available methods on the server"""
    client = get_client(url)
    try:
        methods = client.proxy.system.listMethods()
        print("Available methods:")
        for method in methods:
            print(f"  - {method}")
    except Exception as e:
        print(f"Error listing methods: {e}")

@app.command()
def test(
    url: str = typer.Option("http://localhost:8000", help="Server URL")
):
    """Test connection to server"""
    client = XMLRPCClient(url, verify_ssl=False)
    if client.test_connection():
        print("Connection test successful!")
    else:
        raise typer.Exit(1)

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """XML-RPC Client - Call math functions on XML-RPC servers

    Examples:
        python client.py add 10 5
        python client.py multiply 7 6 --url https://localhost:8443
        python client.py list-methods --url https://localhost:8443
    """
    if ctx.invoked_subcommand is None:
        print("Use --help to see available commands")
        print("\nQuick examples:")
        print("  python client.py add 10 5")
        print("  python client.py multiply 7 6 --url https://localhost:8443")
        print("  python client.py list-methods")


if __name__ == "__main__":
    with logger.catch():
        app()
