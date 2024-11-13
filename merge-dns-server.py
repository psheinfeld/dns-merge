from dnslib import DNSRecord, DNSHeader, DNSQuestion, RR, QTYPE
from dnslib.server import DNSServer, BaseResolver
import socket
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class ForwardingResolver(BaseResolver):
    def __init__(self, upstream_servers):
        self.upstream_servers = upstream_servers

    def query_upstream(self, request, upstream_server):
        try:
            upstream_address = (upstream_server, 53)
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(request.pack(), upstream_address)
            response_data, _ = sock.recvfrom(4096)
            response = DNSRecord.parse(response_data)
            return response
        except Exception as e:
            logging.warning(f"Failed to get response from {upstream_server}: {e}")
            return None

    def resolve(self, request, handler):
        # Log the incoming request
        logging.info(f"Received request: {request.q.qname}")

        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(self.query_upstream, request, server) for server in self.upstream_servers]
            for future in as_completed(futures):
                response = future.result()
                if response and response.rr:
                    return response

        # If all upstream servers fail or return empty responses, return an empty response
        return DNSRecord(DNSHeader(id=request.header.id, qr=1, aa=1, ra=1), q=request.q)

if __name__ == "__main__":
    # Read upstream servers from environment variable
    upstream_servers = os.getenv("UPSTREAM_SERVERS", "8.8.8.8,8.8.4.4").split(",")
    logging.info(f"Using upstream servers: {upstream_servers}")
    
    resolver = ForwardingResolver(upstream_servers)
    server = DNSServer(resolver, port=53, address="0.0.0.0")
    server.start_thread()

    logging.info("DNS server started")

    try:
        while True:
            pass
    except KeyboardInterrupt:
        logging.info("DNS server stopped")
