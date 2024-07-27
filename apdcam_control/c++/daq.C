#include <iostream>
#include <fstream>

#include "daq.h"
#include "utils.h"
#include "error.h"
#include "pstream.h"
#include "channel_signal_extractor.h"

//#include <stdio.h>
//#include <stdlib.h>
//#include <unistd.h>
//#include <string.h>
//#include <sys/types.h>
//#include <sys/socket.h>
//#include <netinet/in.h>


namespace apdcam10g
{
    using namespace std;

/*
    daq &daq::mac(const string &m)
    {
        auto ss = split(m,":");
        if(ss.size() != 6) APDCAM_ERROR("The MAC address (argument of daq::mac) must contain 6 hex numbers separated by :");
        for(int i=0; i<6; ++i) mac_[i] = (std::byte)std::stol(ss[i],0,16);
        return *this;
    }


    daq &daq::ip(const string &a)
    {
        auto ss = split(a,".");
        if(ss.size() != 4) APDCAM_ERROR("The IP address (argument of daq::ip) must contain 4 numbers separated by a dot");
        for(int i=0; i<4; ++i) ip_[i] = (std::byte)std::stol(ss[i],0,10);
        return *this;
    }
    */

    void daq::dump()
    {
/*
        cout<<"MAC: ";
        for(int i=0; i<6; ++i) 
        {
            if(i>0) cout<<":";
            cout<<hex<<(int)mac_[i]<<dec;
        }
        cout<<endl;
        cout<<"IP: ";
        for(int i=0; i<4; ++i) 
        {
            if(i>0) cout<<":";
            cout<<(int)ip_[i];
        }
*/
        cout<<endl;
        cout<<"MTU: "<<mtu_<<endl;
    }



    template <safeness S>
    daq &daq::initialize(bool dual_sata, const std::vector<std::vector<std::vector<bool>>> &channel_masks, const std::vector<unsigned int> &resolution_bits, version ver)
    {
        if(mtu_ == 0) APDCAM_ERROR("MTU has not been set");
        if(channel_masks.size() != resolution_bits.size()) APDCAM_ERROR("Masks and resolution sizes do not agree");

        channel_masks_ = channel_masks;
        resolution_bits_ = resolution_bits;

        sockets_.clear(); // delete any previously open socket, if any

        const int nof_adc = channel_masks.size();

        if(mtu_==0) APDCAM_ERROR("MTU has not yet been specified in daq::initialize");
        if(dual_sata && nof_adc>2) APDCAM_ERROR("Dual sata is set with more than two ADC boards present");

        for(auto e: extractors_) delete e;
        extractors_.resize(nof_adc);
        sockets_.resize(nof_adc);

        //network_buffers_.resize(nof_adc);

        calculate_channel_info();

        for(unsigned int i_adc=0; i_adc<nof_adc; ++i_adc)
        {
            // Open sockets
            if(dual_sata)
            {
                cerr<<"Listening on port "<<ports_[i_adc*2]<<endl;
                sockets_[i_adc].open(ports_[i_adc*2]);
            }
            else
            {
                cerr<<"Listening on port "<<ports_[i_adc*2]<<endl;
                sockets_[i_adc].open(ports_[i_adc]  );
            }

            // initialize ring buffers
            network_buffers_[i_adc].resize(network_buffer_size_*max_udp_packet_size_);

            extractors_[i_adc] = new channel_data_extractor<S>(i_adc,ver,sample_buffer_size_);
            extractors_[i_adc]->stream(this);
        }

        for(unsigned int i_adc=0; i_adc<nof_adc; ++i_adc)
        {
            cerr<<"ADC"<<i_adc<<" bytes per sample: "<<board_bytes_per_shot_[i_adc]<<endl;
        }

        return *this;
    }

    void daq::flush()
    {
      cerr<<"daq::flush is not yet implemented"<<endl;
    }


