#ifndef __APDCAM10G_BYTES_H__
#define __APDCAM10G_BYTES_H__

#include <vector>
#include <cstdint>
#include <algorithm>
#include <iostream>
#include <cstddef>
#include <sstream>
#include <cmath>
#include <bit>
#include "error.h"
#include "safeness.h"


namespace apdcam10g
{
    // Ensure clear endianness (i.e. all numeric types having the same endianness... on some rare platforms
    // integer and floating-point types have different endianness, which is not handled by this code)
    // For mixed-endian systems std::endian::native does not equal any of big or little
    static_assert(std::endian::native == std::endian::big || std::endian::native == std::endian::little, "Mixed-endian system, the code can not be compiled on this machine, sorry");

    // Create a mask which has 'nbits' bits set, starting at 'startbit' (from the least significant one)
    template <typename T> T make_mask(unsigned int startbit, unsigned int nbits)
    {
        T result = 0;
        for(int i=0; i<nbits; ++i) result |= 1<<(i+startbit);
        return result;
    }

    template<bool is_signed, int N> class shortest_int 
    {
        static_assert(false,"Signed integers must be represented by the same number of bytes as their native size");
    };

    // For signed integers, specializations are only provided for the native fixed-width types
    // stored in the same number of bytes as their native size. If tried to be used with a different
    // number of bytes, the unspecified default will fail due to static_assert
    template<> class shortest_int<true,sizeof(int8_t)>  { public: typedef int8_t type; };
    template<> class shortest_int<true,sizeof(int16_t)> { public: typedef int16_t type; };
    template<> class shortest_int<true,sizeof(int32_t)> { public: typedef int32_t type; };
    template<> class shortest_int<true,sizeof(int64_t)> { public: typedef int64_t type; };

    // For unsigned integer types, all sizes up to 8 bytes are specialized, so we will not fall back to the unspecialized
    // (failing) default class above. 
    template<> class shortest_int<false,1> { public: typedef uint_fast8_t type; };
    template<> class shortest_int<false,2> { public: typedef uint_fast16_t type; };
    template<> class shortest_int<false,3> { public: typedef uint_fast32_t type; };
    template<> class shortest_int<false,4> { public: typedef uint_fast32_t type; };
    template<> class shortest_int<false,5> { public: typedef uint_fast64_t type; };
    template<> class shortest_int<false,6> { public: typedef uint_fast64_t type; };
    template<> class shortest_int<false,7> { public: typedef uint_fast64_t type; };
    template<> class shortest_int<false,8> { public: typedef uint_fast64_t type; };


    /*
      class byte_converter

      A utility class which can convert between the byte-array representation of an integer number
      in memory space (in either little or big endian format) and a native C++ integer type.

      The class is templated, giving a great flexibility with no run-time cost. The native C++
      integer type can be specified by the user, otherwise it is automatically chosen to be the shortest
      unsigned integer type needed to represent NBYTES bytes. The class offers a typedef 'type' which
      is an alias to the native C++ type

      In addition, a 'safeness' template argument decides whether during conversion (back and forth)
      any checks are made on overflow, etc. In safe mode (default), in case of a problem, an 
      apdcam10g::error exception is thrown. In unsafe mode, no checks are made

      The converter offers an (templated) assignment operator from any type which can be converted
      to the native C++ type. Assignment automatically writes into the underlying memory space (the byte array)

      The converter has a type-conversion operator to the native C++ type. Conversion is made at every call,
      so the resulting integer value will automatically update if the underlying byte-array in memory is changed.

     */

