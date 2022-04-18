.PHONY: all clean

#ARCH=-m32
OBJ_DIR = objs
LIB_DIR = libs
BIN_DIR = .
#PG = -pg
CFLAGS = $(ARCH) -Wall -Wextra -ggdb -DAPD_VERSION -fPIC -Wno-unused -O2 -Wstrict-aliasing=0 -Wshadow -Wno-inline -Wno-disabled-optimization $(PG)
CXXFLAGS = $(CFLAGS) -Wno-effc++ -std=gnu++0x
LDFLAGS = $(PG) -ggdb $(ARCH) -L$(LIB_DIR) -Wl,-rpath=$(realpath $(LIB_DIR)) -lapd
LDFLAGS_PRE = $(PG) -ggdb $(ARCH) -L$(LIB_DIR) -Wl,-rpath=$(realpath $(LIB_DIR))
LDFLAGS_POST = -lapd -lcap -lpthread

APDLIB = $(LIB_DIR)/libapd.so
APDLIB_SRCS = helper.cpp UDPClient.cpp UDPServer.cpp GECClient.cpp GECCommands.cpp LowlevelFunctions.cpp InternalFunctions.cpp DataEvaluation.cpp HighlevelFunctions.cpp SysLnxClasses.cpp LnxClasses.cpp CamClient.cpp CamServer.cpp Helpers.cpp
APDLIB_OBJS = $(patsubst %,$(OBJ_DIR)/%,$(subst .cpp,.o,$(APDLIB_SRCS)))
APDLIB_LDFLAGS = $(ARCH) -lcap -lpthread

APDTEST = $(BIN_DIR)/APDTest_10G

APDTEST_SRCS = APDTest.cpp
APDTEST_OBJS = $(patsubst %,$(OBJ_DIR)/%,$(subst .cpp,.o,$(APDTEST_SRCS)))

OBJS = $(APDLIB_OBJS) $(APDTEST_OBJS)

all: $(APDLIB) $(APDTEST) dump_parser
#	@echo $(SRCS)
#	@echo $(OBJS)

$(BIN_DIR):
	mkdir -p $(BIN_DIR)

$(LIB_DIR):
	mkdir -p $(LIB_DIR)

$(OBJ_DIR):
	mkdir -p $(OBJ_DIR)

$(OBJ_DIR)/%.o: %.cpp Makefile
	mkdir -p $(OBJ_DIR)
	$(CXX) -c -o $@ $< $(CXXFLAGS)

dump_parser : $(BIN_DIR) $(OBJ_DIR)/dump_parser.o
	$(CXX) -o $@ $(OBJ_DIR)/dump_parser.o

$(APDLIB) : $(LIB_DIR) $(APDLIB_OBJS)
	$(CXX) $(PG) -o $@ -shared $(APDLIB_LDFLAGS) $(APDLIB_OBJS)

$(APDTEST) : $(APDLIB) $(BIN_DIR) $(APDTEST_OBJS)
# 1.	$(CXX) -o $@ $(LDFLAGS) $(APDTEST_OBJS)  # this works on the helium machine!
# This works on newer Linux OS-es:
	$(CXX) -o $@ $(LDFLAGS_PRE) $(APDTEST_OBJS) $(LDFLAGS_POST)
#	$(CXX) -static-libgcc -o $@ $(APDLIB_OBJS) $(APDTEST_OBJS) $(LDFLAGS)
# 1. g++ -o APDTest  -ggdb  -Llibs -Wl,-rpath=/home/csega/prog/APDTest_10G/libs -lapd objs/APDTest.o
# vs.
# g++ -o APDTest  -ggdb  -L./libs -Wl,--as-needed,-rpath=/home/apdcam/prog/APDTest_10G/libs ./objs/LnxClasses.o ./objs/APDTest.o -lapd -lcap -lpthread
# minimal working
# g++ -o APDTest  -ggdb  -Llibs -Wl,-rpath=/home/apdcam/prog/APDTest_10G/libs ./objs/APDTest.o -lapd -lcap -lpthread

clean:
	$(RM) $(OBJS) $(OBJ_DIR)/dump_parser.o

distclean: clean
	$(RM) $(APDTEST) $(APDLIB) dump_parser
