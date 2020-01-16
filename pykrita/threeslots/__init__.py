from .threeslots import ThreeSlotsExtension
import krita

plugin = ThreeSlotsExtension(Application)

Scripter.addExtension(plugin)

class noti(krita.Notifier):

    def __init__(self, parent):
        super(noti, self).__init__(parent)

        self.viewClosed.connect(self.close)

    def close(self):
        #print("closing")
        plugin.writeSettings()

noti(Application)