    // This first version, which automatically tried to figure out if a conversion is needed, by comparing the provided endianness to the native one, and comparing
    // the size of the type T to the required number of bytes, was removed. This could mean a non-converting byte_converter for unaligned memory addresses, which could cause
    // undefined behavior.
    //template<int NBYTES, std::endian E, safeness S=default_safeness, typename T=shortest_int<false,NBYTES>::type, bool must_convert=(std::endian::native!=E || sizeof(T)!=NBYTES)> class byte_converter {};
    template<int NBYTES, std::endian E, safeness S=default_safeness, typename T=shortest_int<false,NBYTES>::type, bool must_convert=true> class byte_converter {};


// non-converting byte_converter (i.e. last template argument being false) is disallowed, because this was implemented
// as a T-type variable allocated to a given address, which may cause an unaligned read/write operation. This is supported
// by some compilers on x86_64 platforms, but not on other platforms or by other compilers, which would cause undefined benavior.    
// If you enable this, make sure you only set the last template argument 'must_convert' to false if this converter will always only
// access memory at aligned addresses.
/*
    // The converter which actually does not make a conversion (first template argument is 'false')
    // just maps the memory representation of the given type T to the byte array
    template<int NBYTES, std::endian E, safeness S, typename T> class byte_converter<NBYTES,E,S,T,false>
    {
        // Make sure that the size of the native type T is matching the  number of bytes
        static_assert(sizeof(T)==NBYTES);
        // Also make sure that the required endianness is the system's native one
        static_assert(std::endian::native == E);
    private:
        std::byte *address_=0;
        T *value_=0;
    public:
        // A symbolic constant to query whether this particular converter is indeed
        // making any conversion in the background, or not
        const bool converts = false;

        // Symbolic typedef for the actual native C++ type, which is the shortest
        // integer type being able to store the NBYTES bytes
        typedef T type;

        // Constructor, initialize from the underlying memory region (byte array)
        byte_converter(std::byte *a=0) : address_(a), value_((T*)a) {}

        // Set the address of the underlying byte array memory storage
        void address(std::byte *a) {address_ = a; value_ = (T*)a;}

        // Assignment operator. Any type can be assigned to this object which can be
        // implicitly converted to the native type. The value is propagated down to the 
        // underlying byte array in memory
        template <typename T2>
        byte_converter<NBYTES,E,S,T,false> &operator=(const T2 &t) { *value_ = t; return *this; }

        // Type conversion operator to the native C++ type. The value is calculated from the byte
        // array at each call so it automatically updates if the byte array is changed
        operator T() const { return *value_; }
    };
*/

    template<int NBYTES, std::endian E, safeness S, typename T> class byte_converter<NBYTES,E,S,T,true>
    {
    private:
        mutable union
        {
            T value;
            std::byte mem[sizeof(T)];
        } storage_;
        std::byte *address_ = 0;
    public:
        // A symbolic constant to query whether this particular converter is indeed
        // making any conversion in the background, or not
        const bool converts = true;

        // Symbolic typedef for the actual native type
        typedef T type;

        // Constructor, initialize from the underlying memory region (byte array)
        byte_converter(std::byte *a =0) : address_(a) {}

        // Set the address of the underlying byte array memory storage
        void address(std::byte *a)
            {
                address_ = a;
            }

        // Assignment operator. Any type can be assigned to this object which can be
        // implicitly converted to the native type. The value is propagated down to the 
        // underlying byte array in memory
        template <typename T2>
        byte_converter<NBYTES,E,S,T,true> &operator=(const T2 &t)
            {
                storage_.value = t;

                if(S && NBYTES !=sizeof(T2)) // optimized out at compile time if not needed
                {
                    // Loop over the truncated bytes (the most significant ones which will be discarded
                    // because we are down-converting to a smaller number of bytes from the native type T
                    for(unsigned int i=(std::endian::native==std::endian::little ? NBYTES : 0); 
                        i<(std::endian::native==std::endian::little ? sizeof(T2) : sizeof(T2)-NBYTES); 
                        ++i)
                    {
                        if(storage_.mem[i] != (std::byte)0) 
                        { 
                            std::string msg;
                            std::ostringstream msgstream(msg);
                            msgstream<<"The value '"<<t<<"' does not fit into "<<NBYTES<<" bytes";
                            APDCAM_ERROR(msg);
                        }
                    }
                }
                

                // Now copy the least significant bytes. Remember that the native type used to represent this value, T, may be
                // longer than the number of bytes in the buffer. So we do need to take care to only copy NBYTES bytes, the
                // least significant ones
                // The conditions of these ifs are evaluable at compile time and will be optimized out
                if(std::endian::native == std::endian::little)
                {
                    if(E == std::endian::native) std::copy        (storage_.mem, storage_.mem+NBYTES,address_); // if no endianness reversion is needed
                    else                         std::reverse_copy(storage_.mem, storage_.mem+NBYTES,address_); // if endianness reversion is needed
                }
                else
                {
                    if(E == std::endian::native) std::copy        (storage_.mem+sizeof(T2)-NBYTES, storage_.mem+sizeof(T2),address_);
                    else                         std::reverse_copy(storage_.mem+sizeof(T2)-NBYTES, storage_.mem+sizeof(T2),address_);
                }
                return *this;
            }

        // Type conversion operator to the native C++ type. The value is calculated from the byte
        // array at each call so it automatically updates if the byte array is changed
        operator T() const
            {
                // Make sure that unused bytes in the native type representation are zero
                std::fill(storage_.mem,storage_.mem+sizeof(T),(std::byte)0);
                if(std::endian::native == std::endian::little)
                {
                    if(E == std::endian::native) std::copy        (address_, address_+NBYTES, storage_.mem);
                    else                         std::reverse_copy(address_, address_+NBYTES, storage_.mem);
                }
                else
                {
                    if(E == std::endian::native) std::copy        (address_, address_+NBYTES, storage_.mem+sizeof(T)-NBYTES);
                    else                         std::reverse_copy(address_, address_+NBYTES, storage_.mem+sizeof(T)-NBYTES);
                }
                return storage_.value;
            }
    };