    template <safeness S>
    daq &daq::start(bool wait)
    {
        producer_threads_.clear();
        consumer_threads_.clear();

        // Start the producer (reading from the UDP sockets) threads
        if(separate_network_threads_)  // Start one thread for each socket
        {
            for(unsigned int i=0; i<sockets_.size(); ++i)
            {
                // Make the corresponding socket blocking. This thread is reading only from one socket, so
                // we can safely be blocked until data is available 
                sockets_[i].blocking(true);

                network_threads_.push_back(std::jthread( [this, i](std::stop_token stok)
                    {
                        try
                        {
                            while(!stok.stop_requested())
                            {
                                cerr<<"getting write region..."<<endl;
                                // if there is a continuous free region of 'udp_packet_size_' bytes in the buffer, receive data into it
                                auto [ptr1,size1,ptr2,size2] = network_buffers_[i].write_region(max_udp_packet_size_);
                                cerr<<"done: "<<size1<<endl;
                                if(size1==max_udp_packet_size_)
                                {
                                    // Increment the write pointer of the ring buffer only if we received an entire packet
                                    const auto received_packet_size = sockets_[i].recv<S>(ptr1,max_udp_packet_size_);
                                    cerr<<"Received packet size: "<<received_packet_size<<endl;
                                    if(received_packet_size<0) APDCAM_ERROR_ERRNO(errno);
                                    if(received_packet_size>0)
                                    {
                                        cerr<<"Incrementing write ptr..."<<endl;
                                        network_buffers_[i].increment_write_ptr(received_packet_size);
                                        cerr<<"FINISHED"<<endl;
                                    }
                                    // If a partial packet was received, we reached the end of data transfer (remainig data could not fill the packet entirely)
                                    if(received_packet_size != max_udp_packet_size_) break;
                                }
                                // else there was no room in the ring buffer, so just keep looping
                            }
                        }
                        catch(apdcam10g::error &e) { cerr<<e.full_message()<<endl; }
                    }));
            }
        }
        else
        {
            // First, make all input sockets non-blocking, because we continuously loop
            // over all of them, and if there is no data in one of them, that should not block
            // the loop from trying to read from the others
            for(unsigned int i=0; i<sockets_.size(); ++i) sockets_[i].blocking(false);

            network_threads_.push_back(std::jthread( [this](std::stop_token stok)
                {
                    try
                    {
                        while(!stok.stop_requested())
                        {
                            for(unsigned int i=0; i<sockets_.size(); ++i)
                            {
                                auto [ptr1,size1,ptr2,size2] = network_buffers_[i].write_region(max_udp_packet_size_);
                                if(size1==max_udp_packet_size_)
                                {
                                    // Increment the write pointer of the ring buffer only if we received an entire packet
                                    const auto received_packet_size = sockets_[i].recv<S>(ptr1,max_udp_packet_size_);
                                    cerr<<"Received packet: "<<received_packet_size<<endl;
                                    if(received_packet_size>0) network_buffers_[i].increment_write_ptr(received_packet_size);
                                    if(received_packet_size != max_udp_packet_size_) break;
                                }
                            }
                        }
                    }
                    catch(apdcam10g::error &e) { cerr<<e.full_message()<<endl; }
                }));
        }

        // Start the producer (reading from the UDP sockets) threads
        if(separate_extractor_threads_)  // Start one thread for each socket
        {
            for(unsigned int i_socket=0; i_socket<sockets_.size(); ++i_socket)
            {
                extractor_threads_.push_back(std::jthread( [this, i_socket](std::stop_token stok)
                    {
                        try
                        {
                            while(!stok.stop_requested()) extractors_[i_socket]->run(network_buffers_[i_socket]);
                        }
                        catch(apdcam10g::error &e) { cerr<<e.full_message()<<endl; }
                    }));
            }
        }
        else
        {
            extractor_threads_.push_back(std::jthread( [this](std::stop_token stok)
                {
                    try
                    {
                        while(!stok.stop_requested())
                        {
                            for(unsigned int i_socket=0; i_socket<sockets_.size(); ++i_socket)
                            {
                                extractors_[i_socket]->run(network_buffers_[i_socket]);
                            }
                        }
                    }
                    catch(apdcam10g::error &e) { cerr<<e.full_message()<<endl; }
                }));
        }

	// Create 
	{
	  processor_thread_ = std::jthread([this](std::stop_token stok)
					   {
					     try
					       {
						 while(!stok.stop_requested())
						   {
						     cerr<<"processor thread is not yet ipmlemented"<<endl;
						   }
					       }
					     catch(apdcam10g::error &e) { cerr<<e.full_message()<<endl; }
					   });
	}

        sleep(1);

        if(wait)
        {
            for(auto &t : network_threads_) if(t.joinable()) t.join();
            for(auto &t : extractor_threads_) if(t.joinable()) t.join();
	    if(processor_thread_.joinable()) processor_thread_.join();
        }

        return *this;
    }

    template <safeness S>
    daq &daq::stop(bool wait)
    {
        for(auto &t : producer_threads_) t.request_stop();
        for(auto &t : consumer_threads_) t.request_stop();
        if(wait)
        {
            for(auto &t : producer_threads_) if(t.joinable()) t.join();
            for(auto &t : consumer_threads_) if(t.joinable()) t.join();
        }
        return *this;
    }

    template daq &daq::stop<safe>(bool);
    template daq &daq::stop<unsafe>(bool);
    template daq &daq::start<safe>(bool);
    template daq &daq::start<unsafe>(bool);
    template daq &daq::initialize<safe>  (bool, const std::vector<std::vector<std::vector<bool>>>&, const std::vector<unsigned int>&, version);
    template daq &daq::initialize<unsafe>(bool, const std::vector<std::vector<std::vector<bool>>>&, const std::vector<unsigned int>&, version);
}

#ifdef FOR_PYTHON
extern "C"
{
    using namespace apdcam10g;
    daq         *create() { return new daq; }
    void         destroy(daq *self) { delete self; }
    void         mtu(daq *self, int m) { self->mtu(m); }
    void         start(daq *self, bool wait) { self->start(wait); }
    void         stop(daq *self, bool wait) { self->stop(wait); }
    void         initialize(daq *self, bool dual_sata, int n_adc_boards, bool ***channel_masks, unsigned int *resolution_bits, version ver, bool is_safe)
    {
        std::vector<std::vector<std::vector<bool>>> chmasks(n_adc_boards);
        std::vector<unsigned int> rbits(n_adc_boards);
        for(unsigned int i_adc_board=0; i_adc_board<n_adc_boards; ++i_adc_board)
        {
            chmasks[i_adc_board].resize(4);
            rbits[i_adc_board] = resolution_bits[i_adc_board];
            for(unsigned int i_chip=0; i_chip<4; ++i_chip)
            {
                chmasks[i_adc_board][i_chip].resize(8);
                for(unsigned int i_channel=0; i_channel<8; ++i_channel)
                {
                    chmasks[i_adc_board][i_chip][i_channel] = channel_masks[i_adc_board][i_chip][i_channel];
                }
            }
        }

        if(is_safe) self->initialize<safe>(dual_sata,chmasks,rbits,ver);
        else        self->initialize<unsafe>(dual_sata,chmasks,rbits,ver);
    }
    void         dump(daq *self) { self->dump(); }
}
#endif
