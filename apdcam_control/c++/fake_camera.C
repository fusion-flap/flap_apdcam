#include "fake_camera.h"
#include "udp.h"
#include "packet.h"
#include <thread>

using namespace std;

namespace apdcam10g
{
    void fake_camera::send(int nshots, bool wait)
    {
        const int n_adc = board_bytes_per_shot_.size();

        // Allocate buffers and set proper size
        vector<vector<std::byte>> buffer(channelinfo_.size());

        vector<vector<int>> shot_numbers(channelinfo_.size());

        for(unsigned int i_adc=0; i_adc<n_adc; ++i_adc)
        {
            // Allocate sufficient memory to store exactly the nshots shots + the extra room for a cc_streamheader (22 bytes)
            // at the front
            {
                const int buffersize = nshots*board_bytes_per_shot_[i_adc]+packet::cc_streamheader;
                buffer[i_adc].resize(buffersize,std::byte(0));
            }

            // Byte counter within a packet, to keep track when we reach the boundary of a
            // UDP packet. 
            int packet_byte_index = 0;

            for(unsigned int i_shot=0; i_shot<nshots; ++i_shot)
            {
                // The starting index of the data of the given shot, within the ADC's buffer. We have a global offset of
                // packet::cc_streamheader so that we have sufficient room before the first data to write the packet header.
                // For the non-first packet, the previos packet's data region will be overwritten
                const unsigned int shot_start = packet::cc_streamheader + i_shot*board_bytes_per_shot_[i_adc];
                for(unsigned int i_chip=0; i_chip<4; ++i_chip)
                {
                    const unsigned int chip_start = chip_offset_[i_adc][i_chip];
                    unsigned int target_byte = 0; // relative to chip start
                    int target_bit = 7; // signed so that we can check when it is -1. We start from the MSB
                    for(unsigned int i_channel=0; i_channel<8; ++i_channel)
                    {
                        if(!channel_masks_[i_adc][i_chip][i_channel]) continue;

                        // We set the value of the shot number into each channel
                        const int channel_value = i_shot;
                        
                        // We copy the value bit-by-bit to the buffer, to have a different algo than the
                        // value extraction, so that we decrease the risk of having a bug undiscovered due to the
                        // same algo generating and reading the data
                        
                        // Loop over the bits of the value, starting from MSB
                        for(int bit=resolution_bits_[i_adc]-1; bit>=0; --bit)
                        {
                            if(target_byte >= chip_bytes_per_shot_[i_adc][i_chip]) APDCAM_ERROR("This is a bug! We write outside of the chip's memory space");

                            // Shift and mask this bit from the value, and write it to the subsequent bit of the buffer's byte
                            buffer[i_adc][shot_start+chip_start+target_byte] |= std::byte(((channel_value>>bit)&1)<<target_bit);
                            
                            // When writing the first bit of the first byte of a packet (8*octet_ bytes), register the first shot numbers
                            if(packet_byte_index==0 && target_bit==7) shot_numbers[i_adc].push_back(i_shot);
                            
                            // Increment the bit/byte indices
                            if(--target_bit<0)
                            {
                                target_bit=7;
                                ++target_byte;
                                if(++packet_byte_index > octet_*8) packet_byte_index = 0;
                            }
                        }
                    }
                }
            }
        }

        vector<jthread> threads;
        for(unsigned int i_adc=0; i_adc<n_adc; ++i_adc)
        {
            threads.push_back(std::jthread( [this,nshots,i_adc,&shot_numbers,&buffer](std::stop_token stok)
                {
                    udp_client client(ports_[i_adc],server_ip_);
                    packet_v2 p;

                    try
                    {
                        for(unsigned int i_packet=0; !stok.stop_requested() && packet::cc_streamheader+i_packet*8*octet_<buffer[i_adc].size(); ++i_packet)
                        {
                            // The real data bytes start at cc_streamheader (=22) offset. We set the UDP packet data pointer
                            // to 22 bytes before. At the head of each buffer, there was this extra 22 bytes reserved,
                            // serving as the space for the header of the first packet. For subsequent packets, the packet start
                            // pointer (i.e. including the 22 header bytes) will be moved forward, occupying the last 22 bytes
                            // of the previous (already sent) packet memory region. This is for simplicity and efficiency. We overwrite
                            // these 22 last bytes of each previous packet buffer, so the data is invalidated
                            p.data(&(buffer[i_adc].front())+i_packet*8*octet_,8*octet_+packet::cc_streamheader);
                            p.clear_header();
                            p.serial_number = i_packet;  // what is a serial number?
                            p.packet_counter = i_packet;
                            p.sample_counter = shot_numbers[i_adc][i_packet];
                            p.udp_test_mode = 0;
                            p.stream_number = i_adc;
                            p.burst_counter = 0;
                            p.data_bytes = 8*octet_; // must be updated, for last packet it is less than this...
                            p.trigger_location = 0;
                            p.trigger_status = 0;
                            p.adc_stream_mode = 1;
                            p.sample_start_condition = 0;
                            p.dual_sata_mode = 0;
                            p.burst_start = 0;

                            if(client.send(p.start(),p.udp_packet_size())<0) APDCAM_ERROR("Sending of data failed");
                        }
                    }
                    catch(const apdcam10g::error &e)
                    {
                        cerr<<e.full_message()<<endl;
                    }
                }));
        }


        if(wait)
        {
            cerr<<"Waiting for the threads to finish"<<endl;
            for(unsigned int i_adc=0; i_adc<n_adc; ++i_adc) if(threads[i_adc].joinable()) threads[i_adc].join();
        }
    }
}
