#pragma once
#ifndef __LOWLEVELFUNCTIONS_H__

#define __LOWLEVELFUNCTIONS_H__

#include "CamClient.h"

bool WritePDI(CAPDClient *client, unsigned char address, UINT32 subaddress, unsigned char* buffer, int noofbytes, UINT32 ip_address_h = 0, UINT16 ip_port_h = 0, int timeout = 5000);
bool ReadPDI(CAPDClient *client, unsigned char address, UINT32 subaddress, unsigned char* buffer, int noofbytes, UINT32 ip_address_h = 0, UINT16 ip_port_h = 0, int timeout = 5000);
bool ReadCC(CAPDClient *client, UINT16 acktype, unsigned char *buffer, UINT32 ip_address_h = 0, UINT16 ip_port_h = 0, int timeout = 5000); //10G
bool ReadFlashPage(CAPDClient *client, UINT16 PgAddress, unsigned char *buffer, UINT32 ip_address_h = 0, UINT16 ip_port_h = 0, int timeout = 5000); //10G
bool StartFUP(CAPDClient * client, unsigned char * date, unsigned char * buffer, UINT32 ip_address_h = 0, UINT16 ip_port_h = 0, int timeout = 5000); // 10G

#if 0
bool SetupTS(CAPDClient *client, unsigned char channel, int packetSize, UINT16 port_h);
bool SetupAllTS(CAPDClient *client, int packetsize_1, int packetsize_2, int packetsize_3, int packetsize_4, 
				 UINT16 port_h_1 = 57000, UINT16 port_h_2 = 57001, UINT16 port_h_3 = 57002, UINT16 port_h_4 = 57003);
bool ShutupTS(CAPDClient *client, unsigned char channel);
bool ShutupAllTS(CAPDClient *client);
bool SetIP(CAPDClient *client, UINT32 ip_h);
#endif
bool CCControl(CAPDClient *client, int opcode, int length = 0, unsigned char *buffer = 0); //10G

#endif  /* __LOWLEVELFUNCTIONS_H__ */
