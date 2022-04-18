#pragma once
#ifndef __HELPERS_H__

#define __HELPERS_H__

#include <stdint.h>
#include <stdlib.h>

int GetBitPosition(unsigned char uc, int n);
unsigned int GetBitCount(uint64_t uc);
unsigned int GetBlockSize(int channels, int bitsPerSample, int *pPaddingBits = NULL);
bool Filter_6(const char *filter_str, const char *match_str);

#endif  /* __HELPERS_H__ */
