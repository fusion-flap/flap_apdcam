#include "udp.h"
#include <string>
#include <string.h>
#include <errno.h>
#include <fcntl.h>
#include <netdb.h> 
#include <unistd.h>
#include <arpa/inet.h>
#include <iostream>

using namespace std;

// https://www.geeksforgeeks.org/udp-server-client-implementation-c/
// https://stackoverflow.com/questions/18995361/can-recvfrom-function-from-socket-extract-the-sender-ip-address

namespace apdcam10g
{
    void udp_socket::close()
    {
        if(fd_!=0) ::close(fd_);
        fd_ = 0;
        active_ = false;
    }

    udp_socket &udp_socket::open(unsigned int port)
    {
        if(fd_ != 0) close();
        if((fd_ = socket(AF_INET,SOCK_DGRAM,0))<0) APDCAM_ERROR(string("Error creating UDP server socket: ") + strerror(errno));
        blocking(blocking_);
        return *this;
    }

    udp_socket &udp_socket::blocking(bool b)
    {
        blocking_ = b;
        if(fd_ == 0) return *this;
        
        int flags = fcntl(fd_,F_GETFL);
        if(!blocking_) flags |= O_NONBLOCK;
        else flags &= ~O_NONBLOCK;
        fcntl(fd_,F_SETFL,flags);
        return *this;
    }

    udp_server &udp_server::open(unsigned int port) 
    {
        udp_socket::open(port);
        memset(&server_address_, 0, sizeof(server_address_)); 
        memset(&client_address_, 0, sizeof(client_address_));
        server_address_.sin_family    = AF_INET; // IPv4 
        server_address_.sin_addr.s_addr = INADDR_ANY; 
        server_address_.sin_port = htons(port);
        if(bind(fd_, (sockaddr*)&server_address_, sizeof(server_address_)) == -1) APDCAM_ERROR(string("Error binding the socket: ") + strerror(errno));
        return *this;
    }

    std::string udp_server::last_ip() const
    {
        char ip[100];
        inet_ntop(AF_INET,&client_address_.sin_addr,ip,100);
        return ip;
    }

    template <safeness s>
    int udp_server::recv(std::byte *buffer, int length)
    {
        socklen_t len = sizeof(client_address_);
        int n = recvfrom(fd_, (char*)buffer, length, 0, (sockaddr*) &client_address_, &len); 
        return n;
    }
    template <safeness s>
    int udp_server::recv(char *buffer, int length)
    {
        socklen_t len = sizeof(client_address_);
        int n = recvfrom(fd_, buffer, length, 0, (sockaddr*) &client_address_, &len); 
        return n;
    }

    template <safeness s>
    int udp_server::send(const std::byte *buffer, int length)
    {
        return sendto(fd_, (char*)buffer, length, 0, (const sockaddr*) &client_address_, sizeof(client_address_)); 
    }
    template <safeness s>
    int udp_server::send(const char *buffer, int length)
    {
        return sendto(fd_, buffer, length, 0, (const sockaddr*) &client_address_, sizeof(client_address_)); 
    }



    udp_client &udp_client::open(unsigned int port, const std::string &ip_address)
    {
        udp_socket::open(port);
        memset(&server_address_, 0, sizeof(server_address_)); 
        server_address_.sin_family = AF_INET; 
        server_address_.sin_port = htons(port); 
        inet_pton(AF_INET,ip_address.c_str(),&server_address_.sin_addr.s_addr);
        return *this;
    }

    template <safeness s>
    int udp_client::recv(std::byte *buffer, int length)
    {
        socklen_t len = sizeof(server_address_);
        int n = recvfrom(fd_, (char *)buffer, length, MSG_WAITALL, (sockaddr*) &server_address_, &len); 
        return n;
    }
    template <safeness s>
    int udp_client::recv(char *buffer, int length)
    {
        socklen_t len = sizeof(server_address_);
        int n = recvfrom(fd_, buffer, length, MSG_WAITALL, (sockaddr*) &server_address_, &len); 
        return n;
    }

    template <safeness s>
    int udp_client::send(const std::byte *buffer, int length)
    {
        return sendto(fd_, (const char *)buffer, length, MSG_CONFIRM, (const sockaddr*) &server_address_, sizeof(server_address_)); 
    }
    template <safeness s>
    int udp_client::send(const char *buffer, int length)
    {
        return sendto(fd_, buffer, length, MSG_CONFIRM, (const sockaddr*) &server_address_, sizeof(server_address_)); 
    }

    // template instantiation
    template int udp_server::recv<safe>(std::byte *buffer, int length);
    template int udp_server::recv<unsafe>(std::byte *buffer, int length);
    template int udp_server::recv<safe>(char *buffer, int length);
    template int udp_server::recv<unsafe>(char *buffer, int length);

    template int udp_server::send<safe>(const std::byte *buffer, int length);
    template int udp_server::send<unsafe>(const std::byte *buffer, int length);
    template int udp_server::send<safe>(const char *buffer, int length);
    template int udp_server::send<unsafe>(const char *buffer, int length);

    template int udp_client::recv<safe>(std::byte *buffer, int length);
    template int udp_client::recv<unsafe>(std::byte *buffer, int length);
    template int udp_client::recv<safe>(char *buffer, int length);
    template int udp_client::recv<unsafe>(char *buffer, int length);

    template int udp_client::send<safe>(const std::byte *buffer, int length);
    template int udp_client::send<unsafe>(const std::byte *buffer, int length);
    template int udp_client::send<safe>(const char *buffer, int length);
    template int udp_client::send<unsafe>(const char *buffer, int length);


}
