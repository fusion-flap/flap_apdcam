#include "daq.h"
#include <iostream>
#include <string>
#include <thread>
#include <vector>
#include <unistd.h>
#include <stdlib.h>
#include <signal.h>

using namespace apdcam10g;
using namespace std;

void help(const daq &s)
{
    cout<<"Usage: apdcam-data-recorder [options]"<<endl<<endl;
    cout<<"  -i <interface>                   Set the network interface. Defaults to 'lo'"<<endl;
    cout<<"  -s|--sample-buffer <interface>   Set the sample buffer size. Defaults to "<<s.sample_buffer_size()<<endl;
    cout<<"  -n|--network-buffer <interface>  Set the network ring buffer size in terms of UDP packets. Defaults to "<<s.network_buffer_size()<<endl;
    cout<<endl;
    cout<<"Upon starting it will create a file 'settings.json' that can be read by the fake camera using the -s command line argument"<<endl;
    exit(0);
}

daq the_daq;


void flush_output(int sig)
{
    cerr<<"Flushing outputs.."<<endl;
    std::this_thread::sleep_for(1s);
    the_daq.flush();
    cerr<<"DONE"<<endl;
    std::this_thread::sleep_for(1s);
    signal (sig, SIG_DFL);
    raise (sig);
}

int main(int argc, char *argv[])
try
{

    string ld_library_path = getenv("LD_LIBRARY_PATH");
    ld_library_path += ":..";
    setenv("LD_LIBRARY_PATH",ld_library_path.c_str(),1);

    signal(SIGINT,flush_output);

    for(unsigned int opt=1; opt<argc; ++opt)
    {
        if(!strcmp(argv[opt],"-h") || !strcmp(argv[opt],"--help")) help(the_daq);
        else if(!strcmp(argv[opt],"-i"))
        {
            if(opt+1>=argc) APDCAM_ERROR("Missing argument (interface) after -i");
            the_daq.interface(argv[++opt]);
        }
        else if(!strcmp(argv[opt],"-s") || !strcmp(argv[opt],"--sample-buffer"))
        {
            if(opt+1>=argc) APDCAM_ERROR(std::string("Missing argument (buffer size) after ") + argv[opt]);
            the_daq.sample_buffer_size(atoi(argv[++opt]));
        }
        else if(!strcmp(argv[opt],"-n") || !strcmp(argv[opt],"--network-buffer"))
        {
            if(opt+1>=argc) APDCAM_ERROR(std::string("Missing argument (buffer size) after ") + argv[opt]);
            the_daq.network_buffer_size(atoi(argv[++opt]));
        }
        else APDCAM_ERROR(std::string("Bad argument: ") + argv[opt]);
    }

    the_daq.get_net_parameters();
    the_daq.initialize(false,{{
                {true,true,true,false,false,false,false,false},
                {true,true,true,false,false,false,false,false},
                {true,true,true,false,false,false,false,false},
                {true,true,true,false,false,false,false,false}
            }}, {14}, v1);
    the_daq.write("settings.json");

//    the_daq.print_channel_map();

    cerr<<"Starting..."<<endl;
    the_daq.start(true);

    return 0;
}
catch(apdcam10g::error &e)
{
    cerr<<e.full_message()<<endl;
}
