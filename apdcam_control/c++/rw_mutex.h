/*

The class 'rw_mutex' (which stands for read-write mutex) provides a tool to allow multiple simultaneous
read operations on a resource (i.e. which do not modify it), and ensure exclusivity with writing (modifying) operations.
Code that is writing (modifying) the resource must be guarded by rw_mutex::write(m); where 'm' is a rw_mutex instance,
and code that is reading the resource must be guarded by rw_mutex::read(m), as illustrated below

Usage:

rw_mutex m;

void write_operation()
{
  // Destructor of the variable 'write_lock' will release the lock
  // Do not make the mistake to create an unnamed variable like this: rw_mutex::write(m) - this creates a variable
  // which is potentially destroyed immediately and therefore the code is not guarded
  rw_mutex::write_lock wl(m);
  
  ... do some operation which modifies the resource
  // Code which is goarded by rw_mutex::write(m) can not run in parallel with
  // any code that is guarded by either rw_mutex::write(m) or rw_mutex::read(m)
}

void read_operation()
{
  rw_mutex::read_lock rl(m);  // Destructor of the variable 'read_lock' will release the lock

  ... do some operation which does not modify the resource
  // Code which is guarded by rw_mutex::read(m) can run in parallel, but not
  // with code that is guarded by rw_mutex::write(m)
}

 */

#ifndef __APDCAM_RW_MUTEX_H__
#define __APDCAM_RW_MUTEX_H__

#include <mutex>
#include <condition_variable>

// https://stackoverflow.com/questions/27860685/how-to-make-a-multiple-read-single-write-lock-from-more-basic-synchronization-pr

namespace apdcam10g
{
    class rw_mutex 
    {
    public:

        rw_mutex() : 
            shared() , 
            readerQ(), 
            writerQ() , 
            active_readers(0), 
            waiting_writers(0), 
            active_writers(0)
            {}
        
        class read_lock
        {
        private:
            rw_mutex &mutex_;
        public:
            read_lock(rw_mutex &m) : mutex_(m) { mutex_.lock_read(); }
            ~read_lock()  { mutex_.unlock_read(); }
        };
        class write_lock
        {
        private:
            rw_mutex &mutex_;
        public:
            write_lock(rw_mutex &m) : mutex_(m) { mutex_.lock_write(); }
            ~write_lock()  { mutex_.unlock_write(); }
        };

        void lock_read() 
            {
                std::unique_lock<std::mutex> lk(shared);
                while( waiting_writers != 0 )
                    readerQ.wait(lk);
                ++active_readers;
                lk.unlock();
            }
        
        void unlock_read() 
            {
                std::unique_lock<std::mutex> lk(shared);
                --active_readers;
                lk.unlock();
                writerQ.notify_one();
            }

        void lock_write() 
            {
                std::unique_lock<std::mutex> lk(shared);
                ++waiting_writers;
                while( active_readers != 0 || active_writers != 0 )
                    writerQ.wait(lk);
                ++active_writers;
                lk.unlock();
            }

        void unlock_write() 
            {
                std::unique_lock<std::mutex> lk(shared);
                --waiting_writers;
                --active_writers;
                if(waiting_writers > 0)
                    writerQ.notify_one();
                else
                    readerQ.notify_all();
                lk.unlock();
            }

        

private:
    std::mutex              shared;
    std::condition_variable readerQ;
    std::condition_variable writerQ;
    int                     active_readers;
    int                     waiting_writers;
    int                     active_writers;
};

}

#endif
