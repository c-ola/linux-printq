#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
#include <stdarg.h>
#include <unistd.h>
#include <string.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <libgen.h>
#include <stdlib.h>
#include <errno.h>

static int (*real_unlink)(const char *pathname) = NULL;
static int (*real_unlinkat)(int dirfd, const char *pathname, int flags) = NULL;

static void ensure_fns(void) {
    if (!real_unlink) real_unlink = dlsym(RTLD_NEXT, "unlink");
    if (!real_unlinkat) real_unlinkat = dlsym(RTLD_NEXT, "unlinkat");
}

static void try_copy_before_unlink(const char *path) {
    if (!path) return;
    // only care about files named "url.out" inside dirs named is-*.tmp
    const char *fname = strrchr(path, '/');
    if (fname) fname++; else fname = path;

    if (strcmp(fname, "url.out") != 0) return;

    // check parent dir name
    char *p = strdup(path);
    if (!p) return;
    char *dir = dirname(p);
    char *base = basename(dir);
    if (!base) { free(p); return; }
    if (strncmp(base, "is-", 3) != 0) { free(p); return; }

    // attempt to copy file to /tmp/captured-url-<pid>-<rand>
    char dest[512];
    pid_t pid = getpid();
    snprintf(dest, sizeof(dest), "/tmp/captured-url-%d-%ld.out", (int)pid, random());
    int srcfd = open(path, O_RDONLY);
    if (srcfd >= 0) {
        int dstfd = open(dest, O_CREAT | O_WRONLY, 0600);
        if (dstfd >= 0) {
            char buf[8192];
            ssize_t r;
            while ((r = read(srcfd, buf, sizeof(buf))) > 0) {
                ssize_t w = write(dstfd, buf, r);
                (void)w;
            }
            close(dstfd);
            // optionally signal or log where it was saved
            FILE *log = fopen("/tmp/capture-unlink.log","a");
            if (log) {
                fprintf(log, "pid %d copied %s -> %s\n", (int)pid, path, dest);
                fclose(log);
            }
        }
        close(srcfd);
    }
    free(p);
}

int unlink(const char *pathname) {
    ensure_fns();
    try_copy_before_unlink(pathname);
    return real_unlink(pathname);
}

int unlinkat(int dirfd, const char *pathname, int flags) {
    ensure_fns();
    // build full path if needed: best-effort only
    if (pathname && pathname[0] == '/') {
        try_copy_before_unlink(pathname);
    } else {
        // attempt readlink of /proc/self/fd/dirfd to build path (not always possible)
        char procpath[256];
        snprintf(procpath, sizeof(procpath), "/proc/self/fd/%d", dirfd);
        char resolved[4096];
        ssize_t n = readlink(procpath, resolved, sizeof(resolved)-1);
        if (n > 0) {
            resolved[n] = '\0';
            char full[8192];
            snprintf(full, sizeof(full), "%s/%s", resolved, pathname);
            try_copy_before_unlink(full);
        }
    }
    return real_unlinkat(dirfd, pathname, flags);
}

