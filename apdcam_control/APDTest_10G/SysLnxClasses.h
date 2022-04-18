#ifndef __SYSLNXCLASSES_H__

#define __SYSLNXCLASSES_H__

#include <pthread.h>
#include <unistd.h>

#include "InterfaceDefs.h"

class Mutex
{
public:
	Mutex();
	~Mutex();

	void lock();
	void unlock();
private:
	pthread_mutex_t m_PMutex;
	Mutex(const Mutex&);
	Mutex& operator=(const Mutex&);
};


class MutexGuard
{
public:
	MutexGuard(Mutex &);
	void assertIdenticalMutex(const Mutex &) const;
	~MutexGuard();
private:
	Mutex &m_TargetMutex;
	MutexGuard(const MutexGuard &);
	MutexGuard& operator=(const MutexGuard &);
};


class UDPBase
{
public:
	UDPBase(void);
	virtual ~UDPBase(void);

	int GetLastError() const { return m_ErrorCode; }

protected:
	class socketRAII
	{
	public:
		socketRAII(int& sock) : m_Socket(sock) {};
		~socketRAII() {close(m_Socket);}
	private:
		int& m_Socket;
	};

	int m_Socket;
	int m_ErrorCode;

	bool CreateSocket();
};


class Thread
{
public:
	Thread();
	virtual ~Thread();

	bool Start(bool wait = false);
	void Stop();

protected:
	CEvent *m_ExitSignal;

	static void* start_handler(void*);
	virtual unsigned int Handler(void) = 0;
	virtual void OnStop() {};
	void InitDone();

private:
	Thread(const Thread &);
	Thread& operator=(const Thread &);
	pthread_t  m_tid;
	CEvent    *m_ThreadStarted;
	CEvent    *m_ThreadExited;
};

#endif  /* __SYSLNXCLASSES_H__ */
