#include <fstream>
#include <iostream>
#include "channel_data_extractor.h"
#include "daq.h"

using namespace std;

namespace apdcam10g
{

    template <safeness S>
      channel_data_extractor<S>::channel_data_extractor(unsigned int adc, version ver, unsigned int sample_buffer_capacity) : adc_(adc) // : data_consumer(adc,ver)
    {
        // Create a version-specific packet handler
        packet_ = packet::create(ver);
        next_packet_ = packet::create(ver);

        channel_data_capacity_ = sample_buffer_capacity;
        for(unsigned int i=0; i<32; ++i)
        {
            channel_data_[i] = new data_type[channel_data_capacity_];
            if(::mlock(channel_data_[i],sample_buffer_capacity) != 0) APDCAM_ERROR_ERRNO(errno);
            channel_data_size_[i] = 0;
            output_file_[i] = new std::ofstream("ADC-" + std::to_string(adc_) + "_channel-" + std::to_string(i) + ".dat");
        }
    }

  template <safeness S>
    channel_data_extractor<S>::~channel_data_extractor()
    {
      delete packet_;
      delete next_packet_;
    }

    template <safeness S>
    void channel_data_extractor<S>::flush()
    {
        cerr<<"  flushing channel signal extractor"<<endl;
        for(unsigned int channel_number=0; channel_number<32; ++channel_number) flush(channel_number);
    }

    template <safeness S>
    void channel_data_extractor<S>::flush(unsigned int channel_number)
    {
        if(channel_data_size_[channel_number] > 0)
        {
            for(unsigned int s=0; s<channel_data_size_[channel_number]; ++s) (*(output_file_[channel_number]))<<channel_data_[channel_number][s]<<std::endl;
            output_file_[channel_number]->flush();
            channel_data_size_[channel_number] = 0;
        }
    }

    template <safeness S>
    channel_data_extractor<S>::~channel_data_extractor()
    { 
        flush();

        // Loop over all 32 channels
        for(unsigned int channel_number=0; channel_number<32; ++channel_number)
        {
            ::munlock(channel_data_[channel_number],channel_data_capacity_);
            delete [] channel_data_[channel_number];
            delete output_file_[channel_number];
        }
    }

    template <safeness S>
    unsigned int channel_data_extractor<S>::run(ring_buffer<std::byte> &buffer)
    {
        // We will use the maximum udp packet size, since the ring buffer is allocated to contain set of full max-sized udp packets
        const unsigned int udp_packet_size = daq_->max_udp_packet_size();

        const unsigned int board_bytes_per_shot = daq_->board_bytes_per_shot(adc_);

        // Get the available number of bytes in the buffer
        const int size = buffer.size();

        // The number of available packets
        if(S==safe && size%udp_packet_size!=0) APDCAM_ERROR("Data available in the ring buffer is not an integer multiple of the packet size");
        const int npackets = size/udp_packet_size; // integer division

        if(udp_packet_size*npackets != size) APDCAM_ERROR("Not a full package received...");
        
        unsigned int removed_packets = 0;

        for(int ipacket=0; ipacket<npackets; )
        {
            auto [ptr1,size1,ptr2,size2] = buffer.read_region(udp_packet_size);
            if(size1!=udp_packet_size) APDCAM_ERROR("Oops");
            packet_->data(ptr1,size1);

            const auto &chinfo = daq_->channelinfo(adc_);

            // Loop over the samples stored in this packet
            while(true)
            {
                // if the entire sample fits into this packet
                if(packet_->adc_data_start()+sample_offset_within_adc_data_+board_bytes_per_shot <= packet_->end())
                {
                    for(auto c : chinfo) store_channel_data_(c.channel_number, get_channel_value_(packet_->adc_data_start()+sample_offset_within_adc_data_+c.byte_offset,c));

                    // Advance the offset within the packet by the length of one sample
                    sample_offset_within_adc_data_ += board_bytes_per_shot;
                    
                    // if by this we finished processing the given UDP packet, then reset the offset to zero, and
                    // remove this UDP packet from the buffer
                    // (the > should never happen in this condition, only =, but let's be sure)
                    if(packet_->adc_data_start()+sample_offset_within_adc_data_ >= packet_->end())
                    {
                        // Remove the packet from the ring buffer
                        buffer.increment_read_ptr(udp_packet_size);
                        ++ipacket;
                        ++removed_packets;
                        // Set the pointer-within-packet to zero
                        sample_offset_within_adc_data_ = 0;
                        break;
                    }

                    // If we have not reached the end of the packet (and have quite the loop-over-samples loop), 
                    // then go to the next sample
                    continue;
                }

                // If we are here, then the current, entire sample did not fit into this packet, but extends into the next one
                // Check if there is a next packet.
                if(ipacket+1<npackets)
                {
                    // Initialize a next packet within the buffer, without actually incrementing the read pointer
                    // of the ring buffer
                    auto [p1,n1,p2,n2] = buffer.read_region(udp_packet_size,udp_packet_size);
                    if(n1 != udp_packet_size) APDCAM_ERROR("Opps");
                    next_packet_->data(p1,udp_packet_size);
                                     
                    for(auto c : chinfo)
                    {
                        // If all bytes of this channel still fit into this packet
                        if(packet_->adc_data_start()+sample_offset_within_adc_data_+c.byte_offset+c.nbytes <= packet_->end())
                        {
                            store_channel_data_(c.channel_number, get_channel_value_(packet_->adc_data_start()+sample_offset_within_adc_data_+c.byte_offset,c));
                        }
                        
                        // If not all bytes of this channel are within the current packet, but it starts in this packet,
                        // then it's a split value. Most complicated case
                        else if(packet_->adc_data_start()+sample_offset_within_adc_data_+c.byte_offset < packet_->end())
                        {
                            // Create a temporary buffer (we need max. 3 bytes) which will continuously store the
                            // bytes of this channel value
                            std::byte tmp[3];
                            for(unsigned int i=0; i<c.nbytes; ++i)
                            {
                                if(packet_->adc_data_start()+sample_offset_within_adc_data_+c.byte_offset+i < packet_->end()) tmp[i] = packet_->adc_data_start()[sample_offset_within_adc_data_+c.byte_offset+i];
                                else tmp[i] = next_packet_->adc_data_start()[sample_offset_within_adc_data_+c.byte_offset+i-packet_->adc_data_size()];
                                store_channel_data_(c.channel_number, get_channel_value_(tmp,c));
                            }
                        }
                        
                        // If this channel data is entirely in the next packet
                        else
                        {
                            store_channel_data_(c.channel_number, get_channel_value_(next_packet_->adc_data_start()+sample_offset_within_adc_data_+c.byte_offset-packet_->adc_data_size(), c));
                        }
                    }
                    
                    // We can safely assume that if a sample was extending into the next packet, it is entirely contained there,
                    // and does not extend into a further packet. 
                    // Remove the packet from the ring buffer
                    buffer.increment_read_ptr(udp_packet_size);
                    ++ipacket;
                    ++removed_packets;

                    // Set the pointer-within-packet to zero
                    sample_offset_within_adc_data_ = sample_offset_within_adc_data_ + board_bytes_per_shot - packet_->adc_data_size();

                    // Break looping over the samples within the current packet, go to the next one (which has already been partially processed,
                    // but this is taken care of by sample_offset_within_adc_data_ being set to some positive offset)
                    break; 
                }

                break;
            }
        }

        return removed_packets;
    }

    template class channel_data_extractor<safe>;
    template class channel_data_extractor<unsafe>;
}                           
