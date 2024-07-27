#include "pstream.h"
#include <iostream>
#include <unistd.h>
#include <sys/wait.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <errno.h>
#include <streambuf>
#include <cstring>
#include <stdlib.h>
#include "error.h"

namespace apdcam10g
{
    using namespace std;

    void pipehandler(int)
    {
	cerr<<"Broken pipe (child caught signal)"<<endl;
	exit(0);
    }

    class pipebuf: public std::streambuf
    {
    private:
	int status_;
	int child_pid_;
	std::string cmd_;
	int fd_in_,fd_out_;
	int put_buffer();
	void fetch_status(int);
    public:
	bool is_open();
	pipebuf *open(const std::string &command, int mode);
	int close();
	
	void setinputbuffer(int size);
	void setoutputbuffer(int size);
	
	pipebuf();
	~pipebuf();
	
	int sync();
	int overflow(int c);
	int underflow();
	int uflow();

	const std::string &cmd() const { return cmd_; }

	void kill(int sig=SIGTERM);
    };
    
    void pipebuf::kill(int sig)
    {
	if(child_pid_ <= 0) return;
	sync();
	::kill(child_pid_,sig);
	//close();
    }

    pipebuf::pipebuf()
    {
	setg(0,0,0);
	setp(0,0);
	fd_in_ = fd_out_ = child_pid_ = 0;
	status_ = 0;
    }
    
    pipebuf::~pipebuf()
    {
	this->close();
	delete [] eback();
	delete [] pbase();
    }

    pipebuf *pipebuf::open(const std::string &command, int mode)
    {
	status_ = 0;

	cmd_ = command;
	fd_in_ = fd_out_ = 0;
	
	int   fd_read[2] = {0,0};
	int   fd_write[2] = {0,0};
	
	if(mode & ios::in)
	{
	    if(pipe(fd_read) < 0)
	    {
		std::cerr<<"Error opening a pipe in pipebuf::open"<<endl;
		return 0;
	    }
	}

	if(mode & ios::out)
	{
	    if(pipe(fd_write) < 0)
	    {
		std::cerr<<"Error opening a pipe in pipebuf::open"<<endl;
		return 0;
	    }
	}

	if((child_pid_=fork()) < 0)
	{
	    APDCAM_ERROR("Fork error in pipebuf::open");
	    return 0;
	}

	// now: fd[0] == for reading in both parent and child
	//      fd[1] == for writing

	if(child_pid_ > 0) //parent
	{
	    if( mode & ios::out )
	    {
		::close(fd_write[0]);
		fd_out_ = fd_write[1];
	    }

	    if( mode & ios::in )
	    {
		::close(fd_read[1]);
		fd_in_  = fd_read[0];
	    }

	    return this;
	}
	else // child
	{
	    signal(SIGPIPE, pipehandler);

	    bool ok = true;

	    if( mode & ios::out )
	    {
		::close(fd_write[1]);

		if(fd_write[0] != STDIN_FILENO)
		{
		    if(dup2(fd_write[0],STDIN_FILENO) != STDIN_FILENO)
		    {
			std::cerr<<"dup2 failed in pipebuf::open"<<endl;
			ok = false;
		    }
		    ::close(fd_write[0]);
		}
	    }

	    if( mode & ios::in )
	    {
		::close(fd_read[0]);

		if(fd_read[1] != STDOUT_FILENO)
		{
		    if(dup2(fd_read[1],STDOUT_FILENO) != STDOUT_FILENO)
		    {
			std::cerr<<"dup2 failed in pipebuf::open"<<endl;
			ok = false;
		    }
		    ::close(fd_read[1]);
		}
	    }

	    if(ok)
	    {
		const char *shell = "/bin/bash";
		struct stat buf;
		if(stat(shell,&buf) != 0) shell = "/bin/sh";
		execl(shell, "sh", "-c", command.c_str(), NULL);

		// the next line does not get executed, only if execl fails
		cerr<<"execl failed ...."<<endl;
		_exit(127);
	    }
	}
	return 0;
    }


