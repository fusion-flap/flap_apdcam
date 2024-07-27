#include "../udp.h"
#include <string>
#include <string.h>
#include <iostream>

using namespace std;

int main()
{
    apdcam10g::udp_server server(10000);
    server.blocking(true);

    char msg[5000];

    while(true)
    {
        const int recvresult = server.recv(msg,5000);
        if(recvresult <= 0) continue;
        msg[recvresult] = '\0';
        
        cerr<<"Message from "<<server.last_ip()<<": "<<msg<<endl;

        const std::string answer = "You sent me the message: " + std::string(msg);
        cerr<<"Sending back the answer to client: "<<answer<<endl;
        server.send(answer.c_str(),answer.length());

        if(!strncmp(msg,"exit",4)) 
        {
            cerr<<"Exiting.."<<endl;
            break;
        }
    }


    return 0;

}
