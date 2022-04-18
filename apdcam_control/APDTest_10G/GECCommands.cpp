#include "GECCommands.h"


int CReplyCmdSet::g_CmdSet[] = {OP_SENDACK, OP_READPDI, OP_FLREAD, OP_STARTFUP};

DDTOIPHEADER::DDTOIPHEADER()
{
	DDToIp[0] = 0x44;
	DDToIp[1] = 0x44;
	DDToIp[2] = 0x54;
	DDToIp[3] = 0x6F;
	DDToIp[4] = 0x49;
	DDToIp[5] = 0x50;
	memset(UserText, 0, sizeof(UserText));
	strncpy(UserText, COMPANY, sizeof(COMPANY));
	V = 3;
}

void DDTOIPHEADER::Prepare(char *_usertext)
{
	DDToIp[0] = 0x44;
	DDToIp[1] = 0x44;
	DDToIp[2] = 0x54;
	DDToIp[3] = 0x6F;
	DDToIp[4] = 0x49;
	DDToIp[5] = 0x50;
	memset(UserText, 0, sizeof(UserText));
	strncpy(UserText, _usertext, MIN(15, sizeof(UserText)));
	V = 3;
}

bool DDTOIPHEADER::Validate()
{
	return (
		DDToIp[0] == 0x44 &&
		DDToIp[1] == 0x44 &&
		DDToIp[2] == 0x54 &&
		DDToIp[3] == 0x6F &&
		DDToIp[4] == 0x49 &&
		DDToIp[5] == 0x50 &&
		V == 3);
}
