import pyaudio
import wave
import librosa
import librosa.display
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import QMainWindow, QGraphicsScene
from ui_mainwindow import Ui_MainWindow
from Recorder import Recorder

class MainWindow(QMainWindow):
    ui = None
    rrecorder = None
    devices = None

    def __init__(self, parent=None):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.recorder = Recorder()

        # === Background Tab ===
        # add device list to combobox
        self.devices = self.get_device_list()
        for device in self.devices:
            self.ui.pilihMD.addItem(device['name'])
            self.ui.pilihMJ.addItem(device['name'])

        # set default device index
        self.set_device_id()

        # get combobox index and save to variable
        self.ui.pilihMD.currentIndexChanged.connect(self.set_device_id)
        self.ui.pilihMJ.currentIndexChanged.connect(self.set_device_id)

        # Record button clicked and callback function with parameter
        self.ui.pbBG.clicked.connect(lambda: self.process("background"))

        # Noise Reduction button clicked and callback function with parameter
        self.ui.noiseBG.clicked.connect(lambda: self.noise_reduction("background"))

        # === Kayu Tab ===
        # add device list to combobox
        self.devices = self.get_device_list()
        for device in self.devices:
            self.ui.pilihMDK.addItem(device['name'])
            self.ui.pilihMJK.addItem(device['name'])

        # set default device index
        self.set_device_id()

        # get combobox index and save to variable
        self.ui.pilihMDK.currentIndexChanged.connect(self.set_device_id)
        self.ui.pilihMJK.currentIndexChanged.connect(self.set_device_id)

        # Record button clicked and callback function with parameter
        self.ui.pbKayu.clicked.connect(lambda: self.process("kayu"))

        # Noise Reduction button clicked and callback function with parameter
        self.ui.noiseKayu.clicked.connect(lambda: self.noise_reduction("kayu"))

    def process(self, type=None):
        # record audio and save to file
        self.recorder.record()

        if type == None:
            self.recorder.setFilename_1("output_1.wav")
            self.recorder.setFilename_2("output_2.wav")
        
        elif type == "background":
            self.recorder.setFilename_1("background_1.wav")
            self.recorder.setFilename_2("background_2.wav")
        
        elif type == "kayu":
            wood_name = self.ui.namaKayu.text()
            if wood_name == "" or wood_name == None:
                wood_name = "kayu"

            filename1 = wood_name + "_1.wav"
            filename2 = wood_name + "_2.wav"
            self.recorder.setFilename_1(filename1)
            self.recorder.setFilename_2(filename2)

        self.recorder.save()

        # show audio waveform
        if type == "background":
            self.plotBG(index=1)
            self.plotBG(index=2)
        elif type == "kayu":
            self.plotKayu(index=1)
            self.plotKayu(index=2)

    def noise_reduction(self, type=None):
        print("Noise Reduction")
        

    def plotBG(self, index=None):
        print("Plot Background")

        if index == 1:
            audio = self.recorder.getFilename_1()
        elif index == 2:
            audio = self.recorder.getFilename_2()

        scene = self.plot(audio_name=audio)

        if index == 1:
            self.ui.mdBG.setScene(scene)
        elif index == 2:
            self.ui.mjBG.setScene(scene)

    def plotKayu(self, index=None):
        print("Plot Kayu" + str(index))
        if index == 1:
            audio = self.recorder.getFilename_1()
        elif index == 2:
            audio = self.recorder.getFilename_2()

        scene = self.plot(audio_name=audio)

        if index == 1:
            self.ui.mdKayu.setScene(scene)
        elif index == 2:
            self.ui.mjKayu.setScene(scene)

    def plot(self, audio_name=None):
        if audio_name == None:
            return

        # Plot the audio signal in time
        x, sr = librosa.load(audio_name)

        # size in px
        figure = plt.figure(figsize=(12, 5), dpi=50)
        axes = figure.gca()
        axes.set_title('Audio Signal in Time Domain', size=12)
        librosa.display.waveshow(x, sr)
        axes.set_xlabel('Time (s)', size=12)
        axes.set_ylabel('Amplitude (dB)', size=12)

        # put figure to scene
        scene = QGraphicsScene()
        scene.addWidget(FigureCanvas(figure))

        return scene

    def get_device_list(self):
        # Dapatkan jumlah perangkat audio yang tersedia
        num_devices = self.recorder.p.get_device_count()

        # create list of devices dictionary
        devices = []

        # Tampilkan daftar mikrofon yang tersedia
        # add index and name to dictionary
        # print("Daftar mikrofon yang tersedia:"
        for i in range(num_devices):
            info = self.recorder.p.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                print("Input Device id ", i, " - ", info['name'])
                devices.append({'device_id': i, 'name': info['name']})

        return devices

    def set_device_id(self):
        # get combobox index and save to variable
        print("Device changed")

        index_D = self.devices[self.ui.pilihMD.currentIndex()]['device_id']
        index_J = self.devices[self.ui.pilihMJ.currentIndex()]['device_id']
        print(f"Device D: {index_D}")
        print(f"Device J: {index_J}")

        self.recorder.setDeviceID_1(device_id=index_D)
        self.recorder.setDeviceID_2(device_id=index_J)
