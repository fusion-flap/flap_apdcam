#ifndef __APDCAM10G_DAQ_SETTINGS_H__
#define __APDCAM10G_DAQ_SETTINGS_H__



/*

  class daq_settings

  This class defines all settings which influence the data transfer between the camera and the PC, 
  providing read/write functions to load/save the settings from/to a file
  This way both the real data recording code and the fake camera can use the same settings.

 */

#include "channel_info.h"
#include <vector>
#include <string>
#include <iostream>

namespace apdcam10g
{
    class daq_settings
    {
    protected:
        std::string interface_ = "lo";
        const static int ipv4_header_ = 20;
        const static int udp_header_ = 8;
        unsigned int mtu_ = 0;
        unsigned int octet_ = 0;

        // The maximum UDP packet size, which is 22 bytes (streamheader) + 8*octet. At the end of a burst or a sequence
        // of transmitted shots, there may be a smaller UDP packet if the shots do not fill an entire one, but
        // all preceding packets will have this maximum size
        unsigned int max_udp_packet_size_ = 0;

        // A lot of (redundant) information to be able to access and manipulate the memory storage
        // in different ways efficiently
        std::vector<std::vector<std::vector<bool>>> channel_masks_;           // Indices: ADC number, chip number, channel number
        std::vector<unsigned int>                   resolution_bits_;         // Index: ADC number
        std::vector<unsigned int>                   board_bytes_per_shot_;    // index is ADC number
        std::vector<std::vector<unsigned int>>      chip_bytes_per_shot_;     // indices are ADC number (0..3max) and chip nummber (0..3)
        std::vector<std::vector<unsigned int>>      chip_offset_;             // Offset of the first data byte of the chip w.r.t. the board's first data byte, indices are ADC number and chip number
        std::vector<std::vector<channel_info>>      channelinfo_;             // Indices: ADC number, and a counter over the enabled channels (of all chips)
                                                                              // Example: channelinfo_[0][3] describes the 3rd ENABLED channel (and not the 3rd channel) of the 0th ADC board
        const int ports_[4] = {10000, 10001, 10002, 10003};

    public:
        // set/get the MTU value (Maximum Transmission Unit, the biggest size of packet that can be sent
        // without fragmentation) used for all sockets
        daq_settings &mtu(unsigned int m);
        unsigned int mtu() const { return mtu_; }

        daq_settings &interface(const std::string &i) { interface_ = i; return *this; }
        const std::string &interface() const { return interface_; }
        daq_settings &get_net_parameters();

        bool channel_mask(int i_adc, int i_chip, int i_channel) { return channel_masks_[i_adc][i_chip][i_channel]; }
        unsigned int resolution_bits(int i_adc) { return resolution_bits_[i_adc]; }
        unsigned int board_bytes_per_shot(int i_adc) { return board_bytes_per_shot_[i_adc]; }
        unsigned int chip_bytes_per_shot(int i_adc, int i_chip) { return chip_bytes_per_shot_[i_adc][i_chip]; }
        unsigned int chip_offset(int i_adc, int i_chip) { return chip_offset_[i_adc][i_chip]; }
        const std::vector<channel_info> &channelinfo(unsigned int adc) { return channelinfo_[adc]; }

        // Returns the maximum size of the packets: the CC header + the ADC data 
        // (but not including the UDP header, IPv4 header and Ethernet header)
        // If fewer samples are available at the end of a burst or data recording sequence,
        // the packet will be shorter.
        unsigned int max_udp_packet_size() const { return max_udp_packet_size_; }
        

        // Read/write the configuration into a .json file
        void write(const std::string &filename);
        bool read(const std::string &filename);

        // Calculate the byte/bit offsets of the channels within the ADC bytes of a given sample,
        // and the masks/shifts to extract the values
        // calculates the bytes_per_sample_[...] values as well for each ADC
        // The resolution_bits_[i_adc] array and channel_masks_ must be set before calling this function !!!
        void calculate_channel_info();

        void print_channel_map(std::ostream &out = std::cout);
    };

}


#endif


