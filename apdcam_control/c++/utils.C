#include "utils.h"


using namespace std;

namespace apdcam10g
{
    vector<string> split(const string &s,const string &separator)
    {
	vector<string> out;
	string w;
	for(unsigned int i=0; i<s.size(); ++i)
	{
	    if(separator.find(s[i]) != string::npos)
	    {
		if(w != "") out.push_back(w);
		w = "";
	    }
	    else
	    {
		w += s[i];
	    }
	}
	if(w != "") out.push_back(w);
	return out;
    }
    
}
