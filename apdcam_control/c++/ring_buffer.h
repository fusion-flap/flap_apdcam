#ifndef __APDCAM10G_RING_BUFFER_H__
#define __APDCAM10G_RING_BUFFER_H__

/*

  A templated ring-buffer, which automatically calls 'mlock' on the reserved memory to
  inhibit swapping it out to disk. It is implementing a FIFO queue on a fixed-size pre-allocated
  memory buffer in a cyclic way. The C++ STL container concepts are adopted (in terms of member functions
  and naming conventions - see front, back, push_back, pop_front, size, empty --- the member functions required
  for a container to be the underlying container of a std::queue (https://cplusplus.com/reference/queue/queue/)

  The data (*) can be laid out in memory (non-used bytes are shown by -) as follows

                begin()                                end()
                front()                            back()|
                  v                                     vv
  ----------------***************************************-------------------------------

            back                                          front
             v                                              v
  ************----------------------------------------------****************************

  front() and back() access the extreme elements in the buffer. begin() and end() return iterators, similarly to STL
  containers, which point to the front() element, and one beyond the back() element
  
  Whenever the container is full, no more push_back operations are possible, apdcam10g::error will be thrown.
  Similarly, if the buffer is empty, pop_front() will throw apdcam10g::error
  
  
 */

#include "error.h"
#include "safeness.h"
#include "rw_mutex.h"
#include <bit>
#include <sys/mman.h>
#include <tuple>
#include <atomic>

#include <iostream>
using namespace std;

namespace apdcam10g
{
    template <typename T = std::byte, safeness S=safe>
    class ring_buffer
    {
    private:
        mutable rw_mutex mutex_;

        // The capacity (allocated continuous memory) to store data in a cyclic way
        unsigned int capacity_ = 0;

        // The user can request to allocate an extended continuous memory region for the following purpose.
        // The data will normally still be only stored in the 'normal' memory region, i.e.
        // in the range [0..capacity_[, but the underlying continuous memory region will be longer, so that
        // if some client can only handle a continuous memory region when reading, and it wants to access
        // a range of data that is split (at the end of the buffer, and at the beginning), then instead
        // of copying/merging both of these two data segments into a newly allocated continuous memory,
        // only the segment at the beginning of the ring buffer needs to be copied to the end (if there is
        // sufficient space available)
        unsigned int extended_capacity_ = 0;

        T *buffer_= 0; // Pointer to the first object of the available buffer space

        // Offsets (with respect to the buffer's start address) of the front and back elements
        // Note that 'back' is not "past the last element", but the last one
        unsigned int back_index_, front_index_; 

        // Two absolute counters, keeping track of the counts of objects going through the
        // buffer since its last reset.
        unsigned int back_counter_, front_counter_;

        bool empty_ = true;

    public:
        typedef T type;

        ring_buffer(unsigned int capacity=0, unsigned int extended_capacity=0)
        {
            resize(capacity,extended_capacity);
        }
        ~ring_buffer()  
        { 
            ::munlock(buffer_,sizeof(T)*capacity_);
            delete [] buffer_; 
        }

        // Remember to explicitly call the constructor of mutex_(). If it is not called, it is not initialized
        // and will be in an undefinite state
        ring_buffer(const ring_buffer<T,S> &rhs) : mutex_() 
        {
            resize(rhs.capacity_,rhs.extended_capacity_);
            for(unsigned int i=rhs.front_index_; i%capacity_<rhs.back_index_; ++i)
            {
                buffer_[i%capacity_] = rhs.buffer_[i%capacity_];
                back_index_ = rhs.back_index_;
                front_index_ = rhs.front_index_;
                back_counter_ = rhs.back_counter_;
                front_counter_ = rhs.front_counter_;
            }
        }


        inline bool empty() const
        {
            rw_mutex::read_lock rl(mutex_);
            return empty_;
        }
        inline bool full() const
        {
            rw_mutex::read_lock rl(mutex_);
            return capacity_==0 || (!empty_ && back_index_==(front_index_+capacity_-1)%capacity_);
        }

