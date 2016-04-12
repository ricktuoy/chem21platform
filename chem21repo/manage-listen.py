import os
import importlib

from twisted.internet import protocol
from twisted.internet import reactor
from twisted.internet import utils


class Call(protocol.Protocol):

    """Twisted protocol to send command to Django project manager script"""

    def __init__(self, exc, *args, **kwargs):
        """ Builds protocol, gets path to manager from Django project settings
        Args:
            settings_path(str): Python path to Django project settings
            command(str): command to send to the Django manager
        """
        self.exc = exc
        self.args = args

    def connectionMade(self):
        output = utils.getProcessOutput(self.exc, self.args)
        output.addCallbacks(self.writeResponse, self.noResponse)

    def writeResponse(self, resp):
        self.transport.write(resp)
        self.transport.loseConnection()

    def noResponse(self, err):
        self.transport.loseConnection()


class DjangoManagerFactory(protocol.Factory):

    """docstring for DjangoManagerFactory"""

    def __init__(self, settings_path, command):
        """ Gets path to manager from Django project settings
        Args:
            settings_path(str): Python path to Django project settings
            command(str): command to send to the Django manager
        """
        settings = importlib.import_module(settings_path)
        self.command = command
        self.manager_path = os.path.join(settings.BASE_DIR, "../manage.py")

    def buildProtocol(self, addr):
        return Call("python", self.manager_path, self.command)


if __name__ == '__main__':
    reactor.listenTCP(
        10999, DjangoManagerFactory("settings.common", "collectstatic"))
    reactor.run()
