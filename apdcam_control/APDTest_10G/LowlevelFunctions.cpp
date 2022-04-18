#include <stdio.h>

#include "GECCommands.h"
#include "LowlevelFunctions.h"
#include "helper.h"

#define MAX_WRITE_SIZE 256

bool WritePDI(CAPDClient *client, unsigned char address, UINT32 subaddress, unsigned char* buffer, int noofbytes, UINT32 ip_address_h, UINT16 ip_port_h, int timeout)
{
	bool res = true;

	CAPDFactory *factory = CAPDFactory::GetAPDFactory();
	CClientContext *clientContext = factory->GetClientContext();
	CEvent *event = factory->GetEvent();
	clientContext->pEvent = event;
	CWaitForEvents *wait = factory->GetWaitForEvents();
	wait->Add(event);

	unsigned char rbuffer[32] = {0};
	clientContext->bufferLength = 32;
	clientContext->pBuffer = rbuffer;

	do
	{
		int sendlen = MIN(MAX_WRITE_SIZE, noofbytes);
		WRITEPDI cmdw;
		cmdw.instruction.Prepare(address, subaddress, buffer, (int)sendlen);

		READPDI cmdr;
		cmdr.instruction.Prepare(address, subaddress, (UINT16)MIN(sendlen, 32));

		BULKCMD cmd;
		cmd.Add(cmdw);
		cmd.Add(cmdr);

		clientContext->pEvent->Reset();
		client->SendData(&cmd, clientContext, ip_address_h, ip_port_h);

		if (wait->WaitAll(timeout) != CWaitForEvents::WR_OK)
		{
			res = false;
		}

		noofbytes -= sendlen;
		buffer += sendlen;
		subaddress += sendlen;
		Sleep(20);
	} while (noofbytes > 0 && res);

	delete wait;
	delete event;
	delete clientContext;

	return res;
}

bool ReadPDI(CAPDClient *client, unsigned char address, UINT32 subaddress, unsigned char* buffer, int noofbytes, UINT32 ip_address_h, UINT16 ip_port_h, int timeout)
{
	bool res = true;

	CAPDFactory *factory = CAPDFactory::GetAPDFactory();
	CClientContext *clientContext = factory->GetClientContext();
	CEvent *event = factory->GetEvent();
	clientContext->pEvent = event;
	CWaitForEvents *wait = factory->GetWaitForEvents();
	wait->Add(event);

	clientContext->bufferLength = noofbytes;
	clientContext->pBuffer = buffer;

	READPDI cmdr;
	cmdr.instruction.Prepare(address, subaddress, (UINT16)noofbytes);

	client->SendData(&cmdr, clientContext, ip_address_h, ip_port_h);
	switch (wait->WaitAll(timeout))
	{
		case CWaitForEvents::WR_TIMEOUT:
			fprintf(stderr, "ReadPDI() timed out!\n");
			res = false;
			break;
		case CWaitForEvents::WR_ERROR:
			fprintf(stderr, "ReadPDI(): WaitAll() error: %s\n", strerror(wait->GetError()));
			res = false;
			break;
		default:
			break;
	}

	delete wait;
	delete event;
	delete clientContext;

	return res;
}

bool ReadCC(CAPDClient *client, UINT16 acktype, unsigned char *buffer, UINT32 ip_address_h, UINT16 ip_port_h, int timeout)
{
	bool res = true;

	CAPDFactory *factory = CAPDFactory::GetAPDFactory();
	CClientContext *clientContext = factory->GetClientContext();
	CEvent *event = factory->GetEvent();
	clientContext->pEvent = event;
	CWaitForEvents *wait = factory->GetWaitForEvents();
	wait->Add(event);

	clientContext->bufferLength = 768;
	clientContext->pBuffer = buffer;

	SENDACK cmdr;
	cmdr.instruction.Prepare(acktype);

	client->SendData(&cmdr, clientContext, ip_address_h, ip_port_h);
	if (wait->WaitAll(timeout) != CWaitForEvents::WR_OK)
	{
		res = false;
	}

	delete wait;
	delete event;
	delete clientContext;

	return res;
}