        // Get the capacity (i.e. the physical size of the buffer, irrespectively of how full it is)
        unsigned int capacity() const 
            { 
                rw_mutex::read_lock rl(mutex_);
                return capacity_; 
            }

        // Return the size of data actually available in the buffer
        inline unsigned int size() const
        {
            rw_mutex::read_lock rl(mutex_);
            return (empty_ ? 0 : (back_index_ + (back_index_<front_index_?capacity_:0))-front_index_+1);
        }

        inline unsigned int available() const
        {
            rw_mutex::read_lock rl(mutex_);
            return capacity_ - (empty_ ? 0 : (back_index_ + (back_index_<front_index_?capacity_:0))-front_index_+1);
            //                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
            // This is just the same code (should be) as 'size()'
        }

        // Allocate memory for storing the data. The size of the allocated memory that will be available for
        // writing data is 'capacity', but if the argument 'extended_capacity' is not zero (and in this case must
        // be larger or equal to capacity), then in fact a larger memory region of size extended_capacity is
        // allocated. This extra space will allow copying data segments from the beginning of the buffer
        // to the end to make data available in a continuous way for clients that only can use data this way.
        // That is, we do not need to copy two data segments (from the end and from the beginning of the buffer)
        // to a newly allocated continuous memory in this case, but only the segment from the beginning of the buffer.
        // Initialize the write/read pointers to the beginning of the buffer. Reset the counter to zero.
        void resize(unsigned int capacity,unsigned int extended_capacity=0) 
        {
            if(extended_capacity==0) extended_capacity=capacity;
            if(extended_capacity<capacity) APDCAM_ERROR("Extended capacity must not be smaller than capacity");

            rw_mutex::write_lock wl(mutex_);

            // If there is previously reserved buffer, unlock it first, and then free it
            if(buffer_)
            {
                if(::munlock(buffer_,sizeof(T)*extended_capacity_) != 0) APDCAM_ERROR_ERRNO(errno);
                delete [] buffer_;
            }

            capacity_ = capacity;
            extended_capacity_ = extended_capacity_;

            // These settings themselves would be equivalent to a full buffer, but the empty_ flag indicates
            // it is in fact empty.
            // These initial values ensure that subsequent front/back increments result in a valid state
            front_index_ = 0;
            back_index_ = capacity_-1;
            empty_ = true;

            front_counter_ = 0;
            back_counter_ = (unsigned int)-1; // to ensure that the first increment brings it to zero

            // This is not an error - we allow initialization by 0 capacity (if the buffer is for example
            // contained in a vector<ring_buffer>, default constructible is a requirement), it can then be
            // resized later
            if(capacity_==0) return;

            buffer_ = new T[extended_capacity];
            if(::mlock(buffer_,sizeof(T)*extended_capacity) != 0) APDCAM_ERROR_ERRNO(errno);
        }

