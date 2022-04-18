//Monitoring application for APDCAM10G

#include <arpa/inet.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <unistd.h>

#include "helper.h"
#include "APDLib.h"

int main()
{
	UINT32 table[32];
    int nelems = 0;
	int res = 0;
	ADT_HANDLE g_handle;
	unsigned char temp;
	//char c;
	/*unsigned char *ack;
	ack = (unsigned char *)malloc(304);
	unsigned char dat[304];*/
	int value[1];
	
	APDCAM_Init();
	APDCAM_Find(ntohl(inet_addr("10.123.13.102")), ntohl(inet_addr("10.123.13.102")), table, 1, &nelems, (char *)"*", 5000);
	
	
	g_handle = APDCAM_Open(table[0]);
	
	if (nelems == 0)
	{
		printf("ADC Board not found.\n");
		while(1)
		{
			//10G C&C temp
			APDCAM_ReadCC(g_handle, 3, value, 276, 1);
			printf("\b");
			printf("10G C&C temperature (Celsius): %d\n", value[0]);
			Sleep(1000);
			
		}
	}
	else
	{
		while(1)
		{
			//ADC Board & 10G C&C temp
			APDCAM_ReadPDI(g_handle, 8, 0x0A, &temp, 1);
			printf("ADC Board temperature (Celsius): %d\n", temp);
			APDCAM_ReadCC(g_handle, 3, value, 276, 1);
			printf("\b");
			printf("10G C&C temperature (Celsius):   %d\n", value[0]);
			Sleep(1000);
			
		}
	}
	return res;
}
