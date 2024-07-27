#ifndef __APDCAM10G_CHANNEL_DATA_EXTRACTOR_H__
#define __APDCAM10G_CHANNEL_DATA_EXTRACTOR_H__

/*

  A worker class derived from data_consumer, which consumes APDCAM data (UDP packets) from the ring buffer,
  and extracts the channel-by-channel data into linear buffers (per channel). Once these buffers are full,
  they are dumped to disk. The linear buffers are protected from swapping by mlock.

  One instance of this class handles one data stream at one port, i.e. one ADC
  
 */

#include "daq.h"

namespace apdcam10g
{
    template <safeness S = default_safeness>
    class channel_data_extractor 
    {
    private:
        
        // A pointer to a daq object to query packet size, number of bytes per ADC chip, per ADC board, etc
        daq *daq_ = 0;

        // The ADC number, the data of which this consumer will be processing
        unsigned int adc_ = 0;
        
        packet *packet_ = 0, *next_packet_ = 0;

        data_type *channel_data_[32] = {0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0}; // 32 buffers for the 32 channels
        unsigned int channel_data_capacity_ = 0;  // Capacity of the buffers (each channel) to store the channel samples
        unsigned int channel_data_size_[32];      // Actual size of (number of samples stored in) the buffer per channel

        std::ofstream *output_file_[32];

        // The offset within the packet in the ring buffer, where the next sample
        // will start. 
        unsigned int sample_offset_within_adc_data_ = 0;

        // Append the value to the array of values of the given channel in the buffer, and if the buffer is full,
        // automatically write it to the corresponding file, and empty the buffer
        inline void store_channel_data_(unsigned int channel_number, data_type value)
            {
                channel_data_[channel_number][channel_data_size_[channel_number]++] = value;
                if(channel_data_size_[channel_number] == channel_data_capacity_) flush(channel_number);
            }
        
        // Get the channel value from the byte array pointed to by 'ptr', which is the first byte
        // of the encoded channel value. 
        inline data_type get_channel_value_(std::byte *ptr, channel_info &c)
            {
                switch(c.nbytes)
                {
                    // For 1 and 2 bytes we fit into data_type. However, if the value reaches over 3 bytes, we need to use a larger integer to represent it
                    // before shifting down to the least significant bit.
                case 2: return ((data_type(ptr[0])<<8 | data_type(ptr[1])) >> c.shift) & make_mask<data_type>(0,daq_->resolution_bits(adc_));
                case 3: return data_type( (data_envelope_type(ptr[0])<<16 | data_envelope_type(ptr[1])<<8 | data_envelope_type(ptr[2])) >> c.shift) & make_mask<data_type>(0,daq_->resolution_bits(adc_));
                case 1: return (data_type(ptr[0])>>c.shift) & make_mask<data_type>(0,daq_->resolution_bits(adc_));
                default: APDCAM_ERROR("Bug! Number of bytes should be 1, 2 or 3");
                }
                return 0;
            }
        
    public:
        // Constructor
        // adc -- ADC number (0..3)
        // ver -- version (from version.h)
        // sample_buffer_size -- buffer capacity for the channel samples, before writing to file
        channel_data_extractor(unsigned int adc, version ver, unsigned int sample_buffer_size);

        ~channel_data_extractor();

        void stream(daq *s) { daq_ = s; }
      
        // Flush the buffers of all channels
        void flush();

        // Flush the buffer of one channel
        void flush(unsigned int channel_number);

        unsigned int run(ring_buffer<std::byte> &buffer);
    };
}


#endif