        // WARNING! This function is not thread-safe in the sense that even though it returns low-level memory pointers
        // for low-level write operations (to be done by the user, outside of the scope of the class) in a thread-safe way
        // (i.e. the returned pointers and size values are calculated without race condition), but exactly since the write
        // operation is outside of the scope of the class, by the user, it can get in race condition with other eventual
        // write operations on the same buffer. If there are no parallel threads that use low-level writing using this
        // function, there is no problem.
        //
        // Return one or two continuous memory regions for low-level writing of new data directly into memory, 
        // at the 'back' of the buffer. 
        // If the required size is available without splitting
        // (i.e. without jumping to the start), only the first pair (T*,int) is non-zero. Otherwise both pointers and integers
        // are non-zero, and data must be written to these two regions, in a split way. Note that this function DOES NOT INCREMENT
        // the write pointer, it must be done by the user. If the required size 'write_size' is not available, both
        // returned pointers and sizes are zero.
        // The two regions starting at buf1 (and eventually at buf2) are continuous and can be read/written by low-level
        // memcpy etc functions as well, if needed
        // Better explained through an example:
        // auto [buf1,size1,buf2,size2] = the_ring_buffer.write_region(100);
        // if(buf1==0) APDCAM_ERROR("No room to write 100 objects"); // buf1=buf1=0, size1=size2=0
        // // Here, size1+size2=100. Write 'size1' objects to the memory starting at buf1, and IF buf2!=0,
        // // write the remaining objecs (size2=100-size1) to the memory starting at buf2
        // the_ring_buffer.increment_write_ptr(100); // if successfully written
        std::tuple<T*,unsigned int,T*,unsigned int> write_region(unsigned int write_size)
        {
            // We only create a read_lock (!) and not a write lock, to ensure that we calculate the
            // pointers/sizes for the low-level memory write operations without race conditions.
            rw_mutex::read_lock rl(mutex_);
            
            // If the required size does not fit into the available free buffer (even if split), return zero
            if(write_size > available()) return {0,0,0,0};

            // If the requested size fits into a single contiguous domain at the back, return one chunk
            const int start = (back_index_+1)%capacity_; // The start pointer for the write region
            if(start+write_size<capacity_) return {buffer_+start,write_size,0,0};

            // Otherwise return 2 chunks
            const unsigned int size1 = capacity_ - start; // back_index_ is less than capacity_, guaranteed, so subtracting these unsigned ints is ok
            const unsigned int size2 = write_size-size1;
            return {buffer_+start,size1,buffer_,size2};
        }

        // Analogue of write_region(unsigned int size) - return one or two contiguous memory regions for reading, starting at the
        // front of the buffer
        // 'offset' is an optional offset value counted from the front of the buffer
        std::tuple<T*,unsigned int, T*,unsigned int> read_region(unsigned int read_size, unsigned int offset=0)
        {
            rw_mutex::read_lock rl(mutex_);
            if((empty_ ? 0 : (back_index_ + (back_index_<front_index_?capacity_:0))-front_index_+1) < offset+read_size) return {0,0,0,0};
            //  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^  this is equivalent to 'size()'
            const unsigned int start = (front_index_+offset)%capacity_;
            if(start+read_size <= capacity_) return {buffer_+start,read_size,0,0};
            const unsigned int size1 = capacity_ - start; // front_index_ is less than capacity_, guaranteed, so subtracting these two unsigned ints is ok
            const unsigned int size2 = read_size-size1;
            return {buffer_+start,size1,buffer_,size2};
        }

        // The same as read_region, but if the requested data is only available in a split way, copy
        // the segment from the beginng of the buffer to the end (into the extended memory region), if it fits.
        // If it does not fit, or if the required amount of data is not available, return zero
        // Note that data copying is made by memcpy, i.e. not by object copy constructors. 
        T* read_region_continuous(unsigned int read_size, unsigned int offset=0)
        {
            rw_mutex::read_lock rl(mutex_);
            if((empty_ ? 0 : (back_index_ + (back_index_<front_index_?capacity_:0))-front_index_+1) < offset+read_size) return 0;
            //  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^  this is equivalent to 'size()'
            const unsigned int start = (front_index_+offset)%capacity_;

            // If this size is available continuously, just return
            if(start+read_size <= capacity_) return buffer_+start;

            // If the flattened data would not fit into the extended range, return zero
            if(start+read_size >= extended_capacity_) return 0;


            const unsigned int size1 = capacity_ - start; // front_index_ is less than capacity_, guaranteed, so subtracting these two unsigned ints is ok
            const unsigned int size2 = read_size-size1;
            memcpy(buffer_+capacity_,buffer_,size2*sizeof(T));
            return buffer_+start;
        }

        // The same as read_region_continuous, but accessing a data range by the absolute object counter.
        T *operator()(unsigned int counter_from, unsigned int counter_to)
        {
            if(S==safe)
            {
                if(counter_from < front_counter_ || back_counter_ <= counter_to) APDCAM_ERROR("Trying to access out-of-range data by counter in ring buffer");
            }
            unsigned int offset = counter_from - front_counter_;
            unsigned int read_size = counter_to - counter_from + 1;
            return read_region_continuous(read_size,offset);
        }
        
