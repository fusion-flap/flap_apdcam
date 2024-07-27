#ifndef __APDCAM10G_UDP_SOCKET_H__
#define __APDCAM10G_UDP_SOCKET_H__

#include "safeness.h"
#include "error.h"
#include <cstddef>
#include <sys/socket.h>
#include <netinet/in.h>

namespace apdcam10g
{
    class udp_socket
    {
    protected:
        int       fd_ = 0;  // file descriptor (socket)
        bool      blocking_ = false;
        bool      active_ = true;

    public:
        // Constructor, do not open/bind socket
        udp_socket() {}

        // Destructor, close the socket if open
        ~udp_socket() { close(); }

        // Set blocking/non-blocking status
        udp_socket &blocking(bool b);
        
        udp_socket &open(unsigned int port);

        // Close the socket and free resources
        void close();

        // Return the state of the 'active' flag. This flag is automatically set to true upon opening,
        // and to false upon closing. However, the user has control over this flag and can set
        // via the 'active(bool)' member function
        bool active() const { return active_; }

        // Set the 'active' flag
        udp_socket &active(bool a) { active_ = a; return *this; }
    };

    class udp_server : public udp_socket
    {
    private:
        sockaddr_in server_address_;  // This stores the port number where the server is listening, and INADDR_ANY to allow connections from anywhere
        sockaddr_in client_address_;  // This stores the last client's IP address after the reception of a package
        
    public:
        udp_server() {}
        udp_server(unsigned int port) { open(port); }

        udp_server &open(unsigned int port);

        // Receive data from the port associated with this server, and store the client
        // address for subsequent (optional) answers back to the client
        template <safeness s=default_safeness>
        int recv(std::byte *buffer, int length);
        template <safeness s=default_safeness>
        int recv(char *buffer, int length);

        std::string last_ip() const;

        // Send data back to the client address, obtained during the last call to 'recv'
        // Behavior is undefined if there was no previous recv call
        template <safeness s=default_safeness>
        int send(const std::byte *buffer, int length);
        template <safeness s=default_safeness>
        int send(const char *buffer, int length);
    };

    class udp_client : public udp_socket
    {
    private:
        sockaddr_in server_address_;
        
    public:
        udp_client() {}
        udp_client(unsigned int port, const std::string &ip_address) { open(port,ip_address); }

        // Set connection parameters for the remote server
        udp_client &open(unsigned int port, const std::string &ip_address);

        template <safeness s=default_safeness>
        int recv(std::byte *buffer, int length);
        template <safeness s=default_safeness>
        int recv(char *buffer, int length);

        template <safeness s=default_safeness>
        int send(const std::byte *buffer, int length);
        template <safeness s=default_safeness>
        int send(const char *buffer, int length);
    };

}

#endif
