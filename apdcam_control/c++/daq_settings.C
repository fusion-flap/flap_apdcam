#include <jsoncpp/json/json.h>
// Write/read settings using JSON

#include <fstream>

#include "daq_settings.h"
#include "error.h"
#include "bytes.h"
#include "packet.h"
#include "pstream.h"

using namespace std;

namespace apdcam10g
{
    void daq_settings::print_channel_map(std::ostream &out)
    {

        for(int i=0; i<channelinfo_.size(); ++i)
        {
            out<<endl<<"ADC "<<i<<endl;
            out<<"Resolution: "<<resolution_bits_[i]<<endl;

            out<<endl;
            for(auto c : channelinfo_[i])
            {
                out<<"channel number: "<<c.channel_number<<endl;
                out<<"byte offset   : "<<c.byte_offset<<endl;
                out<<"nbytes        : "<<c.nbytes<<endl;
                out<<"shift         : "<<c.shift<<endl;
                out<<endl;
            }
        }
    }

    daq_settings &daq_settings::mtu(unsigned int m)
    {
        mtu_ = m; 
        const int max_adc_data_length = mtu_ - (packet::ipv4_header+packet::udp_header+packet::cc_streamheader);
        octet_ = max_adc_data_length/8; // INTEGER DIVISION!
        if (octet_ < 1) APDCAM_ERROR("MTU value is too small!");
        max_udp_packet_size_ = 8*octet_ + packet::cc_streamheader;
        return *this; 
    }    

    daq_settings &daq_settings::get_net_parameters()
    {
        bool mtu_ok=false, mac_ok=false, ip_ok=false;

        {
            string cmd_string = "ip link show " + interface_;
            ipstream cmd(cmd_string);
            string s;
            while(cmd>>s)
            {
                if(s == "mtu")
                {
                    unsigned int m;
                    cmd>>m;
                    mtu(m); // Set MTU and calculate 'octet_'
                    mtu_ok = true;
                }
                /*
                if(s == "link/ether") 
                {
                    cmd>>s;
                    auto ss = split(s,":");
                    if(ss.size() != 6) APDCAM_ERROR("The MAC address returned by the command '" + cmd_string+ "' does not contain 6 bytes");
                    for(int i=0; i<6; ++i) mac_[i] = std::stol(ss[i],0,16);
                    mac_ok = true;
                }
                */
            }
        }

        /*
        {
            string cmd_string = "ip -o address show " + interface_;
            auto cmd = ipstream(cmd_string);
            string s;
            while(cmd>>s)
            {
                if(s=="inet")
                {
                    cmd>>s;
                    ip_ = split(s,"/")[0];
                    ip_ok = true;
                }
            }
        }

        if(!mtu_ok || !mac_ok || !ip_ok)
        {
            string cmd_string = "ifconfig " + interface_;
            ipstream cmd(cmd_string);
            string s;
            while(cmd>>s)
            {
                if(s=="mtu")
                {
                    cmd>>mtu_;
                    mtu_ok = true;
                }
                if(s=="ether") 
                {
                    cmd>>s;
                    auto ss = split(s,":");
                    if(ss.size() != 6) APDCAM_ERROR("The MAC address returned by the command '" + cmd_string+ "' does not contain 6 bytes");
                    for(int i=0; i<6; ++i) mac_[i] = std::stol(ss[i],0,16);
                    mac_ok = true;
                }
                if(s=="inet")
                {
                    cmd>>ip_;
                    ip_ok = true;
                }
            }
        }
        if(!mtu_ok || !mac_ok || !ip_ok) APDCAM_ERROR("Could not determine MTU, MAC or IP");
        */


        cerr<<"Interface: "<<interface_<<endl;
        cerr<<"MTU      : "<<mtu_<<endl;
        //cerr<<"MAC      : ";
        //for(unsigned int i=0; i<6; ++i) cerr<<(i>0?":":"")<<hex<<(int)mac_[i]<<dec;
        //cerr<<endl;
        //cerr<<"IP       : "<<ip_<<endl;
        cerr<<"OCTET    : "<<octet_<<endl;

        return *this;
    }    

