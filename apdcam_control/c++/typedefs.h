#ifndef __APDCAM10G_TYPEDEFS_H__
#define __APDCAM10G_TYPEDEFS_H__

#include <stdint.h>

namespace apdcam10g
{
    // The native type that can contain the ADC samples with their highest resolution (14 bits), used
    // for storage of the data
    typedef uint16_t data_type;         

    // The type that can contain the bit-shifted values as they arrive in the data stream, occupying
    // up to 3 bytes
    typedef uint32_t data_envelope_type;

}

#endif