bool ReadFlashPage(CAPDClient *client, UINT16 PgAddress, unsigned char *buffer, UINT32 ip_address_h, UINT16 ip_port_h, int timeout)
{
	bool res = true;

	CAPDFactory *factory = CAPDFactory::GetAPDFactory();
	CClientContext *clientContext = factory->GetClientContext();
	CEvent *event = factory->GetEvent();
	clientContext->pEvent = event;
	CWaitForEvents *wait = factory->GetWaitForEvents();
	wait->Add(event);

	clientContext->bufferLength = 1030;
	clientContext->pBuffer = buffer;

	FLREAD cmdr;
	cmdr.instruction.Prepare(PgAddress);

	client->SendData(&cmdr, clientContext, ip_address_h, ip_port_h);
	if (wait->WaitAll(timeout) != CWaitForEvents::WR_OK)
	{
		res = false;
	}

	delete wait;
	delete event;
	delete clientContext;
        

	return res;
}

bool StartFUP(CAPDClient *client, unsigned char * date, unsigned char *buffer, UINT32 ip_address_h, UINT16 ip_port_h, int timeout)
{
	bool res = true;

	CAPDFactory *factory = CAPDFactory::GetAPDFactory();
	CClientContext *clientContext = factory->GetClientContext();
	CEvent *event = factory->GetEvent();
	clientContext->pEvent = event;
	CWaitForEvents *wait = factory->GetWaitForEvents();
	wait->Add(event);

	clientContext->bufferLength = 20;
	clientContext->pBuffer = buffer;

	STARTFUP cmdr;
	cmdr.instruction.Prepare(date);
	unsigned char * bbb;
	bbb = (unsigned char *)&cmdr;
	client->SendData(&cmdr, clientContext, ip_address_h, ip_port_h);
	if (wait->WaitAll(timeout) != CWaitForEvents::WR_OK)
	{
		res = false;
	}

	delete wait;
	delete event;
	delete clientContext;
        

	return res;
}

#if 0
bool SetupTS(CAPDClient *client, unsigned char channel, int packetSize, UINT16 port_h)
{
	bool res = true;

	CAPDFactory *factory = CAPDFactory::GetAPDFactory();
	CClientContext *clientContext = factory->GetClientContext();
	CEvent *event = factory->GetEvent();
	clientContext->pEvent = event;
	CWaitForEvents *wait = factory->GetWaitForEvents();
	wait->Add(event);

	SENDTS cmd_sendTS;
	cmd_sendTS.instruction.Prepare(channel, packetSize, port_h);

	client->SendData(&cmd_sendTS, clientContext);

	if (wait->WaitAll(5000) != CWaitForEvents::WR_OK)
	{
		res = false;
	}

	delete wait;
	delete event;
	delete clientContext;

	return res;
}

bool SetupAllTS(CAPDClient *client, int packetsize_1, int packetsize_2, int packetsize_3, int packetsize_4, UINT16 port_h_1, UINT16 port_h_2, UINT16 port_h_3, UINT16 port_h_4)
{
	bool res = true;

	CAPDFactory *factory = CAPDFactory::GetAPDFactory();
	CClientContext *clientContext = factory->GetClientContext();
	CEvent *event = factory->GetEvent();
	clientContext->pEvent = event;
	CWaitForEvents *wait = factory->GetWaitForEvents();
	wait->Add(event);

	SENDTS cmd_sendTS0;
	cmd_sendTS0.instruction.Prepare(1, packetsize_1, port_h_1);
	SENDTS cmd_sendTS1;
	cmd_sendTS1.instruction.Prepare(2, packetsize_2, port_h_2);
	SENDTS cmd_sendTS2;
	cmd_sendTS2.instruction.Prepare(3, packetsize_3, port_h_3);
	SENDTS cmd_sendTS3;
	cmd_sendTS3.instruction.Prepare(4, packetsize_4, port_h_4);

	BULKCMD cmd;
	cmd.Add(cmd_sendTS0);
	cmd.Add(cmd_sendTS1);
	cmd.Add(cmd_sendTS2);
	cmd.Add(cmd_sendTS3);

	client->SendData(&cmd, clientContext);

	if (wait->WaitAll(5000) != CWaitForEvents::WR_OK)
	{
		res = false;
	}

	delete wait;
	delete event;
	delete clientContext;

	return res;
}