    void daq_settings::calculate_channel_info()
    {
        // channel_masks_ and resolution_bits_ must have been set before!
        
        const int nof_adc = channel_masks_.size();
        board_bytes_per_shot_.resize(nof_adc);
        chip_bytes_per_shot_.resize(nof_adc);
        for(auto &v : chip_bytes_per_shot_) v.resize(4);
        chip_offset_.resize(nof_adc);
        for(auto &v : chip_offset_) v.resize(4);
        channelinfo_.resize(nof_adc);
        for(auto &i : channelinfo_) i.clear();

        for(unsigned int i_adc=0; i_adc<nof_adc; ++i_adc)
        {
            
            board_bytes_per_shot_[i_adc] = 0;

            for(unsigned int i_chip=0; i_chip<4; ++i_chip)
            {
                if(i_chip==0) chip_offset_[i_adc][i_chip] = 0;
                else          chip_offset_[i_adc][i_chip] = chip_offset_[i_adc][i_chip-1] + chip_bytes_per_shot_[i_adc][i_chip-1];

                // start accumulating the chip's bytes per shot from zero
                chip_bytes_per_shot_[i_adc][i_chip] = 0;

                // The offset of the given channel in terms of bits w.r.t. the given chip's first bit, a sliding value
                unsigned int channel_bit_offset = 0;

                // Calculate the number of bits used by this chip (a chip is a group of 8 channels). 
                for(unsigned int i_channel=0; i_channel<8; ++i_channel)
                {
                    // skip disabled channels
                    if(!channel_masks_[i_adc][i_chip][i_channel]) continue;

                    channel_info chinfo;
                    chinfo.board_number = i_adc;
                    chinfo.chip_number = i_chip;
                    chinfo.channel_number = i_chip*8 + i_channel;
                    chinfo.absolute_channel_number = i_adc*4*8 + i_chip*8 + i_channel;
                    chinfo.byte_offset    = chip_offset_[i_adc][i_chip] + channel_bit_offset/8;

                    // The first bit of this channel's value within the byte, STARTING FROM LEFT, FROM THE MOST SIGNIFICANT BIT
                    const unsigned int startbit = channel_bit_offset%8; // starting from 'left', that is, from the most significant bit

                    // The number of bytes over which this value is distributed
                    chinfo.nbytes = (startbit+resolution_bits_[i_adc])/8 + ((startbit+resolution_bits_[i_adc])%8 ? 1 : 0);

                    // The right-shift (deduced from the last bit of this value within the last byte)
                    chinfo.shift = 8-((startbit+resolution_bits_[i_adc])%8); 

                    // Checks
                    if(chinfo.nbytes == 1 && chinfo.shift != 0) APDCAM_ERROR("Bug! With 1 bytes the shift should be 1.");
                    

/*                    
                    int remaining_bits = resolution_bits_[i_adc];
                    
                    // The portion of this value falling into the first byte. Since the APD resolution is at least 8 bits,
                    // the first byte is in any case right-aligned (i.e. towards the least significant bits). If it starts at the
                    // most significant bit, it will occupy the full byte (so this is right-aligned). If it does not start at the
                    // most significant bit, then it will occupy all less-significant bits, so it is right-aligned.
                    {
                        const int startbit = channel_bit_offset%8; // starting from 'left', that is, from the most significant bit
                        const int nbits = std::min(remaining_bits,8-startbit); // the number of most significant bits of the value to be encoded in the first byte
                        //chinfo.masks[0] = make_mask<data_type>(8-startbit-nbits, nbits);
                        remaining_bits -= nbits;
                        //chinfo.shifts[0] = -8+startbit+nbits+remaining_bits;  // this needs to be everywhere -1*(1st arg of make_mask)+remaining_bits
                        chinfo.nbytes = 1;
                    }

                    // If the value did not fully fit into the first byte, take the second byte. The remaining
                    // bits of the value are left-aligned within the 8 bits of this byte
                    if(remaining_bits > 0)
                    {
                        const int startbit = 0; // starting from 'left', that is, from the most significant bit
                        const int nbits = std::min(remaining_bits,8-startbit);
                        chinfo.masks[1] = make_mask<data_type>(8-nbits, nbits);
                        remaining_bits -= nbits;
                        chinfo.shifts[1] = -8+nbits+remaining_bits;
                        chinfo.nbytes = 2;
                    }
                    else
                    {
                        chinfo.masks[1] = 0;
                        chinfo.shifts[1] = 0;
                    }

                    // If the value did not fully fit into the first 2 bytes, take the 3rd byte. Left aligned.
                    if(remaining_bits > 0)
                    {
                        const int startbit = 0; // starting from 'left', that is, from the most significant bit
                        const int nbits = std::min(remaining_bits,8-startbit);
                        chinfo.masks[2] = make_mask<uint_fast16_t>(8-nbits, nbits);
                        remaining_bits -= nbits;
                        chinfo.shifts[2] = -8+nbits+remaining_bits;
                        chinfo.nbytes = 3;
                    }
                    else
                    {
                        chinfo.masks[2] = 0;
                        chinfo.shifts[2] = 0;
                    }

                    if(remaining_bits != 0) APDCAM_ERROR("The channel bits do not fit into 3 bytes (bug)");
*/

                    channelinfo_[i_adc].push_back(chinfo);
                    channel_bit_offset += resolution_bits_[i_adc];
                }

                // channel_bit_offset here is the number of bits used for this chip. Calculate the number of full bytes
                // which can contain this many bits
                // const int variable named only to clearly indicate what we do. Used only in the next line
                chip_bytes_per_shot_[i_adc][i_chip] = channel_bit_offset/8 + (channel_bit_offset%8 ? 1 : 0);

                // Accumulate the number of bytes by each chip
                board_bytes_per_shot_[i_adc] += chip_bytes_per_shot_[i_adc][i_chip];
            }

            // Round up the number of bytes of an ADC board to an integer multiple of 4 bytes
            if(board_bytes_per_shot_[i_adc]%4 != 0) board_bytes_per_shot_[i_adc] = (board_bytes_per_shot_[i_adc]/4+1)*4;
        }
    }

