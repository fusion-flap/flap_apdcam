#include "../udp.h"
#include <string>
#include <iostream>
#include <unistd.h>

using namespace std;

int main()
{
    apdcam10g::udp_client client(10000,"192.168.8.100");
    client.blocking(true);

    string line;
    while(getline(cin,line))
    {
        cerr<<"Will send htis string to server: "<<line<<endl;
        client.send(line.c_str(),line.length());

        //sleep(1);

        char answer[5000];
        const int recvresult = client.recv(answer,5000);
        answer[recvresult] = '\0';
        cerr<<"Received answer from server: "<<answer<<endl;
    }

    cerr<<"Exiting..."<<endl;
    client.send("exit",4);

    return 0;

}
