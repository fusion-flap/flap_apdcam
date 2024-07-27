// Compile with: g++ -fPIC -shared -o libtest.so Test.C



#include <iostream>
#include <string>
using namespace std;

class Test{
     private:
        int n;
     public:
        Test(int k){
            n=k;
        }
        void setInt(int k){
            n = k;
        }
        int getInt(){
            return n;
        }
    void show(const string &s) { cerr<<s<<endl; }
};

extern "C" 
{
    // include below each method you want to make visible outside
    Test* init(int k) {return new Test(k);}
    void setInt(Test *self, int k) {self->setInt(k);}
    int getInt(Test *self) {return self->getInt();}
    void show(Test *self, char *s) { self->show(s); }
}
