import version

class server:
    def echo(self, s):
        return s

    def ping(self):
        return version.VERSION_STRING
