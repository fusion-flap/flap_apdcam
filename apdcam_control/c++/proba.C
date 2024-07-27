#include <thread>
#include <string>
#include <string.h>
#include <iostream>
#include <bit>
#include <stdint.h>
#include <tuple>
#include <deque>
//#include "error.h"
//#include "ring_buffer.h"
//#include "safe_semaphore.h"
#include <string.h>
using namespace std;
//using namespace apdcam10g;

class A
{
public:
    A() { cerr<<"A default ctor"<<endl; }
    A(const A &rhs) { cerr<<"A copy ctor"<<endl; }
};

class B
{
public:
    A a;
    B() { cerr<<"B default ctor"<<endl; }
    B(const B &rhs) { cerr<<"B copy ctor"<<endl; }
};


int main()
{
    B b1;
    cerr<<"---------"<<endl;
    B b2(b1);

    return 0;
}
