#ifndef __APDCAM10G_CHANNEL_INFO_H__
#define __APDCAM10G_CHANNEL_INFO_H__

#include "typedefs.h"

namespace apdcam10g
{

    /*
      This class stores information about how the channel data is encoded in the byte stream of a given ADC board,
      taking into account which channels are enabled, and what is the bit-resolution
     */

    struct channel_info
    {
        // The number (0..3) of the ADC board of this channel
        unsigned int board_number;

        // The number (0..3) of the chip within the ADC board
        unsigned int chip_number;

        // The channel number (0..31 inclusive) within the ADC board
        unsigned int channel_number;

        // The absolute channel number (0..127 inclusive)
        unsigned int absolute_channel_number;

        // The offset of the first byte (full or partial) of this channel w.r.t. the ADC board's data, 
        // i.e. the first byte of the first (enabled) channel of the first chip. 
        unsigned int byte_offset;
        
        // The number of bytes that this value is extending over.
        unsigned int nbytes;

        // The amount of bitwise right-shift (i.e. towards least significant bit)
        unsigned int shift;

        /*
        // A sample of 14 bits could possibly extend over 3 bytes. These are the masks to get them out
        data_type masks[3];
        
        // The bit-shift value for the given byte, within the 16-bit result integer. Positive value means a left-shift (i.e. toward
        // more significant bits), negative means right-shift
        int shifts[3];
        */
    };
}

#endif
