'''
This is the python interface for the C++ class "data_stream", which is a wrapper class
around the fast data communication sockets between the PC and the camera.

'''


import ctypes
import platform

lib = ctypes.CDLL("./libapdcam10g.so",winmode=0)

class daq(object):

    # Constructor
    def __init__(self):
        lib.create.argtypes = []
        lib.create.restype = ctypes.c_void_p

        lib.destroy.argtypes = [ctypes.c_void_p]
        lib.destroy.restype = None

        lib.mtu.argtypes = [ctypes.c_void_p,ctypes.c_int]
        lib.mtu.restype = None

        lib.start.argtypes = [ctypes.c_void_p,ctypes.c_bool]
        lib.start.restype = None

        lib.stop.argtypes = [ctypes.c_void_p,ctypes.c_bool]
        lib.stop.restype = None
        
        lib.initialize.argtypes = 
        lib.initialize.restype = None

        lib.dump.argtypes = [ctypes.c_void_p]
        lib.dump.restype = ctypes.c_void_p

        self.obj_ = lib.create()

    # Destructor
    def __del__(self):
        lib.destroy(self.obj_)

    def initialize(self,dual_sata, channel_masks, resolution_bits, version, safe):
        if len(channel_masks) != len(resolution_bits):
            raise Exception("Length of channel_masks and resolution_bits differs","In function 'initialize'") 

        n_adc_boards = len(channel_masks)
        multi_array_type = ( (ctypes.c_bool * 8) * 4 ) * n_adc_boards
        uint_array_type = ctypes.c_uint * n_adc_boards

        channel_masks_2 = multi_array_type()
        resolution_bits_2 = uint_array_type()

        for i_adc_board in range(n_adc_boards):
            resolution_bits_2[i_adc_board] = resolution_bits[i_adc_board]
            for i_chip in range(4):
                for i_channel in range(8):
                    channel_masks_2[i_adc_board][i_chip][i_channel] = channel_masks[i_adc_board][i_chip][i_channel]

        lib.initialize(self.obj_, dual_sata, channel_masks_2, resolution_bits_2, version, safe)

    def mtu(self,m):
        '''
        Set the MTU value of the network communication, and calculate (and store) the octet value
        of the communication
        '''
        lib.mtu(self.obj_,m)

    def start(self,wait):
        lib.start(self.obj_,wait)

    def stop(self,wait):
        lib.start(self.obj_,wait);

    def dump(self):
        '''
        Dump the DAQ settings to stdout
        '''
        lib.dump(self.obj_)