    int pipebuf::close()
    {
	if(fd_in_ > 0 || fd_out_ > 0) sync();
	if(fd_out_ > 0)
	{
	    ::close(fd_out_);
	    fd_out_ = 0;
	}

	if(fd_in_ > 0)
	{
	    ::close(fd_in_);
	    fd_in_ = 0;
	}

	if(child_pid_ > 0) 
	{
	    int wret,status;
	    while((wret=waitpid(child_pid_, &status, 0)) < 0)
	    {
		if(errno != EINTR)
		{
		    cerr<<"waitpid returned "<<wret<<endl;
		    return -1;
		}
	    }
	    fetch_status(status);
	    child_pid_ = 0;
	}
	return status_;
    }

    void pipebuf::fetch_status(int status)
    {
	if(WIFEXITED(status))
	{
	    status_ = WEXITSTATUS(status);
	}
	else if(WIFSIGNALED(status))
	{
	    status_ = WTERMSIG(status);
	}
	else if(WIFSTOPPED(status))
	{
	    status_ = WSTOPSIG(status);
	}
	else
	{
	    cerr<<"This should not happend"<<endl;
	    status_ = status;
	}
    }

    bool pipebuf::is_open()
    {
	if(child_pid_ <= 0) return false;
	if(fd_in_<=0 && fd_out_<=0) return false;

	int status;
	int ret = waitpid(child_pid_,&status,WNOHANG);

	if(ret != 0)
	{
	    child_pid_ = 0;
	    if(fd_in_  > 0) { ::close(fd_in_);  fd_in_  = 0; }
	    if(fd_out_ > 0) { ::close(fd_out_); fd_out_ = 0; }
	    if(ret > 0)  fetch_status(status);
	    else status_ = -1;
	    return false;
	}

	return true;
    }

    void pipebuf::setinputbuffer(int size)
    {
	delete [] eback();
	if(size > 0)
	{
	    char *ptr = new char[size];
	    setg(ptr,ptr+size,ptr+size);
	}
	else setg(0,0,0);
    }

    void pipebuf::setoutputbuffer(int size)
    {
	delete [] pbase();
	if(size > 0)
	{
	    char *ptr = new char[size];
	    setp(ptr,ptr+size);
	}
	else setp(0,0);
    }

    int pipebuf::sync()
    {
	if(pbase() != pptr()) put_buffer();
	return 0;
    }

    int pipebuf::overflow(int c)
    {
	if(pbase() != pptr())
	{
	    if(put_buffer() == EOF) return EOF;
	}

	if(c != EOF)
	{
	    if(pbase() == epptr()) // unbuffered
	    {
		char cc = (char)c;
		if(write(fd_out_,&cc,1) != 1)
		{
		    std::cerr<<"Write error in pipebuf::overflow"<<endl;
		    return EOF;
		}
	    }
	    else sputc(c);
	}
	return 0;
    }

    int pipebuf::put_buffer()
    {
	if(write(fd_out_, pbase(), pptr() - pbase()) < 0)
	{
	    std::cerr<<"Write error in pipebuf::put_buffer"<<endl;
	    return EOF;
	}
	setp(pbase(), epptr());
	return 0;
    }

    int pipebuf::uflow()
    {
	char c;
	if(read(fd_in_,&c,1) <= 0) return EOF;
	return c;
    }

    int pipebuf::underflow()
    {
	int size = egptr() - eback();
	if(size <= 0)
	{
	    cerr<<"pipebuf::underflow called for unbuffered input !!!"<<endl;
	    return EOF;
	}
	int new_size = read(fd_in_, eback(), size);
	if(new_size == 0)
	{
	    setg(eback(),eback(),eback());
	    return EOF;
	}
	if(new_size < 0)
	{
	    setg(0,0,0);
	    return EOF;
	}
	setg ( eback(), eback(), eback() + new_size );
	return *eback();
    }

    // ----------------------------------------------------------

    std::string pstream_base::cmd() const
    {
	return (buffer_?buffer_->cmd():"");
    }

    bool pstream_base::is_open() const
    {
	if(buffer_ == 0) return false;
	return buffer_->is_open();
    }

    void pstream_base::kill(int sig)
    {
	if(buffer_ == 0) return;
	buffer_->kill(sig);
    }

    // ------------------  ipstream  ---------------------------


    ipstream::ipstream(const ipstream &) : istream(0)
    {
	buffer_ = 0;
    }

