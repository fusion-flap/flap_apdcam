#ifndef __APDCAM10G_MEMBER_PTR_H__
#define __APDCAM10G_MEMBER_PTR_H__

namespace apdcam10g
{
    /*

      Description of the problem:

      class Base { virtual void show() { cerr<<"Base"<<endl; }
      class Derived : public Base { void show() { cerr<<"Derived"<<endl; }
      class Parent
      {
        public:
          Derived d;
      }

      Now, even though Derived is based from Base, one can not store the pointer-to-member of the member 'd'
      in a "Base Parent::*" type variable:

      Base Parent::*ptr = &Parent::d;   // error
      
     */

    template <typename PARENT, typename BASE, typename DERIVED>
    class member_ptr__ : public member_ptr__<PARENT,BASE,void>
    {
    private:
        DERIVED PARENT::*ptr_ = 0;
    public:

        // Constructor, initialize to point to a given member of type DERIVED
        // of a class of type PARENT
        member_ptr__(DERIVED PARENT::*p) : ptr_(p) {}
        
        const member_ptr__<PARENT,BASE,DERIVED> &operator= (DERIVED PARENT::*p)
            {
                ptr_ = p;
                return *this;
            }
        
        typedef DERIVED PARENT::*type;
        operator type() const { return ptr_; }
        
        BASE *dereference(PARENT *p)
            {
                return &(p->*ptr_);
            }
        member_ptr__<PARENT,BASE,DERIVED> *clone() const
            {
                return new member_ptr__<PARENT,BASE,DERIVED>(ptr_);
            }
    };
    
    // The base class (specialization), which only provides a virtual dereferencing parenthesis operator.
    template <typename PARENT, typename BASE>
    class member_ptr__<PARENT,BASE,void>
    {
    public:
        virtual BASE *dereference(PARENT *p) = 0;
    };
    

    template <typename PARENT, typename BASE>
    class member_ptr
    {
    private:
        member_ptr__<PARENT,BASE,void> *ptr_ = 0;

    public:
        ~member_ptr() { delete ptr_; }
        member_ptr(const member_ptr<PARENT,BASE> &rhs) { ptr_ = rhs.ptr_->clone(); }
        template <typename DERIVED>
        member_ptr(DERIVED PARENT::*p) { ptr_ = new member_ptr__<PARENT,BASE,DERIVED>(p); }

        template <typename DERIVED>
        const member_ptr<PARENT,BASE> &operator=(DERIVED PARENT::*p) 
            {
                delete ptr_;
                ptr_ = new member_ptr__<PARENT,BASE,DERIVED>(p);
                return *this;
            }

        BASE *operator()(PARENT *p)
            {
                if(!ptr_) return 0;
                return ptr_->dereference(p);
            }
    };


    
        
}

#endif
