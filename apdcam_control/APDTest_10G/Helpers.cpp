#include "Helpers.h"

#if 0
bool IsHexDigit(_TCHAR c)
{
	if (_TCHAR('0') <= c && c <= _TCHAR('9')) return true;
	if (_TCHAR('a') <= c && c <= _TCHAR('f')) return true;
	if (_TCHAR('A') <= c && c <= _TCHAR('F')) return true;
	return false;
}

unsigned int GetValue(_TCHAR c)
{
	if (_TCHAR('0') <= c && c <= _TCHAR('9')) return c - _TCHAR('0');
	if (_TCHAR('a') <= c && c <= _TCHAR('f')) return c - _TCHAR('a') + 10;
	if (_TCHAR('A') <= c && c <= _TCHAR('F')) return c - _TCHAR('A') + 10;
	return 0;
}

UINT32 hstoul(_TCHAR *hs)
{
	if (_tcslen(hs) > 8) return 0xFFFFFFFF;

	UINT32 ul = 0;
	while (IsHexDigit(*hs))
	{
		ul = 16*ul + GetValue(*hs);
		hs++;
	}
	return ul;
}
#endif

// Returns the bit position of n-th 1. Eg: 0 for (01101001, 0), 3 for (01101001, 1) & 5 for (01101001, 2) 
int GetBitPosition(unsigned char uc, int n)
{
	int c = -1;
	for (int i = 0; i < 8; ++i)
	{
		if ((uc & 0x01))
			++c;
		uc = uc >> 1;
		if (c == n)
			return i;
	}
	return -1;
}

unsigned int GetBitCount(uint64_t uc)
{
	int count = 0;
	for (unsigned int i = 0; i < sizeof(uc) * 8; ++i)
	{
		if ((uc & 0x01))
			++count;
		uc = uc >> 1;
	}
	return count;
}


/*
 * Returns the number of bytes in a sample
 */
unsigned int GetBlockSize(int channels, int bitsPerSample, int *pPaddingBits)
{
	// Calculates sample block size
	int sampleBits = channels * bitsPerSample;
	int paddingBits = (8 - (bitsPerSample % 8)) % 8;

	if (pPaddingBits)
		*pPaddingBits = paddingBits;
	sampleBits += paddingBits;

	return sampleBits / 8;
}

bool Filter_6(const char *filter_str, const char *match_str)
{
	if (filter_str == NULL || match_str == NULL)
		return true;

	for (int i = 0; i < 6; ++i)
	{
		if (*filter_str == '*')
			return true;

		if (*filter_str != *match_str)
			return false;
		filter_str++;
		match_str++;
	}

	return true;
}
