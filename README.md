# 🔐 XML-RPC Client-Server Example with SSL

## 📝 Overview
This project demonstrates a simple XML-RPC client-server architecture in Python, secured with SSL. The server exposes remote procedures, and the client communicates with the server to invoke these procedures.

## 📁 Project Structure
- `server.py`: XML-RPC server implementation with SSL.
- `client.py`: XML-RPC client implementation.
- `utils.py`: Utility functions used by server and client.
- `requirements.txt`: Python dependencies.
- `server.crt`, `server.key`: SSL certificate and key for secure communication.
- `logs/`: Directory for server and client logs.
- `tests/`: Contains test cases.

## 📦 Requirements
- Python 3.8+
- Packages listed in `requirements.txt`

## ⚙️ Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## 🖥️ Running the Server
Start the XML-RPC server:
```bash
python server.py both
```
The server will start and listen for incoming XML-RPC requests over SSL.

## 💻 Running the Client
In a separate terminal, run:
```bash
python client.py add 2 2
```
The client will connect to the server and perform remote procedure calls.

## 🧪 Testing
Run the test suite using pytest:
```bash
pytest tests/
```

## 📄 License

MIT License
