#include <arpa/inet.h>
#include <string.h>
#include <time.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#include "helper.h"
#include "APDLib.h"

ADT_HANDLE handle;

int main(int argc, char *argv[])
{
	UINT32 table = 0;
	int nelems = 0;

	fprintf(stderr, "short: %d\nint: %d\nlong: %d\nlong long: %d\n", sizeof(short), sizeof(int), sizeof(long), sizeof(long long));

	APDCAM_Init();

	APDCAM_Find(ntohl(inet_addr("10.123.13.102")), ntohl(inet_addr("10.123.13.102")), &table, 1, &nelems, "*", 5000);

	if (nelems == 0)
	{
		fprintf(stderr, "===No board found===\n");
	}
	else
	{
//		fprintf(stderr, "===Found %d board===\n", nelems);
#if 1
		 handle = APDCAM_Open(table);
		if (handle == 0)
		{
			fprintf(stderr, "===Cannot open camera===\n");
		}
		else
		{
			int basicPLLmul = 20;
			int basicPLLdiv_0  = 40;
			int basicPLLdiv_1  = 40;

			int clkSrc = 0;
			int extDCMmul = -1;
			int extDCMdiv = -1;

			int res;
			if ((res = APDCAM_SetTiming(handle, basicPLLmul, basicPLLdiv_0, basicPLLdiv_1, clkSrc, extDCMmul, extDCMdiv)) != ADT_OK)
			{
				fprintf(stderr, "===Cannot set timing: %d===\n", res);
			}

			int sampleDiv = 5;
			int sampleSrc = 0;
			if ((res = APDCAM_Sampling(handle, sampleDiv, sampleSrc)) != ADT_OK)
			{
				fprintf(stderr, "===Cannot set sampling: %d===\n", res);
			}

			int sampleCount = 2000000;
			int bits = 12;
			int channelMask_1 = 255;
			int channelMask_2 = 255;
			int channelMask_3 = 255;
			int channelMask_4 = 255;
			int primaryBufferSize = 62;
			if ((res = APDCAM_Allocate(handle, sampleCount, bits, channelMask_1, channelMask_2, channelMask_3, channelMask_4, primaryBufferSize)) != ADT_OK)
			{
				fprintf(stderr, "===Cannot allocate memory: %d===\n", res);
			}
			unsigned char buffer[4];
			buffer[0]=6;
			buffer[1]=6;
			buffer[2]=6;
			buffer[3]=6;

			if ((res = APDCAM_WritePDI(handle, 1, 32, buffer, 4)) != ADT_OK)
			{
				fprintf(stderr, "===Cannot write test pattern! %d===\n", res);
			}
			ADT_MEASUREMENT_MODE measurementMode = MM_ONE_SHOT;
			//sampleCount = 100000;
			ADT_CALIB_MODE calibrationMode = CM_NONCALIBRATED;
			int signalFrequency = 100;
			if ((res = APDCAM_ARM(handle, measurementMode, sampleCount, calibrationMode, signalFrequency)) != ADT_OK)
			{
				fprintf(stderr, "===Cannot arm: %d===\n", res);
			}

			if ((res = APDCAM_Start(handle)) != ADT_OK)
			{
				fprintf(stderr, "===Cannot start: %d===\n", res);
			}

			int timeout = 60000;
			if ((res = APDCAM_Wait(handle, timeout)) != ADT_OK)
			{
				fprintf(stderr, "===Cannot wait: %d===\n", res);
			}

			if ((res = Save(handle, sampleCount)) != ADT_OK)
			{
				fprintf(stderr, "===Cannot save: %d===\n", res);
			}

			APDCAM_Close(handle);
		}
#endif
	}

	APDCAM_Done();
	return 0;
}
