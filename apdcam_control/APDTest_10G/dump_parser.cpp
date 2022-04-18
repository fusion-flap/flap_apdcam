#include <errno.h>
#include <stdio.h>
#include <string.h>

#define FAST_COUNTER
#define CC_SERIAL 0x04030201
#include "GECCommands.h"


#pragma pack(push)
#pragma pack(1)
union BIG
{
	uint16_t flat;
	struct
	{
		unsigned int sample_start_condition : 1;
		unsigned int udp_test_mode : 1;
		unsigned int reserved : 12;
		unsigned int stream_num : 2;
	};
};

union LITTLE
{
	uint16_t flat;
	struct
	{
		unsigned int reserved : 6;
		unsigned int stream_num : 2;
		unsigned int sample_start_condition : 1;
		unsigned int udp_test_mode : 1;
//		unsigned int reserved : 6;
	};
};
union S1_H
{
	uint8_t flat;
	struct
	{
		unsigned int reserved : 6;
		unsigned int stream_num : 2;
	};
};
union S1_L
{
	uint8_t flat;
	struct
	{
		unsigned int sample_start_condition : 1;
		unsigned int udp_test_mode : 1;
		unsigned int reserved : 6;
	};
};
#pragma pack(pop)

int main(int argc, char* argv[])
{
	FILE *dump = fopen(argv[1], "rb");

	if (dump == NULL)
	{
		fprintf(stderr, "Cannot open %s: %s\n", argv[1], strerror(errno));
	}

	uint8_t packet[8 * 1024 * 1024];
	size_t pack_size;
	pack_size = fread(packet, 1, sizeof(packet), dump);
	uint8_t *p_start = packet;

	uint64_t lastPacket = 0;
	uint64_t lastSample = 0;
	uint8_t *lastp_start = p_start;
	uint64_t packetsLost = 0;
	uint64_t nPackets = 0;
	uint64_t consecutiveLosts = 0;
	while (pack_size > sizeof(CC_STREAMHEADER::serial))
	{
		CC_STREAMHEADER *header = reinterpret_cast<CC_STREAMHEADER*>(p_start);
		if (header->serial == CC_SERIAL)
		{
			uint64_t packetCounter = CC_PACKETCOUNTER(header);
			uint64_t sampleCounter = CC_SAMPLECOUNTER(header);

			if (lastPacket == 0)
			{
				lastPacket = packetCounter;
				if (packetCounter != 1)
				{
					packetsLost = packetCounter - 1;
					fprintf(stderr, "Packet Continuity error (exp. 1 got %" PRIu64 ")\n", packetCounter);
				}
			}
			else
				++lastPacket;

			++nPackets;

			if (lastSample == 0)
			{
				lastSample = sampleCounter;
			}
			else
			{
				fprintf(stdout, "Packet size: %ld\n", p_start - lastp_start);
				fprintf(stdout, "Data size: %ld\n", p_start - lastp_start - sizeof(CC_STREAMHEADER));
				fprintf(stdout, "\n");
				lastp_start = p_start;
			}

			fprintf(stdout, "CC_HEADER:\nSerial:\t0x%.4x\nStream:\t%d\nRes:\t%d\nTest:\t%d\nSScond:\t%d\n"
					"BPLL:\t%d\nRes:\t%d\nEDCM:\t%d\nEClk:\t%d\nCTStat:\t%d\nStream:\t%d\nOvrld:\t%d\n"
					"PCount:\t%" PRIu64 "\nSCount:\t%" PRIu64 "\n",
					ntohl(header->serial),
					header->S1.Stream_num + 1,
					header->S1.Reserved,
					header->S1.UDP_Test_Mode,
					header->S1.Sample_Start_Condition,
					header->S2.FPGA_Status.Basic_PLL_Locked,
					header->S2.FPGA_Status.Reserved,
					header->S2.FPGA_Status.EDCM_Locked,
					header->S2.FPGA_Status.Ext_Clock_Valid,
					header->S2.FPGA_Status.CAM_Timer_State,
					header->S2.FPGA_Status.Streaming_Data,
					header->S2.FPGA_Status.Overload,
					packetCounter,
					sampleCounter);

			if (lastPacket != packetCounter)
			{
				++consecutiveLosts;
				fprintf(stderr, "Packet Continuity error (exp. %" PRIu64 " got %" PRIu64 ")\n", lastPacket, packetCounter);
				fprintf(stdout, ">>>Packet Continuity error (exp. %" PRIu64 " got %" PRIu64 "), lost %" PRIu64 " packets, %" PRIu64 " consecutive packet losses<<<\n", lastPacket, packetCounter, packetCounter - lastPacket, consecutiveLosts);
				packetsLost += packetCounter - lastPacket;
				lastPacket = packetCounter;
			}
			else
			{
				consecutiveLosts = 0;
#if 0
				if (sampleCounter > lastSample && header->S1.Sample_Start_Condition == 0)
				{
					if (sampleCounter == lastSample + 1)
					{
						fprintf(stderr, "FIXABLE ");
						fprintf(stdout, ">>>FIXABLE ");
					}
					else
					{
						fprintf(stderr, "NON-FIXABLE ");
						fprintf(stdout, ">>>NON-FIXABLE ");
					}
					fprintf(stderr, "Incorrect sample counter assignment\n");
					fprintf(stdout, "Incorrect sample counter assignment<<<\n");
				}
#endif
			}
			lastSample = sampleCounter;
			if (header->S1.Reserved != 0)
				fprintf(stderr, "S1.Reserved is not ZERO but %d\n", header->S1.Reserved);
			if (header->S1.UDP_Test_Mode != 0)
				fprintf(stderr, "S1.UDP_Test_Mode is not ZERO\n");

			p_start += sizeof(CC_STREAMHEADER);
			pack_size -= sizeof(CC_STREAMHEADER);
		}
		else
		{
			fprintf(stdout, "%.2X %.2X %.2X %.2X %.2X %.2X %.2X %.2X\n", p_start[0], p_start[1], p_start[2], p_start[3], p_start[4], p_start[5], p_start[6], p_start[7]);
			p_start += 8;
			pack_size -= 8;
		}
	}
	fprintf(stdout, "\nReceived %" PRIu64 " packets\nReceived %" PRIu64 " samples\n", nPackets, lastSample);
	if (packetsLost)
	{
		fprintf(stderr, "Lost %" PRIu64 " packets!!!\n", packetsLost);
		fprintf(stdout, "Lost %" PRIu64 " packets!!!\n", packetsLost);
	}

	fclose(dump);
}
