import xmlrpc.client
import ssl
import typer

from utils import Data, convert_value_for_xmlrpc, convert_value_from_xmlrpc

app = typer.Typer(help="XML-RPC Client - Call math functions on XML-RPC servers")

class XMLRPCClient:
    """XML-RPC client supporting both HTTP and HTTPS with kwargs support"""

    def __init__(self, server_url, verify_ssl=False):
        """
        Initialize client

        Args:
            server_url: URL of the XML-RPC server
            verify_ssl: Whether to verify SSL certificates (False for self-signed)
        """
        self.server_url = server_url

        if server_url.startswith('https://') and not verify_ssl:
            # Create SSL context that doesn't verify certificates (for self-signed)
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            self.proxy = xmlrpc.client.ServerProxy(server_url, context=context, allow_none=True, use_builtin_types=True)
        else:
            self.proxy = xmlrpc.client.ServerProxy(server_url, allow_none=True, use_builtin_types=True)

    def test_connection(self, verbose: bool = True):
        """Test connection to server"""
        try:
            # Use introspection to test connection since it's enabled
            methods = self.proxy.system.listMethods()
            if verbose:
                print(f"✓ Connected to {self.server_url}")
                print(f"Available methods: {', '.join(methods)}")
            return True
        except Exception as e:
            if verbose:
                print(f"✗ Failed to connect to {self.server_url}: {e}")
            return False

    def _print_result(self, operation, result):
        """Helper method to print results from Data objects"""
        if isinstance(result, dict) and result.get('_is_data_object', False):
            response_code = result.get('response_code', 'unknown')
            actual_result = result.get('result')
            error = result.get('error')

            if error:
                print(f"{operation} - Code: {response_code}, Error: {error}")
            else:
                print(f"{operation} = {actual_result} (Code: {response_code})")
        else:
            print(f"{operation} = {result}")

    def _return_result(self, result):
        if isinstance(result, dict) and result.get('_is_data_object', False):
            response_code = result.get('response_code', 'unknown')
            actual_result = result.get('result')
            error = result.get('error')

            if error:
                raise Exception(f"Error: {error} (Code: {response_code})")
            else:
                # Convert string representations back to int/float for final result
                converted_result = convert_value_from_xmlrpc(actual_result)
                return converted_result
        else:
            # Convert direct results as well
            return convert_value_from_xmlrpc(result)

    def call_math_function(self, operation: str, x: float, y: float, use_data: bool = False):
        """Call a math function on the server"""
        try:
            if use_data:
                result = getattr(self.proxy, operation)(Data(x=x, y=y))
            else:
                # Convert parameters for direct calls
                converted_x = convert_value_for_xmlrpc(x)
                converted_y = convert_value_for_xmlrpc(y)
                result = getattr(self.proxy, operation)(converted_x, converted_y)

            self._print_result(f"{operation}({x}, {y})", result)
            actual_result = self._return_result(result)
            return actual_result
        except Exception as e:
            print(f"Error calling {operation}({x}, {y}): {e}")
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
    data: bool = typer.Option(False, "--data", help="Use Data class for parameters")
):
    """Add two numbers"""
    client = get_client(url)
    client.call_math_function("add", x, y, data)

@app.command()
def subtract(
    x: float,
    y: float,
    url: str = typer.Option("http://localhost:8000", help="Server URL"),
    data: bool = typer.Option(False, "--data", help="Use Data class for parameters")
):
    """Subtract y from x"""
    client = get_client(url)
    client.call_math_function("subtract", x, y, data)

@app.command()
def multiply(
    x: float,
    y: float,
    url: str = typer.Option("http://localhost:8000", help="Server URL"),
    data: bool = typer.Option(False, "--data", help="Use Data class for parameters")
):
    """Multiply two numbers"""
    client = get_client(url)
    client.call_math_function("multiply", x, y, data)

@app.command()
def divide(
    x: float,
    y: float,
    url: str = typer.Option("http://localhost:8000", help="Server URL"),
    data: bool = typer.Option(False, "--data", help="Use Data class for parameters")
):
    """Divide x by y"""
    client = get_client(url)
    client.call_math_function("divide", x, y, data)

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
        python client.py add 10 5 --data
        python client.py multiply 7 6 --url https://localhost:8443
        python client.py list-methods --url https://localhost:8443
    """
    if ctx.invoked_subcommand is None:
        print("Use --help to see available commands")
        print("\nQuick examples:")
        print("  python client.py add 10 5")
        print("  python client.py add 10 5 --data")
        print("  python client.py multiply 7 6 --url https://localhost:8443")
        print("  python client.py list-methods")

if __name__ == "__main__":
    app()
