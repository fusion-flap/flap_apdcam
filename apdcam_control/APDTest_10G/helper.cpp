#include <arpa/inet.h>
#include <string.h>
#include <time.h>
#include <stdio.h>

#include "helper.h"


int memcpy_s(void *dest, size_t nelem, const void *src, size_t count)
{
	if (dest && src && nelem >= count)
	{
		memcpy(dest, src, count);
		return 0;
	}

	return EINVAL;
}

bool QueryPerformanceCounter(LARGE_INTEGER *li)
{
	li->QuadPart = 1;
	return true;
}

bool QueryPerformanceFrequency(LARGE_INTEGER *li)
{
	li->QuadPart = 1;
	return true;
}

void Sleep(int64_t msec)
{
	struct timespec ts = { msec / 1000, (msec % 1000) * 1000000};

	nanosleep(&ts, NULL);
}
