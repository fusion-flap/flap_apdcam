/*

  std::binary_semaphore is not safe in the sense that multiple calls to release() cause undefined behavior.
  See this for example: https://stackoverflow.com/questions/75556262/c20-binary-semaphore-goes-over-max

  On the other hand, access to the semaphore's state, and releasing it only if it is in acquired state,
  is not possible.

  Take the following situation: a producer thread writes data into a buffer, in a repeated way (dumping UDP packets
  received from the network). A consumer thread is reading this data.
  The consumer thread wants to block until there is new data, so first thouhgt is using a semaphore. The
  producer thread releases the semaphore after writing each UDP packet to the buffer. 
  However, if processing the data takes long, and several UDP packets arrive in the meantime,
  (which is a valid behavior), the semaphore would be released multiple times.

  safe_semaphore is a binary semaphore which can be released multiple times. The 2nd and later releases (without
  an intervening acquire()) do nothing. 

 */

#ifndef __APDCAM10G_SAFE_SEMAPHORE_H__
#define __APDCAM10G_SAFE_SEMAPHORE_H__

#include <condition_variable>
#include <mutex>

namespace apdcam10g
{
    class safe_semaphore
    {
    private:
        std::mutex mutex_;
        std::condition_variable cv_;
        bool state_ = false;
    public:
        inline void release()
        {
            {
                std::lock_guard lk(mutex_);
                state_ = true;
            }
            cv_.notify_all();
        }
        inline void acquire()
        {
            std::unique_lock lk(mutex_);
            cv_.wait(lk, [this]{ return state_; });
            state_ = false;
        }
    };
}
#endif
