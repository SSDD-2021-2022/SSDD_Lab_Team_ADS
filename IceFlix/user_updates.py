""" Modulo para manejar la comunicación entre instancias Authenticator """

from os import path
import uuid
import os
import Ice

try:
    import IceFlix
except ImportError:
    Ice.loadSlice(os.path.join(os.path.dirname(__file__), "iceflix.ice"))
    import IceFlix

AUTH_ID = str(uuid.uuid4())

LOCAL_DB_PATH = path.join(path.join(path.dirname(__file__), "persistence"),
                                                    (AUTH_ID + "_users.json"))

class UserUpdatesListener(IceFlix.UserUpdates):
    """ Listener del topic User updates """

    def __init__(self, own_servant, own_service_id, own_type):
        """ Inicialización del listener """

        self.servant = own_servant
        self.service_id = own_service_id
        self.own_type = own_type

        self.authenticators = {}
        self.catalogs = {}
        self.mains = {}
        self.known_ids = set()

    def newUser(self, user, passwordHash, srvId, current=None): # pylint: disable=invalid-name,unused-argument
        """ Comportamiento al recibir un mensaje newUser """

        if srvId is not self.service_id:
            user = (user, passwordHash)
            self.servant.add_local_user(user)

    def newToken(self, user, userToken, srvId, current=None): # pylint: disable=invalid-name,unused-argument
        """ Comportamiento al recibir un mensaje newToken """

        if srvId is not self.service_id:
            self.servant.add_token(user, userToken)

class UserUpdatesSender:
    """ Sender del topic User updates """

    def __init__(self, topic, service_id, servant_proxy):
        """ Inicialización del sender """

        self.publisher = IceFlix.UserUpdatesPrx.uncheckedCast(
            topic.getPublisher()
        )
        self.service_id = service_id
        self.proxy = servant_proxy

    def newUser(self, user, passwordHash): # pylint: disable=invalid-name,unused-argument
        """ Emitir evento newUser """

        print(f"[UserUpdates] (Emite New User) ID: {self.service_id}," +
              f"Usuario: {user}, PasswordHash: {passwordHash}")
        self.publisher.newUser(user, passwordHash, self.service_id)

    def newToken(self, user, userToken): # pylint: disable=invalid-name,unused-argument
        """ Emitir evento newToken """

        print(f"[UserUpdates] (Emite New Token) ID: {self.service_id}," +
              f"Usuario: {user}, Token: {userToken}")
        self.publisher.newToken(user, userToken, self.service_id)