    ipstream::ipstream() : istream(0)
    {
	buffer_ = new pipebuf;
	istream::init(buffer_);
    }

    ipstream::ipstream(const std::string &command) : istream(0)
    {
	buffer_ = new pipebuf;
	istream::init(buffer_);
	open(command);
    }

    ipstream &ipstream::open(const std::string &command)
    {
	clear();
	buffer_->setinputbuffer(1000);
	if(buffer_->open(command,ios::in) == 0)
	{
	    setstate(ios::failbit | ios::badbit);
	}
	return *this;
    }

    int ipstream::close()
    {
	return buffer_->close();
    }

    ipstream::~ipstream()
    {
	close();
	delete buffer_;
    }

    void ipstream::ibufsize(int size)
    {
	buffer_->setinputbuffer(size);
    }


    // ------------------  opstream  -------------------------------------
    

    opstream::opstream(const opstream &) : ostream(0)
    {
	buffer_ = 0;
    }

    opstream::opstream() : ostream(0)
    {
	buffer_ = new pipebuf;
	ostream::init(buffer_);
    }

    opstream::opstream(const std::string &command) : ostream(0)
    {
	buffer_ = new pipebuf;
	ostream::init(buffer_);
	open(command);
    }

    opstream &opstream::open(const std::string &command)
    {
	clear();
	buffer_->setoutputbuffer(1000);
	if(buffer_->open(command,ios::out) == 0)
	{
	    setstate(ios::failbit | ios::badbit);
	}
	return *this;
    }

    int opstream::close()
    {
	return buffer_->close();
    }

    opstream::~opstream()
    {
	close();
	delete buffer_;
    }

    void opstream::obufsize(int size)
    {
	buffer_->setoutputbuffer(size);
    }

    // ---------------------------

    iremotestream::iremotestream(const string &cmd, const char *name, ios_base::openmode mode)
	: cmd_template_(cmd)
    {
	iremotestream::open(name,mode);
    }

    void iremotestream::open(const char *name, ios_base::openmode mode)
    {
	remote_filename_ = name;
        char tmpbuf[] = "/tmp/oremote-XXXXXX";
	local_filename_ = mktemp(tmpbuf);
	char cmd[1000];
	sprintf(cmd,cmd_template_.c_str(),remote_filename_.c_str(),local_filename_.c_str());
	if(system(cmd) != 0)
	{
	    APDCAM_ERROR(std::string("Failed to execute ") + cmd);
	}
	ifstream::open(local_filename_.c_str(),mode);
    }
				 

    iscpstream::iscpstream(const char *name, ios_base::openmode mode)
	: iremotestream("scp %s %s",strstr(name,"scp://")!=name?name:name+6,mode)
    {}

    ihttpstream::ihttpstream(const char *name, ios_base::openmode mode)
	: iremotestream("wget %s -O %s",strstr(name,"scp://")!=name?name:name+6,mode)
    {}

    // --------------------------------------------------------
    oremotestream::oremotestream(const string &cmd, const char *name, ios_base::openmode mode)
	: cmd_template_(cmd)
    {
	oremotestream::open(name,mode);
    }

    void oremotestream::open(const char *name, ios_base::openmode mode)
    {
	if(mode != ios_base::out)
	{
	    APDCAM_ERROR("At the moment only ios_base::out is supported as the openmode");
	}
	remote_filename_ = name;
        char tmpbuf[] = "/tmp/oremote-XXXXXX";
	local_filename_ = mktemp(tmpbuf);
	ofstream::open(local_filename_.c_str(),mode);
    }

    void oremotestream::close()
    {
	ofstream::close();
	char cmd[1000];
	sprintf(cmd,cmd_template_.c_str(),local_filename_.c_str(),remote_filename_.c_str());
	if(system(cmd) != 0)
	{
	    APDCAM_ERROR(std::string("Failed to execute ") + cmd);
	}
    }

    oremotestream::~oremotestream()
    {
	oremotestream::close();
    }

    // ----------------------------

    oscpstream::oscpstream(const char *name, ios_base::openmode mode)
	: oremotestream("scp %s %s",strstr(name,"scp://")!=name?name:name+6,mode)
    {}
}
