import Ice # pylint: disable=import-error,wrong-import-position
from os import path

SLICE_PATH = path.join(path.dirname(__file__), "iceflix.ice")
Ice.loadSlice(SLICE_PATH)
import IceFlix # pylint: disable=import-error,wrong-import-position

class StreamAnnouncementsListener(IceFlix.StreamAnnouncements):
    
    def __init__(self, own_servant, own_service_id):
        self.servant = own_servant
        self.service_id = own_service_id
        
        self.known_ids = set()
        
    def newMedia(self, media_id, initial_name, srv_id, current=None):
        if srv_id not in self.servant.subscriber.known_ids:
            return
        # TODO: Comprobar que si media_id no esta en el catalogo, lo añada
        pass
    
    def removedMedia(self, media_id, srv_id, current=None):
        if srv_id not in self.servant.subscriber.known_ids:
            return
         # TODO: Comprobar que si media_id no esta en el catalogo, lo quite 

class StreamAnnouncementsSender():
    
    def __init__(self, topic, service_id, servant_proxy):
        self.publisher = IceFlix.StreamAnnouncementsPrx.uncheckedCast(
            topic.getPublisher()
        )
        self.service_id = service_id
        self.proxy = servant_proxy
        
    def newMedia(self, media_id, name):
        self.publisher.newMedia(media_id, name, self.service_id)
    
    def removedMedia(self, media_id):
        self.publisher.removedMedia(media_id, self.service_id)

    