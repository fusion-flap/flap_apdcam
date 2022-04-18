#include <arpa/inet.h>
#include <string.h>
#include <time.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/time.h>
#include <unistd.h>

#include "helper.h"
#include "APDLib.h"

#define ADC 8
#define PC 2
#define NUM 100
#define SIZE 64

int main(int argc, char *argv[])
{
    UINT32 table = 0;
    int nelems = 0;
	int c = 0;
	//unsigned char address; 
	unsigned char buffer[256]; 
	//UINT32 subaddress;
	//int length;

    // readPDI board address length
    /*if (argc < 4) 
	{
		fprintf(stderr,"Bad arguments. readPDI board address length\n");
		exit(1);
	}
	
	address = (unsigned char)atoi(argv[1]);
	subaddress = (UINT32)atoi(argv[2]);
	length = atoi(argv[3]);*/

    APDCAM_Init();
	//sleep(1);

	_tprintf(TEXT("UInit OK\n"));
	fprintf(stdout,"Init OK\n");

	APDCAM_Find(ntohl(inet_addr("10.123.13.102")), ntohl(inet_addr("10.123.13.102")), &table, 1, &nelems, "*", 5000);
    
    /*if (nelems == 0)
    {
		fprintf(stderr, "APDCAM not found\n");
		exit(1);
    }*/
        
    ADT_HANDLE handle = APDCAM_Open(table);
        
    if (handle == 0)
    {
        fprintf(stderr, "Cannot open camera.\n");
		exit(1);
    }
	
	fprintf(stdout,"APDCAM found.\n");
	
	//Read test
	
	unsigned char temp[256], t2[256];
	APDCAM_ReadPDI(handle, PC, 512, temp, 256);
	
	for(int i = 0; i < 100; i++)
	{
		temp[0] = i;
		APDCAM_WritePDI(handle, ADC, 112, temp, 1);
		APDCAM_ReadPDI(handle, PC, 112, buffer, 1);
		APDCAM_ReadPDI(handle, ADC, 112, t2, 1);
		
			if(buffer[0] == t2[0])
			{
				printf("%d, %d\n", buffer[0], t2[0]);
				c++;
			}
		
	}
	
	/* Write-Read Test
	
	unsigned char toWrite[64];
	
	for(int i = 0; i < 1000; i++)
	{
		for(int k = 0; k < 16; k++)
		{
			toWrite[k] = i;
		}
		APDCAM_WritePDI(handle, 8, 112, toWrite, 16 );
		//sleep(1);
		APDCAM_ReadPDI(handle, 8, 112, buffer, 16 );
		//printf("Written val.: %d, %d, Read Buffer: %d, %d\n", toWrite[0], toWrite[63], buffer[0], buffer[63]);
		
		for(int k = 0; k < 16; k++)
		{
			if(buffer[k] != toWrite[k])
			{
				printf("%d != %d\n", buffer[k], toWrite[k]);
				c++;
			}
		}
		
	}*/
	
	
	printf("Errors: %d", c);
	
	/*fprintf(stdout,"Data out (%d): ",length);
	
	for (int i=0; i<length; i++)
	{
		fprintf(stdout,"%d ",buffer[i]);
	}*/
	
	fprintf(stdout,"\n");	
	APDCAM_Close(handle);
	return 0;
}

