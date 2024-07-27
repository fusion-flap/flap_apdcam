#ifndef __APDDCAM10G_ERROR_H__
#define __APDDCAM10G_ERROR_H__

#include <string>
#include <iostream>
#include <string.h>
#include <errno.h>

namespace apdcam10g
{
    class error
    {
    private:
        std::string message_;
        std::string file_;
        int line_;
        mutable bool handled_ = false;
    public:
        error(const std::string &message, const std::string &file, int line) : message_(message), file_(file), line_(line) {}
        
        const error &operator=(const error &rhs)
            {
                message_ = rhs.message_;
                file_ = rhs.file_;
                line_ = rhs.line_;
                handled_ = rhs.handled_;
                return *this;
            }
        
        const std::string &message() const {handled_ = true; return message_;}
        const std::string &file() const { handled_ = true; return file_; }
        int line() const { handled_ = true; return line_; }
        
        std::string full_message() const { return "ERROR: "+message()+" [in "+file()+", line "+std::to_string(line())+"]"; }
            
        ~error() 
        {
            // Seemed to be a good idea to print the message if it has not been accessed before,
            // but if the exception is not caught, its destructor is not called (because there is
            // no stack unwinding?)
            if(!handled_) std::cerr<<"Unhandled error: "<<message_<<std::endl;
        }
    };

    inline std::ostream &operator<<(std::ostream &out, const error &e) 
    {
        out<<e.full_message();
        return out;
    }
    };

#define APDCAM_ERROR(msg) throw apdcam10g::error(msg,__FILE__,__LINE__)
#define APDCAM_ERROR_ERRNO(en) throw apdcam10g::error(strerror(errno),__FILE__,__LINE__) 

#endif
