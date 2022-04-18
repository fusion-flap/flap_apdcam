#include <stdio.h>

#include "GECClient.h"

void CGECClient::OnNetworkEvent(int &clientSocket)
{
	unsigned char recBuffer[2000];
	sockaddr from;
	socklen_t fromlen = sizeof(from);

	//(Ack = 534 byte)
	int bytes_received = recvfrom(clientSocket, (char*)recBuffer, 2000, 0, &from, &fromlen);
	if (bytes_received == 0)
	{
fprintf(stderr, "Socket Closed\n");
		OnSocketClosed(m_userData);
	}
	else if (bytes_received == -1)
	{
		int lerrno = errno;
		fprintf(stderr, "Cannot recvfrom: %s\n", strerror(lerrno));
		OnReceiveError(m_userData);
	}
	else
	{
		OnDataArrived(recBuffer, bytes_received, m_userData);
	}

	m_userData = 0;
}


void CGECClient::OnBeforeSend(int clientSocket, unsigned char *buffer, int length, sockaddr_in &sockAddr, void *userData)
{
}


void CGECClient::OnAfterSend(int /*clientSocket*/, unsigned char *buffer, int length, void *userData)
{

	if (GetLastError() == 0)
	{ // Succesfull sent
		DDTOIPHEADER *pDDTOIPHeader = reinterpret_cast<DDTOIPHEADER*>(buffer);

		bool waitReply = false;
		INSTRUCTIONHEADER *pInstructionHeader = reinterpret_cast<INSTRUCTIONHEADER*>(pDDTOIPHeader +1);
		int len = (unsigned int)length - sizeof(DDTOIPHEADER);

		while (len > 0)
		{
			UINT16 opCode = pInstructionHeader->GetOpCode();

			unsigned int instructionLength = (unsigned int)pInstructionHeader->GetInstructionLength();

			if (CReplyCmdSet::In(opCode)) {
				waitReply = true;
			}

			pInstructionHeader = (INSTRUCTIONHEADER*)((unsigned char*)pInstructionHeader + instructionLength);
			len = len - instructionLength;
		}

		if (!waitReply) 
		{
			if (userData != 0)
			{
				CLIENTCONTEXT *pClientContext = (CLIENTCONTEXT*)userData;
				if (pClientContext->hEvent != NULL)
					pClientContext->hEvent->Set();
			}
			return;
		}
		m_userData = userData;
		// The incomming data will be received in the OnNetworkEvent method (due to the non-blocking socket handling).

/*
// In the case of blocking socket, receive data here.

		unsigned char recBuffer[2000];
		sockaddr from;
		int fromlen = sizeof(from);
		//(Ack = 534 byte)
		int bytes_received = recvfrom(clientSocket, (char*)recBuffer, 2000, 0, &from, &fromlen);
		if (bytes_received == 0)
		{
			OnSocketClosed(userData);
		}
		else if (bytes_received == SOCKET_ERROR)
		{
			OnReceiveError(userData);
		}
		else
		{
			OnDataArrived(recBuffer, bytes_received, userData);
		}
*/
	}
	else
	{
	}
}


void CGECClient::OnDataArrived(unsigned char *buffer, int length, void *userData)
{
	GENERAL_MESSAGE *pMessage = (GENERAL_MESSAGE*)buffer;
	if (pMessage->Validate())
	{
		int answerCode = pMessage->GetOpCode();
		unsigned int dataLength = pMessage->GetDataLength();

		if (dataLength == length - sizeof(GENERAL_MESSAGE))
		{
			unsigned char *pData = buffer + sizeof(GENERAL_MESSAGE);
	//	for (int i=0;i<dataLength;i++) {
	//  		printf("%d ",pData[i]);
	//	}   
			switch (answerCode)
			{
			case AN_ACK:
				{
					OnAck(pData, dataLength, userData);
				}
				break;
			case AN_PDIDATA:
				{
					OnPdiData(pData, dataLength, userData);
				}
				break;
			case AN_FLASHPAGE:
				{
					OnFlashData(pData, dataLength, userData);
				}
				break;		
			default:
				{
					OnError(buffer, length, userData);
				}
				break;
			}
		}
		else
		{
			OnError(buffer, length, userData);
		}
	}
	else
	{
fprintf(stderr, "Invalid msg\n");
		OnError(buffer, length, userData);
	}
}

void CGECClient::OnSocketClosed(void* /*userData*/)
{
}

void CGECClient::OnReceiveError(void* /*userData*/) 
{
}
