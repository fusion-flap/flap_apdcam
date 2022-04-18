#include <fcntl.h>
#include <stdio.h>
#include <errno.h>

#include "LnxClasses.h"
#include "SysLnxClasses.h"



/*
 * Mutex
 */
Mutex::Mutex() :
	m_PMutex()
{
	pthread_mutex_init(&m_PMutex, NULL);
}


Mutex::~Mutex()
{
	if (pthread_mutex_destroy(&m_PMutex) && errno == EBUSY)
	{
		pthread_mutex_unlock(&m_PMutex);
		pthread_mutex_destroy(&m_PMutex);
	}
}


void Mutex::lock()
{
	pthread_mutex_lock(&m_PMutex);
}


void Mutex::unlock()
{
	pthread_mutex_unlock(&m_PMutex);
}



/*
 * MutexGuard
 */
MutexGuard::MutexGuard(Mutex& mutex) :
	m_TargetMutex(mutex)
{
	m_TargetMutex.lock();
}


MutexGuard::~MutexGuard()
{
	m_TargetMutex.unlock();
}



/*
 * UDPBase
 */
UDPBase::UDPBase() :
	m_Socket(-1),
	m_ErrorCode(0)
{
}


UDPBase::~UDPBase()
{
}


bool UDPBase::CreateSocket()
{
	m_Socket = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
	if (m_Socket == -1)
	{
		m_ErrorCode = errno;
fprintf(stderr, "Cannot create socket: %s\n", strerror(m_ErrorCode));
		return false;
	}

	fcntl(m_Socket, F_SETFD, FD_CLOEXEC);

	return true;
}



/*
 * Thread
 */
Thread::Thread() :
	m_ExitSignal(new CLnxEvent()),
	m_tid(-1),
	m_ThreadStarted(NULL),
	m_ThreadExited(NULL)
{
}


Thread::~Thread()
{
	Stop();

	delete m_ExitSignal;
	delete m_ThreadStarted;
	delete m_ThreadExited;
}


void* Thread::start_handler(void *param)
{
	Thread *th = reinterpret_cast<Thread*>(param);

	unsigned int ret = th->Handler();
	th->OnStop();
	th->m_ThreadExited->Set();

	return reinterpret_cast<void*>(ret);
}


bool Thread::Start(bool wait)
{
	if (m_ThreadStarted == NULL)
	{
		m_ThreadStarted = new CLnxEvent();
		m_ThreadExited = new CLnxEvent();

		int status = pthread_create(&m_tid, NULL, Thread::start_handler, this);
		if (status == 0)
		{
			if (wait)
			{
				int index = -1;

				CLnxWaitForEvents waiter;
				waiter.Add(m_ThreadStarted);
				waiter.Add(m_ThreadExited);

				waiter.WaitAny(&index);
				switch (index)
				{
					case 0:
						return true;
					default:
						return false;
				}
			}

			return true;
		}

		delete m_ThreadExited;
		m_ThreadExited = NULL;
		delete m_ThreadStarted;
		m_ThreadStarted = NULL;

		return false;
	}

	/*
	 * Restart a thread that exited erroneously
	 */
	if (m_ThreadExited->IsSignaled())
	{
		Stop();
		return Start(wait);
	}

	return true;
}


void Thread::Stop()
{
	if (m_ThreadStarted && m_ThreadExited)
	{
//fprintf(stderr, "Stopping thread...\n");
		m_ExitSignal->Set();
//fprintf(stderr, "Waiting for thread to terminate...\n");
		m_ThreadExited->Wait(-1);

		pthread_join(m_tid, NULL);

		m_ExitSignal->Reset();

		delete m_ThreadExited;
		m_ThreadExited = NULL;
		delete m_ThreadStarted;
		m_ThreadStarted = NULL;
	}
}


void Thread::InitDone()
{
	m_ThreadStarted->Set();
}
