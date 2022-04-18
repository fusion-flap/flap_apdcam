#pragma once
#ifndef __CAMCLIENT_H__

#define __CAMCLIENT_H__

#include "GECClient.h"

class CCamClient : public CGECClient
{
public:
	CCamClient() {};
private:
	virtual void OnAck(unsigned char *buffer, int length, void *userData);
	virtual void OnFlashData(unsigned char *buffer, int length, void *userData);
	virtual void OnPdiData(unsigned char *buffer, int length, void *userData);
	virtual void OnSocketClosed(void *userData);
	virtual void OnReceiveError(void *userData);
};

#endif  /* __CAMCLIENT_H__ */
