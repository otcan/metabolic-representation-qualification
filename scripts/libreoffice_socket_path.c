/* Local-host workaround: this host's virtual /tmp cannot bind Unix sockets.
 * Redirect only LibreOffice IPC sockets into the current workspace. This shim
 * is optional and used only by the document renderer, never scientific code. */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <stddef.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/un.h>

static const struct sockaddr *redirect(const struct sockaddr *a, socklen_t *n,
                                       struct sockaddr_un *out) {
    const struct sockaddr_un *in = (const struct sockaddr_un *)a;
    if (a && a->sa_family == AF_UNIX && !strncmp(in->sun_path, "/tmp/OSL_PIPE_", 14)) {
        memset(out, 0, sizeof(*out));
        out->sun_family = AF_UNIX;
        const char *prefix = "work/doc-ipc/";
        if (strlen(prefix) + strlen(in->sun_path + 5) < sizeof(out->sun_path)) {
            strcpy(out->sun_path, prefix);
            strcat(out->sun_path, in->sun_path + 5);
            *n = offsetof(struct sockaddr_un, sun_path) + strlen(out->sun_path) + 1;
            return (const struct sockaddr *)out;
        }
    }
    return a;
}
int bind(int fd, const struct sockaddr *a, socklen_t n) {
    static int (*real_fn)(int, const struct sockaddr *, socklen_t);
    if (!real_fn) real_fn = dlsym(RTLD_NEXT, "bind");
    struct sockaddr_un out;
    const struct sockaddr *target = redirect(a, &n, &out);
    return real_fn(fd, target, n);
}
int connect(int fd, const struct sockaddr *a, socklen_t n) {
    static int (*real_fn)(int, const struct sockaddr *, socklen_t);
    if (!real_fn) real_fn = dlsym(RTLD_NEXT, "connect");
    struct sockaddr_un out;
    const struct sockaddr *target = redirect(a, &n, &out);
    return real_fn(fd, target, n);
}
int unlink(const char *path) {
    static int (*real_fn)(const char *);
    if (!real_fn) real_fn = dlsym(RTLD_NEXT, "unlink");
    char out[108];
    if (path && !strncmp(path, "/tmp/OSL_PIPE_", 14) && strlen(path) + 8 < sizeof(out)) {
        strcpy(out, "work/doc-ipc/");
        strcat(out, path + 5);
        return real_fn(out);
    }
    return real_fn(path);
}
