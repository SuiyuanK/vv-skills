#define _GNU_SOURCE
#include <dlfcn.h>
#include <signal.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <unistd.h>
static int (*delegate)(int,const struct sigaction *,struct sigaction *);
static int active;
__attribute__((constructor)) static void setup(void) {
    delegate=dlsym(RTLD_NEXT,"sigaction");
    char exe[4096]; ssize_t n=readlink("/proc/self/exe",exe,sizeof(exe)-1);
    if(n>0) { exe[n]=0; active=!strcmp(exe,"/usr/lib/chatgpt/ChatGPT"); }
    unsetenv("LD_PRELOAD");
}
int sigaction(int sig,const struct sigaction *requested,struct sigaction *previous) {
    if(!delegate) delegate=dlsym(RTLD_NEXT,"sigaction");
    if(!delegate) { errno=ENOSYS; return -1; }
    if(active && sig==SIGCHLD && requested && requested->sa_flags==0) {
        Dl_info info;
        uintptr_t addr=(uintptr_t)requested->sa_handler;
        if(addr>1 && dladdr((void *)addr,&info) &&
           addr-(uintptr_t)info.dli_fbase==0x117d9f78 &&
           memcmp((void *)addr,"\xe9\x4b\xca\x50\x00",5)==0 &&
           memcmp((char *)info.dli_fbase+0x11ce69c8,"\x55\x48\x89\xe5\x5d\xc3",6)==0) {
            struct sigaction installed;
            if(delegate(SIGCHLD,NULL,&installed)==0 && (uintptr_t)installed.sa_handler>1) {
                if(previous) *previous=installed;
                static const char notice[]="[chatgpt-sigchld-guard] prevented known 26.924.22138 handler overwrite\n";
                (void)write(STDERR_FILENO,notice,sizeof(notice)-1);
                return 0;
            }
        }
    }
    return delegate(sig,requested,previous);
}
