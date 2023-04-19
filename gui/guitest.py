import sys
from PyQt5.QtCore import QObject, QUrl, Qt
from PyQt5.QtWidgets import QApplication
from PyQt5.QtQml import QQmlApplicationEngine
from PyQt5.QtCore import  pyqtSignal, pyqtSlot

class APDCAM_Gui(QObject):
    def __init__(self):
        super(APDCAM_Gui,self).__init__()
        self.app = QApplication(sys.argv)
        self.engine = QQmlApplicationEngine()
        self.ctx = self.engine.rootContext()
        self.ctx.setContextProperty("main", self.engine)
        self.ctx.setContextProperty("APDCAM",self)
        self.engine.load('Main.qml')
        self.win = self.engine.rootObjects()[0]
        self.win.show()
        self.camera_preview = self.win.findChild(QObject,"camera_preview");

    def run(self):
        self.status = self.app.exec_()
        return self.status


    def set_window_title(self,t):
        self.win.setProperty("title",t);

    @pyqtSlot(str)
    def show_message(self,msg):
        self.win.findChild(QObject,"message").setProperty("text",msg);
        self.set_window_title("Fusion Instrumemts: " + msg);
        self.camera_preview.add_pixel(1,10,10);
        self.camera_preview.add_pixel(2,30,30);
        self.camera_preview.set_pixel(1,0,1,1);
        self.camera_preview.set_pixel(3,0.4,1,1);
#        self.win.deletePixel("ketto");

    @pyqtSlot(str)
    def say_hello(self, msg):
        print("apdcam_gui.say_hello: " + msg)


        
apdcam_gui = APDCAM_Gui()
sys.exit(apdcam_gui.run())