        // Iterators
        
        class iterator
        {
        private:
            ring_buffer<T,safe> *buffer_ = 0;
            // The index does not cycle back to the start when incremented, so that we can
            // discrimintate begin() and end() in the case of a full buffer (when the wo would be equal)
            // Remember that end() is pointing one behind the back, so for a full buffer it would be
            // the same as begin()
            unsigned int index_;
        public:
            iterator(ring_buffer<T,safe> *b,unsigned int index) : buffer_(b),index_(index) {}
            const iterator &operator++() { ++index_; return *this; }
            T &operator*()  { return buffer_->buffer_[index_%buffer_->capacity_]; }
            T *operator->() { return buffer_->buffer_ + (index_%buffer_->capacity_); }
            bool operator==(const iterator &rhs) { return index_==rhs.index_ && buffer_==rhs.buffer_; }
            bool operator!=(const iterator &rhs) { return index_!=rhs.index_ || buffer_!=rhs.buffer_; }

            // Return the global, absolute object counter associated with the object pointed to
            unsigned int counter() 
            {
                if(index_>=buffer_->front_index_) return buffer_->front_counter_ + index_-buffer_->front_index_;
                return buffer_->front_counter_ + index_ + buffer_->capacity_ - buffer_->front_index_;
            }
        };

        friend iterator;

        iterator begin() { rw_mutex::read_lock rl(mutex_); if(empty_) return end(); return iterator(this,front_index_);}
        iterator end()   { rw_mutex::read_lock rl(mutex_); return iterator(this,back_index_+(back_index_<front_index_?capacity_:0)+1); }

        T &front() 
        { 
            rw_mutex::read_lock rl(mutex_);
            if(S==safe && empty_) APDCAM_ERROR("Empty ring buffer in ring_buffer::front()");
            return buffer_[front_index_]; 
        }
        T &back() 
        { 
            rw_mutex::read_lock rl(mutex_);
            if(S==safe && empty_) APDCAM_ERROR("Empty ring buffer in ring_buffer::back()");
            return buffer_[back_index_]; 
        }

        // Append a new object to the back of the buffer. 
        // If S==safe, it never returns false but throws apdcam10g::error instead
        void push_back(const T& obj) 
        {
            rw_mutex::write_lock wl(mutex_);
            // Since we already created a write lock, we call the 'increment_write_ptr<false>' template function
            // to avoid a second lock
            if(increment_write_ptr_nolock(1)) buffer_[back_index_] = obj;
        }

        // Remove the front element from the queue. Returns true if success (i.e. the queue was not empty),
        // false otherwise
        // If S==safe, it never returns false but throws apdcam10g::error instead
        bool pop_front()
        {
            // increment_read_ptr itself creates a lock, and we do not do any extra here,
            // so no need to lock here
            return increment_read_ptr(1); // This will set empty condition as well, if needed
        }

        // Remove n elements from the front. Returns true if success (i.e. there were enough elements to be
        // popped), false otherwise
        // If S==safe, it never returns false but throws apdcam10g::error instead
        bool pop_front(unsigned int n)
        {
            // increment_read_ptr itself creates a lock, and we do not do any extra here,
            // so no need to lock here
            return increment_read_ptr(n); // This will set empty condition as well, if needed
        }

        // Clear the buffer: remove all elements, make it empty
        void clear()
        {
            rw_mutex::write_lock wl(mutex_);
            
            front_index_=0;
            back_index_=capacity_-1;
            empty_ = true;

            // This is an invalid state! front_counter_ > back_counter_. Reason: upon writing to the buffer,
            // only the back_counter_ is incremented, the front_counter_ not. In order to keep this, 
            // we anticipate, and set front_counter_ to the value it should have after the next write operations.
            // In an empty state, accessing these counters is anyway meaningless.
            front_counter_ = back_counter_+1;
        }