bool ShutupTS(CAPDClient *client, unsigned char channel)
{
	bool res = true;

	CAPDFactory *factory = CAPDFactory::GetAPDFactory();
	CClientContext *clientContext = factory->GetClientContext();
	CEvent *event = factory->GetEvent();
	clientContext->pEvent = event;
	CWaitForEvents *wait = factory->GetWaitForEvents();
	wait->Add(event);

	DONTSENDTS cmd_dontsendTS;
	cmd_dontsendTS.instruction.Prepare(channel);

	client->SendData(&cmd_dontsendTS, clientContext);

	if (wait->WaitAll(5000) != CWaitForEvents::WR_OK)
	{
		res = false;
	}

	delete wait;
	delete event;
	delete clientContext;

	return res;
}


bool ShutupAllTS(CAPDClient *client)
{
	bool res = true;

	CAPDFactory *factory = CAPDFactory::GetAPDFactory();
	CClientContext *clientContext = factory->GetClientContext();
	CEvent *event = factory->GetEvent();
	clientContext->pEvent = event;
	CWaitForEvents *wait = factory->GetWaitForEvents();
	wait->Add(event);

	BULKCMD cmd;
	for (int channel = 1; channel <=4; channel++)
	{
		DONTSENDTS cmd_dontsendTS;
		cmd_dontsendTS.instruction.Prepare(channel);
		cmd.Add(cmd_dontsendTS);
	}

	client->SendData(&cmd, clientContext);

	if (wait->WaitAll(5000) != CWaitForEvents::WR_OK)
	{
		res = false;
	}

	delete wait;
	delete event;
	delete clientContext;

	return res;
}
#endif

bool SetIP(CAPDClient *client, UINT32 ip_h)
{
	bool res = true;

	CAPDFactory *factory = CAPDFactory::GetAPDFactory();
	CClientContext *clientContext = factory->GetClientContext();
	CEvent *event = factory->GetEvent();
	clientContext->pEvent = event;
	CWaitForEvents *wait = factory->GetWaitForEvents();
	wait->Add(event);

	SETIP cmd;
	cmd.instruction.Prepare(ip_h);
/*
	unsigned char *p = (unsigned char *)&cmd;
	for (int i = 0; i < 48; i++)
	{
		if ((i % 16) == 0) printf("\n");
		printf("%02X ", *p);
		p++;
	}
*/
	client->SendData(&cmd, clientContext);

	if (wait->WaitAll(5000) != CWaitForEvents::WR_OK)
	{
		res = false;
	}

	delete wait;
	delete event;
	delete clientContext;

	return res;
}

bool CCControl(CAPDClient *client, int opcode, int length, unsigned char *buffer)
{
	bool res = true;

	CAPDFactory *factory = CAPDFactory::GetAPDFactory();
	CClientContext *clientContext = factory->GetClientContext();
	CEvent *event = factory->GetEvent();
	clientContext->pEvent = event;
	CWaitForEvents *wait = factory->GetWaitForEvents();
	wait->Add(event);

	unsigned char rbuffer[32] = {0};
	clientContext->bufferLength = 32;
	clientContext->pBuffer = rbuffer;

	do
	{
		CCCONTROL cmd;
		int sendlen = cmd.instruction.Prepare(opcode, length, buffer);

		clientContext->pEvent->Reset();
		client->SendData(&cmd, clientContext);

		if (wait->WaitAll(5000) != CWaitForEvents::WR_OK)
		{
			res = false;
		}

		length -= sendlen;
		buffer += sendlen;
	} while (length > 0 && res);

	delete wait;
	delete event;
	delete clientContext;

	return res;
}
