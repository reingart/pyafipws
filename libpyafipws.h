
#if defined(__GNUG__)

#define EXPORT extern "C" 
#define CONSTRUCTOR __attribute__((constructor))
#define DESTRUCTOR __attribute__((destructor))

#else

#include <windows.h>
#define EXPORT __declspec(dllexport) 
#define CONSTRUCTOR
#define DESTRUCTOR

BOOL WINAPI DllMain(HINSTANCE hInstance, DWORD dwReason, LPVOID lpReserved);

#define WIN32

#endif

EXPORT int test();
EXPORT char * WSAA_CreateTRA(const char *service, long ttl);
EXPORT char * WSAA_SignTRA(char *tra, char *cert, char *privatekey);
EXPORT char * WSAA_LoginCMS(char *cms);
