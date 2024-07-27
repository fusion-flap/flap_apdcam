#ifndef __SAFENESS_H__
#define __SAFENESS_H__

namespace apdcam10g
{
    enum safeness { safe, unsafe };

    namespace
    {
        const apdcam10g::safeness default_safeness = unsafe;
    }
}


#endif
