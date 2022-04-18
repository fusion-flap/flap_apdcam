#ifndef __HELPER_H__

#define __HELPER_H__

#include <errno.h>
#include <wchar.h>
#include <endian.h>
#include <byteswap.h>

#include "TypeDefs.h"

//#define min(a,b)	(((a) < (b)) ? (a) : (b))
#define MIN(a,b)        (((a) < (b)) ? (a) : (b))

#if __BYTE_ORDER == __LITTLE_ENDIAN
#define htonll(x)   bswap_64(x)
#define ntohll(x)   bswap_64(x)
#else
#define htonll(x)   (x)
#define ntohll(x)   (x)
#endif

#if 0
uint64_t htonll(uint64_t h_value)
{
	// The answer is 42
	static const int num = 42;

	// Check the endianness
	if (*reinterpret_cast<const char*>(&num) == num)
	{
		const uint32_t high_part = htonl(static_cast<uint32_t>(h_value >> 32));
		const uint32_t low_part = htonl(static_cast<uint32_t>(h_value & 0xFFFFFFFFLL));

		return (static_cast<uint64_t>(low_part) << 32) | high_part;
	}
	else
	{
		return h_value;
	}
}


uint64_t ntohll(uint64_t n_value)
{
	// The answer is 42
	static const int num = 42;

	// Check the endianness
	if (*reinterpret_cast<const char*>(&num) == num)
	{
		const uint32_t high_part = ntohl(static_cast<uint32_t>(n_value >> 32));
		const uint32_t low_part = ntohl(static_cast<uint32_t>(n_value & 0xFFFFFFFFLL));

		return (static_cast<uint64_t>(low_part) << 32) | high_part;
	}
	else
	{
		return n_value;
	}
}
#endif


#define MSB_TO_HOST_16(x, type)   ntohs (*reinterpret_cast<const be ## type*>(x))
#define MSB_TO_HOST_32(x, type)   ntohl (*reinterpret_cast<const be ## type*>(x))
#define MSB_TO_HOST_64(x, type)   ntohll(*reinterpret_cast<const be ## type*>(x))

#define CHAR_TO_TYPE(x, type)     (*reinterpret_cast<type*>(x))

#ifdef APDCAM_UNICODE
# define _tprintf	wprintf
# define _stprintf	swprintf
# define _T(x)		L##x
# define TEXT(x)	L##x
#else
# define _tprintf	printf
# define _stprintf	sprintf
# define _T(x)		x
# define TEXT(x)	x
#endif
int memcpy_s(void *dest, size_t nelem, const void *src, size_t count);
bool QueryPerformanceCounter(LARGE_INTEGER *li);
bool QueryPerformanceFrequency(LARGE_INTEGER *li);
void Sleep(int64_t msec);

#endif  /* __HELPER_H__ */
