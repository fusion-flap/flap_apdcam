#ifndef __APDCAM10G_CHANNEL_DATA_PROCESSOR_H__
#define __APDCAM10G_CHANNEL_DATA_PROCESSOR_H__

#include "error.h"

namespace apdcam10g
{
  class channel_data_processor
  {
  public:
    // The actual analysis task.
    // Arguments:
    // from_counter, to_counter -- the range of data counters [inclusive] (see ring_buffer.h about the counters) which
    //                             is guaranteed to be available within the ring buffers of all channels
    // Returns:
    // The counter of the data, up to which (inclusive) channel signal data from ALL ring buffers can be dicarded
    virtual unsigned int run(unsigned int from_counter, unsigned int to_counter) = 0;
    
  };
}



#endif

