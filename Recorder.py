import pyaudio
import wave

class Recorder:
    p = None
    stream = None
    frames = None
    chunk = None
    sample_format = None
    channels = None
    fs = None
    seconds = None
    filename_MD = None
    filename_MJ = None
    device_id_1 = None
    device_id_2 = None

    def __init__(self, chunk=None, sample_format=None, channels=None,
                 fs=None, seconds=None, filename_MD=None, filename_MJ=None):

        if (chunk == None):
            self.chunk = 1024  # Record in default chunks of 1024 samples
        else:
            self.chunk = chunk

        if (sample_format == None):
            self.sample_format = pyaudio.paInt16  # 16 bits per sampel
        else:
            self.sample_format = sample_format

        if (channels == None):
            self.channels = 1
        else:
            self.channels = channels

        if (fs == None):
            self.fs = 44100  # Rekam 44100 sampel per detik
        else:
            self.fs = fs

        if (seconds == None):
            self.seconds = 5
        else:
            self.seconds = seconds

        if (filename_MD == None):
            self.filename_MD = "output_MD.wav"
        else:
            self.filename_MD = filename_MD

        if (filename_MJ == None):
            self.filename_MJ = "output_MJ.wav"
        else:
            self.filename_MJ = filename_MJ

        self.p = pyaudio.PyAudio()  # Create an interface to PortAudio

    def __del__(self):
        self.p.terminate()

    def setDeviceID_1(self, device_id=None):
        if (device_id == None):
            self.device_id_1 = 0
        else:
            self.device_id_1 = device_id

        print(self.p.get_device_info_by_index(self.device_id_1))

    def setDeviceID_2(self, device_id=None):
        if (device_id == None):
            self.device_id_2 = 0
        else:
            self.device_id_2 = device_id

        print(self.p.get_device_info_by_index(self.device_id_2))


    def setfilename_MD(self, filename=None):
        if (filename == None):
            self.filename_MD = "output_MD.wav"
        else:
            self.filename_MD = filename

    def setfilename_MJ(self, filename=None):
        if (filename == None):
            self.filename_MJ = "output_MJ.wav"
        else:
            self.filename_MJ = filename

    def getfilename_MD(self):
        return self.filename_MD
    
    def getfilename_MJ(self):
        return self.filename_MJ

    def record(self):
        print("Recording...")
        # Initialize arrays to store the recorded data
        self.frames1 = []
        self.frames2 = []

        # Open a connection to microphone 1
        stream1 = self.p.open(format=self.sample_format,
                    channels=self.channels,
                    rate=self.fs,
                    frames_per_buffer=self.chunk,
                    input_device_index=self.device_id_1,  # Use the selected microphone
                    input=True)

        # Open a connection to microphone 2
        stream2 = self.p.open(format=self.sample_format,
                    channels=self.channels,
                    rate=self.fs,
                    frames_per_buffer=self.chunk,
                    input_device_index=self.device_id_2,  # Use the selected microphone
                    input=True)

        # rekam 2 device sekaligus and 
        for i in range(0, int(self.fs / self.chunk * self.seconds)):
            data1 = stream1.read(self.chunk)
            self.frames1.append(data1)

            data2 = stream2.read(self.chunk)
            self.frames2.append(data2)

        # Stop and close the connection to the microphone
        stream1.stop_stream()
        stream1.close()
        stream2.stop_stream()
        stream2.close()

        print("Finished recording")

    def save(self):
        print("Saving...")
        # Save the recorded data as a WAV file
        wf1 = wave.open(self.filename_MD, "wb")
        wf1.setnchannels(self.channels)
        wf1.setsampwidth(self.p.get_sample_size(self.sample_format))
        wf1.setframerate(self.fs)
        wf1.writeframes(b"".join(self.frames1))
        wf1.close()

        wf2 = wave.open(self.filename_MJ, "wb")
        wf2.setnchannels(self.channels)
        wf2.setsampwidth(self.p.get_sample_size(self.sample_format))
        wf2.setframerate(self.fs)
        wf2.writeframes(b"".join(self.frames2))
        wf2.close()

        print("Finished saving")