        // Increment the write pointer by 'n', returns true if it could be done without
        // going beyond the read pointer, false otherwise.
        // If S==safe, the function does not return false but throws an apdcam10g::error instead
        bool increment_write_ptr_nolock(unsigned int n)
        {
            if(n==0) return false;
            
            if(n>capacity_)
            {
                if(S==safe) APDCAM_ERROR("Can not increment write pointer of ring buffer by more than its capacity");
                return false;
            }
            
            if(!empty_ && back_index_+n >= front_index_+(back_index_>=front_index_?capacity_:0))
            {
                if(S==safe) APDCAM_ERROR("Can not increment write pointer of ring buffer by this amount");
                return false;
            }
            // else -- return false if we want to increase by more than capacity, but this has already been treated
            
            back_index_ = (back_index_+n)%capacity_;
            back_counter_ += n;
            empty_ = false;
            return true;
        }

        bool increment_write_ptr(unsigned int n)
        {
            rw_mutex::write_lock wl(mutex_);
            return increment_write_ptr_nolock(n);
        }    
        

        // Increment the read pointer by 'n'. Returns true if there were enough elements for the required
        // increment, false otherwise
        // If S==safe, the function will never return false but throw an apdcam10g::error instead
        bool increment_read_ptr(unsigned int n=1)
        {
            rw_mutex::write_lock wl(mutex_);
            if(empty_)
            {
                if(S==safe) APDCAM_ERROR("Can not call increment_read_ptr on an empty ring buffer");
                return false;
            }

            // Remember not to subtract unsigned ints, transform your formulae to use only addition
            const unsigned int tmp1 = front_index_+n;
            const unsigned int tmp2 = back_index_+(front_index_>back_index_?capacity_:0)+1;

            // We can not increment by this amount, there are not so many elements available
            if(tmp1>tmp2)
            {
                if(S==safe) APDCAM_ERROR("Can not call increment_read_ptr on an empty ring buffer");
                return false;
            }

            // front_index exceeds back_index by one. This would be equivalent to a full buffer, but now
            // it means we popped all elements, so switch on the empty state
            if(tmp1==tmp2) empty_ = true;
            front_index_ = (front_index_+n)%capacity_;
            front_counter_ += n;
            
            return true;
        }

        // Return the counters (sequential number of the going-through objects starting from 0)
        // associated with the front and back elements.
        // Note that these return invalid values when called on an empty buffer
        // If S==safe, apdcam10g::error is thrown if the buffer is empty
        unsigned int front_counter() const 
            {
                rw_mutex::read_lock rl(mutex_);
                if(S == safe && empty_) APDCAM_ERROR("Empty ring buffer, ring_buffer::front_counter() must not be called");
                return front_counter_;
            }
        unsigned int back_counter() const 
            {
                rw_mutex::read_lock rl(mutex_);
                if(S == safe && empty_) APDCAM_ERROR("Empty ring buffer, ring_buffer::front_counter() must not be called");
                return back_counter_;
            }


        // Access objects based on the absolute object counter. 
        // If the template parameter 'S' is 'safe', range-checking is done, out-of-range access will throw apdcam10g::error
        // Otherwise no check is made, and out-of-range access will result in undefined behavior
        T &operator()(unsigned int counter)
        {
            rw_mutex::read_lock rl(mutex_);
            if(S == safe) // Optimized out if not true
            {
                if(counter<front_counter_ || back_counter_<counter) APDCAM_ERROR("Trying to access out-of-range data in ring_buffer by the () operator");
            }
            return buffer_[(front_index_+counter-front_counter_)%capacity_];
        }

        
        

        // Access objects indexed from the front of the buffer. That is, offset=0 will return the front object
        // With 'S'=='safe', range checking is done and out-of-range access will throw apdcam10g::error
        // Otherwise no range-checking is made and out-of-range access will result in undefined behavior
        T &operator[](unsigned int offset)
        {
            rw_mutex::read_lock rl(mutex_);
            if(S == safe)
            {
                if(front_index_+offset > back_index_+(front_index_>back_index_?capacity_:0)) APDCAM_ERROR("Trying to access out-of-range data in ring_buffer by the [] operator");
            }
            return buffer_[(front_index_+offset)%capacity_];
        }
    };



             

}

#endif
