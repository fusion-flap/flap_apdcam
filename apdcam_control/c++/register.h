#ifndef __APDCAM10G_REGISTER_H__
#define __APDCAM10G_REGISTER_H__

#include "bytes.h"
#include <vector>
#include <map>
#include <string>
#include <iostream>

namespace apdcam10g
{

    class apdcam_register
    {
    private:
        std::string name_;
        unsigned int start_address_; // Offset within a memory buffer
        std::string short_description_, long_description_;
    public:
        apdcam_register(const std::string &name, unsigned int start_addr, const std::string &short_description, const std::string &long_description) 
            : name_(name), start_address_(start_addr), short_description_(short_description), long_description_(long_description) {}
        const std::string &name() const { return name_; }
        unsigned int start_address() const { return start_address_; }
        const std::string &short_description() const { return short_description_; }
        const std::string &long_description() const { return long_description_; }
        virtual std::string to_string() const { return ""; }
    };

    template <bool is_signed, int N, std::endian E, bool check=true>
    class apdcam_int_register : public apdcam_register
    {
    private:
        typedef shortest_int<is_signed,N>::type type;
        byte_converter<(E != std::endian::native || sizeof(type) != N), N, E, check> byte_converter_;
    public:
        
    };

    

    std::ostream &operator<<(std::ostream &out, const apdcam_register &r)
    {
        out<<"start: "<<r.start_address()<<", length:"<<r.length()<<", description: "<<r.long_description()<<std::endl;
        return out;
    }


    template <typename T>
    struct members
    {
        typedef apdcam_register T::*register_ptr;
        struct register_record
        {
            std::string name;
            register_ptr ptr;
        };
        static std::vector<register_record> &list() { static std::vector<register_record> l; return l; }
        
        struct reset
        {
            reset() { members::list().clear(); }
        };
        struct add
        {
            add(const std::string &name, register_ptr ptr) { members::list().push_back({name,ptr}); }
        };
    };


    class register_table
    {
    public:
    };

#define REG_INT(name__,start__,length__,is_signed__,byte_order__,short_description__,long_description__) \
    apdcam_register *name__ = {#name__,start__,length__,is_signed__,byte_order__,short_description__,long_description__}; \
    members<mytype>::add name__##_add = {#name__,&mytype::name__};

#define REGTABLE(name__,...) \
    class name__ \
    { \
    private: \
        std::vector<members<name__>::register_record> members_;   \
    public: \
        typedef name__ mytype; \
        members<mytype>::reset reset_; \
        __VA_ARGS__; \
        name__() \
        { \
            members_ = members<mytype>::list(); \
        } \
        void show_members() \
        { \
            for(auto m : members_) std::cerr<<m.name<<" "<<this->*m.ptr<<std::endl; \
        }\
    };
    


REGTABLE(adc_registers,
         REG(reg1,0,1,false,endian::big,"short description 1","long description 1");
         REG(reg2,1,3,false,endian::big,"short description 2","long description 2");

    );

}


#endif
