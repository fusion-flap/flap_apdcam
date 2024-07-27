#ifndef __APDCAM10G_PACKET_H__
#define __APDCAM10G_PACKET_H__

#include "version.h"
#include "bytes.h"
#include <string.h>

namespace apdcam10g
{
    /*
      packet - a base class to handle UDP packets, and interpret the 22-byte header at their front

      These classes implement the decoding of the information sent by the camera in the CC header of the UDP packets.
      Since the goal was to allow run-time decision between camera versions (based on version info queried from the
      camera), these functionalities are implemented as derived classes (in contrast to template-based solutions
      applied elsewhere)
     */

    class packet
    {
    protected:
        std::byte *start_ = 0;
        std::byte *end_ = 0;
        std::byte *adc_data_start_ = 0;
        unsigned int udp_packet_size_ = 0;
        unsigned int adc_data_size_ = 0;
    public:
        packet() {}

        // Specify the data buffer location/size that this class will decode/encode.
        // The pointer 'start' points to the first byte, including the CC streamheader
        // 'size' is the total UDP packet size, including the CC streamheader
        packet(std::byte *start, unsigned int size) { data(start,size); }

        const static unsigned int ipv4_header = 20;
        const static unsigned int udp_header = 8;
        const static unsigned int cc_streamheader = 22;

        void clear_header()
            {
                if(start_) memset(start_,0,cc_streamheader);
            }

        static packet *create(version ver);

        // Converter objects to extract/write data directly in the memory buffer, taking into account the
        // number of bytes representing the number, and endianness. These members can be assigned using = operator,
        // or queried (they automatically convert to the corresponding native integers)
        
        byte_converter<4,std::endian::big> serial_number;  // Serial number from the CC packet header. I assume big endian, not sure. 
        byte_converter<6,std::endian::big> packet_counter; // Packet number (counter) from the CC header. I assume big endian, not sure
        byte_converter<6,std::endian::big> sample_counter; // Sample number (counter) from the CC header. I assume big endian, not sure. Is this the first sample in the packet? First full, or even first partial?

        // Decoders for the S1 bytes
        bits<2,std::endian::big,1,1>       udp_test_mode; 
        bits<2,std::endian::big,14,2>      stream_number; // S1 byte in the header, a value in the range 0..3 inclusive

        // Decoders for the S3 bytes
        // nothing

        // The pointer 'd' points to the first byte, including the CC streamheader.
        // 'size' is the UDP packet size
        void data(std::byte *d, unsigned int size) 
        { 
            start_ = d; 
            end_ = d + size;
            adc_data_start_ = d + cc_streamheader;
            udp_packet_size_ = size;
            adc_data_size_ = size-cc_streamheader;
            serial_number.address(d);
            packet_counter.address(d+8);
            sample_counter.address(d+16);

            udp_test_mode.address(d+4);
            stream_number.address(d+4);
        }
        
        std::byte *start() const { return start_; }
        std::byte *end() const { return end_; }
        std::byte *adc_data_start() { return adc_data_start_; }
        unsigned int udp_packet_size() { return udp_packet_size_; }
        unsigned int adc_data_size() { return adc_data_size_; }
    };

    class packet_v1 : public packet
    {
    public:
        packet_v1() {}
        packet_v1(std::byte *data, unsigned int size) : packet(data,size) {}

        // Decoders for the S2 bytes
        bits<2,std::endian::big,0,8>       dslv_lock_status;
        bits<2,std::endian::big,8,8>       fpga_status;
        bits<2,std::endian::big,0,1>       sample_start_condition;  // True if the first data byte in the packet is the first byte of a sample)


        void data(std::byte *d, unsigned int size)
        {
            packet::data(d,size);
            sample_start_condition.address(d+4);
            dslv_lock_status.address(d+6);
            fpga_status.address(d+6);
        }
    };

    class packet_v2 : public packet
    {
    public:
        packet_v2() {}
        packet_v2(std::byte *data, unsigned int size) : packet(data,size) {}

        byte_converter<2,std::endian::big> burst_counter;     // offset: 6
        byte_converter<2,std::endian::big> data_bytes;        // the number of ADC data bytes in the packet
        byte_converter<2,std::endian::big> trigger_location;  // first byte of the first triggered sample (within the ADC bytes or including the header?) Zero if no triggered sample within the packet

        //Decoders for the R bytes (offset: 14);
        bits<2,std::endian::big,8,8> trigger_status;
        
        // Decoders for the S2 bytes (offset: 16)
        bits<2,std::endian::big,14,2> adc_stream_mode;   // 0 - off, 1 - continuous, 2 - gated, 3 - trigger
        bits<2,std::endian::big,13,1> sample_start_condition;
        bits<2,std::endian::big,12,1> trigger_edge; // 0 - rising, 1 - falling
        bits<2,std::endian::big,11,1> dual_sata_mode; 
        bits<2,std::endian::big,10,1> burst_start;

        void data(std::byte *d, unsigned int size)
            {
                packet::data(d,size);
                
                burst_counter.address(d+6);
                data_bytes.address(d+18);
                trigger_location.address(d+20);
                trigger_status.address(d+14);

                adc_stream_mode.address(d+16);
                sample_start_condition.address(d+16);
                trigger_edge.address(d+16);
                dual_sata_mode.address(d+16);
                burst_start.address(d+16);
            }
    };

    inline packet *packet::create(version ver)
    {
        switch(ver)
        {
        case v1: return new packet_v1;
        case v2: return new packet_v2;
        default: return 0;
        }
    }
    
}

#endif
