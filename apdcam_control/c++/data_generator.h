#ifndef __APDCAM10G_DATA_GENERATOR_H__
#define __APDCAM10G_DATA_GENERATOR_H__

#include "typedefs.h"

namespace apdcam10g
{
    // Base class to declare the interface for a per-ADC data generator service,
    // which will generate data values for a given channel of the ADC according to
    // some algorithm, upon each subsequent call to generate(channel_no);
    class data_generator
    {
    private:
        unsinged int resolution_bits_ = 14;
        data_type max_value_ = pow(2,14)-1;
    public:
        data_generator &resolution_bits(unsigned int r) { resolution_bits_ = r; max_value_ = pow(2,r)-1; return *this; }

        // Generate a value for a channel specified by chip number(0..3)  and channel number(0..7)
        data_type generate(unsigned int chip_number, unsigned int channel_number) { return generate(chip_number*8+channel_number); }

        // Generate value based on channel number only (0..31)
        virtual data_type generate(unsigned int channel_number) = 0;

        class monotonic;
    };

    class data_generator::monotonic : data_generator
    {
    private:
        data_type current_values_[32];
    public:
        monotonic() {for(unsigned int i=0; i<32; ++i) current_values_[i] = 0;}

        data_type generate(unsigned int channel_number) override
        {
            const data_type result = current_value_[channel_number];
            if(++current_value_[channel_number] > max_value_) current_value_[channel_number] = 0;
            return result;
        }
    };

}

#endif