    template<int NBYTES, std::endian E, int STARTBIT, int NBITS, safeness S=default_safeness> class bits
    {
    public:
        // A symbolic typedef: the native unsigned type that can store the the given number
        // of bits
        typedef shortest_int<false,NBITS/8+(NBITS%8?1:0)>::type type;

        // A symbolic typedef: the native unsigned type that can store the given number of BYTES
        typedef shortest_int<false,NBYTES>::type internal_type;
        
    private:
        byte_converter<NBYTES, E, S, internal_type, true > converter_;
        //byte_converter<NBYTES, E, S, shortest_int<false,NBYTES>::type, true > converter_;

        // Even though there is a general make_mask function provided, we define here a private one
        // with constexpr specification so that we guarantee compile-time evaluation
        constexpr static internal_type make_mask_(const int startbit, const int nbits)
            {
                internal_type result = 0;
                for(int i=0; i<nbits; ++i) result |= 1<<(i+startbit);
                return result;
            }

        // mask and inverse mask in-place (i.e. not shifted to the lowest bit).
        // For extracting the bit-encoded value, the mask must first be applied, and then the value
        // must be shifted
        static const internal_type mask_ = make_mask_(STARTBIT,NBITS);
        static const internal_type inverse_mask_ = ~mask_;
    public:

        bits(std::byte *a=0) : converter_(a) {}

        void address(std::byte *a) { converter_.address(a); }

        template <typename T2>
        bits<NBYTES, E, STARTBIT, NBITS, S> &operator=(const T2 &t) 
            { 
                internal_type tmp = converter_;
                converter_ = (tmp & inverse_mask_) | ((((internal_type)t)<<STARTBIT) & mask_);
                return *this; 
            }

        operator type() const { return (((internal_type)converter_)&mask_)>>STARTBIT; }

        internal_type internal_value() const { return converter_; }
    };


    /*
    class bytearray : std::vector<unsigned char>
    {
    public:
        template <typename T>
            bytearray(const T &t, endian::type byteorder, int n=0);
        
        template <typename T>
            static bytearray from(const T &t, int n, endian::type byteorder);
    };

    bytearray operator+(const bytearray &b1, const bytearray &b2)
    {
        bytearray result = b1;
        result.insert(result.end(),b2.begin(),b2.end());
        return result;
    }

    template <>
        bytearray::bytearray(const unsigned int &value, endian::type byteorder, int n) : std::vector<unsigned char>((n==0 ? sizeof(unsigned int) : n))
    {
        const int N = size();
        for(int i=0; i<N; ++i)
        {
            int target_index = i;
            if(byteorder == endian::big) target_index = N-i;
            if(i<sizeof(unsigned int)) (*this)[target_index] = (unsigned char)((value>>(8*i)) & 0xff);
            else (*this)[target_index] = 0;
        }
    }
    */
}

#endif
