import ssl

class InsecureSSLContextFactory:
    @staticmethod
    def create():
        context = ssl.SSLContext(ssl.PROTOCOL_TLS)
        context.verify_mode = ssl.CERT_NONE
        context.check_hostname = False  
        return context
