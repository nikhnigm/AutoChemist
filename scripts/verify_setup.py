import modal
import platform

app = modal.App("test-handshake")

# This function runs in the cloud (Modal's servers)
@app.function()
def remote_echo(text: str):
    node_name = platform.node()
    return f"Connected: Processed '{text}' on Cloud Node: {node_name}"