    void daq_settings::write(const std::string &filename)
    {
        Json::Value settings_root;
        for(unsigned int i_adc=0; i_adc<channel_masks_.size(); ++i_adc)
        {
            settings_root["resolution_bits"][i_adc] = resolution_bits_[i_adc];
            settings_root["resolution_bits"][i_adc].setComment(Json::String(("// ADC " + std::to_string(i_adc)).c_str()),Json::commentAfterOnSameLine);
            for(unsigned int i_chip=0; i_chip<4; ++i_chip)
            {
                for(unsigned int i_channel=0; i_channel<8; ++i_channel)
                {
                    const bool b = channel_masks_[i_adc][i_chip][i_channel];
                    settings_root["channel_masks"][i_adc][i_chip][i_channel] = b;
                    settings_root["channel_masks"][i_adc][i_chip][i_channel].setComment(Json::String(("// Channel " + std::to_string(i_channel)).c_str()),Json::commentAfterOnSameLine);
                }
                settings_root["channel_masks"][i_adc][i_chip].setComment(Json::String(("// Chip " + std::to_string(i_chip)).c_str()),Json::commentBefore);
            }
            settings_root["channel_masks"][i_adc].setComment(Json::String(("// ADC " + std::to_string(i_adc)).c_str()),Json::commentBefore);
        }
        ofstream file(filename);
        file<<settings_root<<endl;
    }

    bool daq_settings::read(const std::string &filename)
    {
        ifstream file(filename);
        if(!file) return false;
        Json::Value settings_root;
        file>>settings_root;
        for(auto key: {"resolution_bits","channel_masks"})
        {
            if(!settings_root.isMember(key)) APDCAM_ERROR(string("Value '") + key + "' is not stored in the file '" + filename + "'");
        }

        const int n_adc = settings_root["channel_masks"].size();
        if(settings_root["resolution_bits"].size() != n_adc) APDCAM_ERROR("The arrays 'channel_masks' and 'resolution_bits' must have the same size in file '" + filename + "'");
        channel_masks_.resize(n_adc);
        for(auto &a : channel_masks_) 
        {
            a.resize(4);
            for(int i=0; i<4; ++i) a[i].resize(8);
        }
        resolution_bits_.resize(n_adc);

        for(unsigned int i_adc=0; i_adc<n_adc; ++i_adc)
        {
            resolution_bits_[i_adc] = settings_root["resolution_bits"][i_adc].asInt();
            for(unsigned int i_chip=0; i_chip<4; ++i_chip)
            {
                for(unsigned int i_channel=0; i_channel<8; ++i_channel)
                {
                     channel_masks_[i_adc][i_chip][i_channel] = settings_root["channel_masks"][i_adc][i_chip][i_channel].asBool();
                }
            }
        }

        calculate_channel_info();
        return true;
    }

}
