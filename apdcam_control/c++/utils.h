#ifndef __APDCAM10G_UTILS_H__
#define __APDCAM10G_UTILS_H__

#include <vector>
#include <string>

namespace apdcam10g
{
    // Split the string at the specified separators (by default: space, tab and newline), and return
    // the substring in a vector. Consecutive separator characters are treated as one single separator
    std::vector<std::string> split(const std::string &s, const std::string &separator = " \t\n");

}


#endif
