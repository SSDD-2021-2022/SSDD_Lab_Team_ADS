#!/usr/bin/python3
# pylint: disable=invalid-name
"""Modulo Servicio de Autenticación"""

from time import sleep
from os import path
import sys
import json
import secrets
import Ice

SLICE_PATH = path.join(path.dirname(__file__), "iceflix.ice")
USERS_PATH = path.join(path.dirname(__file__), "users.json")

try:
    import IceFlix
except ImportError:
    Ice.loadSlice(SLICE_PATH)
    import IceFlix

class AuthenticatorI(IceFlix.Authenticator): # pylint: disable=inherit-non-class
    """Sirviente del servicio de autenticación"""

    def refreshAuthorization(self, user: str, passwordHash: str, current=None): # pylint: disable=invalid-name,unused-argument
        ''' Actualiza el token de un usuario registrado '''

        with open(USERS_PATH, "r") as f:
            obj = json.load(f)

        for i in obj["users"]:
            if i["user"] == user and i["password"] == passwordHash:
                new_token = secrets.token_urlsafe(40)
                self._active_users_.update({user:new_token})
                return new_token

        raise IceFlix.Unauthorized

    def isAuthorized(self, userToken, current=None): # pylint: disable=invalid-name,unused-argument
        ''' Permite conocer si un token está actualizado en el sistema '''

        authorized = bool(userToken in self._active_users_.values())
        if authorized:
            return authorized
        else:
            raise IceFlix.Unauthorized

    def whois(self, userToken, current=None): # pylint: disable=invalid-name,unused-argument
        ''' Permite conocer el usuario asociado a un token'''

        if userToken in self._active_users_.values():
            info = self._active_users_.items()
            for user in info:
                if user[1] == userToken:
                    return user[0]
        else:
            raise IceFlix.Unauthorized

    def addUser(self, user, passwordHash, adminToken, current=None): # pylint: disable=invalid-name,unused-argument
        ''' Perimte al administrador añadir usuarios al sistema '''

        try:
            self.check_admin(adminToken)
        except (IceFlix.TemporaryUnavailable, IceFlix.Unauthorized) as e:
            raise IceFlix.Unauthorized

        with open(USERS_PATH, "r") as f:
            obj = json.load(f)

        obj["users"].append({"user": user, "password": passwordHash, "tags": {}})

        with open(USERS_PATH, 'w') as file:
            json.dump(obj, file, indent=2)

    def removeUser(self, user, adminToken, current=None): # pylint: disable=invalid-name,unused-argument
        ''' Permite al administrador elminar usuarios del sistema '''

        try:
            self.check_admin(adminToken)
        except (IceFlix.TemporaryUnavailable, IceFlix.Unauthorized) as e:
            raise IceFlix.Unauthorized

        with open(USERS_PATH, "r") as reading_descriptor:
            obj = json.load(reading_descriptor)

        for i in obj["users"]:
            if i["user"] == user:
                obj["users"].remove(i)
                break

        with open(USERS_PATH, 'w') as file:
            json.dump(obj, file, indent=2)

        if user in self._active_users_.keys():
            self._active_users_.pop(user)

    def check_admin(self, admin_token: str):
        ''' Comprueba si un token es Administrador '''

        try:
            is_admin = self._main_prx_.isAdmin(admin_token)
            if not is_admin:
                raise IceFlix.Unauthorized
        except IceFlix.TemporaryUnavailable:
            print("Se ha perdido conexión con el servidor Main")
            raise IceFlix.Unauthorized
        else:
            return is_admin

    def __init__(self):
        self._active_users_ = dict()


class AuthenticatorServer(Ice.Application):
    """Servidor del servicio principal"""
    def run(self, argv):
        sleep(1)
        main_service_proxy = self.communicator().stringToProxy(argv[1])
        main_connection = IceFlix.MainPrx.checkedCast(main_service_proxy)

        broker = self.communicator()
        servant = AuthenticatorI()

        adapter = broker.createObjectAdapterWithEndpoints('AuthenticatorAdapter', 'tcp -p 9091')
        authenticator_proxy = adapter.add(servant, broker.stringToIdentity('Authenticator'))

        adapter.activate()
        main_connection.register(authenticator_proxy)
        servant._main_prx_ = main_connection

        self.shutdownOnInterrupt()
        broker.waitForShutdown()

if __name__ == '__main__':
    sys.exit(AuthenticatorServer().main(sys.argv))
