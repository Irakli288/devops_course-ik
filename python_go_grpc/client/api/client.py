import grpc

from . import api_pb2, api_pb2_grpc


class Certs:
    root = None
    cert = None
    key = None

    def __init__(self, root, cert, key):
        self.root = open(root, 'rb').read()
        self.cert = open(cert, 'rb').read()
        self.key = open(key, 'rb').read()


class Client:
    rpc = None

    def __init__(self, addr: str, crt: Certs):
        creds = grpc.ssl_channel_credentials(crt.root, crt.key, crt.cert)
        channel = grpc.secure_channel(addr, creds)
        self.rpc = api_pb2_grpc.DiceServiceStub(channel)

    def roll_die(self) -> int:
        return self.rpc.RollDie(api_pb2.RollDieRequest()).value
