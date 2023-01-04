#include <sys/time.h>

class TimeMeasurement
{
public:
	TimeMeasurement();
	void add(struct timeval t);
	int counter;
	int len;
	struct timeval times[1000];
};



