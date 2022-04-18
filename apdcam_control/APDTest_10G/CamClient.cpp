#include <stdio.h>

#include "CamClient.h"


void CCamClient::OnAck(unsigned char *buffer, int length, void *userData) 
{
	if (userData == 0) return;

	CLIENTCONTEXT *pClientContext = (CLIENTCONTEXT*)userData;
	pClientContext->dataLength = MIN(pClientContext->bufferLength, (unsigned int)length);
	if (pClientContext->pBuffer != NULL)
	{
		memcpy(pClientContext->pBuffer, buffer, pClientContext->dataLength);
	}

	if (pClientContext->hEvent != NULL) 
	{
		pClientContext->hEvent->Set();
	}
}

void CCamClient::OnFlashData(unsigned char *buffer, int length, void *userData) 
{

	if (userData == 0) return;


	CLIENTCONTEXT *pClientContext = (CLIENTCONTEXT*)userData;

	pClientContext->dataLength = MIN(pClientContext->bufferLength, (unsigned int)length);
	if (pClientContext->pBuffer != NULL)
	{
		
		fflush(stdout);
		memcpy(pClientContext->pBuffer, buffer, pClientContext->dataLength);
	}

	if (pClientContext->hEvent != NULL) 
	{
		pClientContext->hEvent->Set();
	}
}


void CCamClient::OnPdiData(unsigned char *buffer, int length, void *userData) 
{
	if (userData == 0)
		return;

	CLIENTCONTEXT *pClientContext = (CLIENTCONTEXT*)userData;

	pClientContext->dataLength = MIN(pClientContext->bufferLength, (unsigned int)length);
	if (pClientContext->pBuffer != NULL)
	{
		memcpy(pClientContext->pBuffer, buffer, pClientContext->dataLength);
	}

	if (pClientContext->hEvent != NULL) 
	{
		pClientContext->hEvent->Set();
	}
}

void CCamClient::OnSocketClosed(void *userData)
{
	CGECClient::OnSocketClosed(userData);
}

void CCamClient::OnReceiveError(void *userData)
{
	CGECClient::OnReceiveError(userData);
	if (userData == 0) return;

	CLIENTCONTEXT *pClientContext = (CLIENTCONTEXT*)userData;
	if (pClientContext->hEvent != NULL) 
	{
		pClientContext->hEvent->Set();
	}
}
