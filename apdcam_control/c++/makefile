SRCS = $(wildcard *.C)
DEPS = $(SRCS:.C=.d)
OBJS = $(SRCS:.C=.o)

all : libapdcam10g.so

.PHONY: test clean
test:
	cd test; $(MAKE)

clean :
	rm -f *.o *.so *.d *~
	cd test; $(MAKE) clean

include $(DEPS)


%.o : %.C
	g++ -DFOR_PYTHON -fPIC -O2 -std=c++20 -c -o $@ $<

%.d : %.C
	g++ -DFOR_PYTHON -M -MF $@ $^

libapdcam10g.so : $(OBJS)
	echo $(OBJS)
	g++ -fPIC -shared -o $@ $^



