with open("/etc/containerd/config.toml") as f:
    c = f.read()

c = c.replace(
    '        endpoint = ["http://172.28.0.56:90"]',
    '        endpoint = ["http://172.28.0.56:90"]\n'
    '      [plugins."io.containerd.grpc.v1.cri".registry.mirrors."172.28.0.165:30090"]\n'
    '        endpoint = ["http://172.28.0.165:30090"]',
    1
)

l = c.split("\n")
for i in range(len(l)):
    if "172.28.0.56:90" in l[i] and "registry.configs" in l[i] and i + 3 < len(l):
        l.insert(i + 3, "")
        l.insert(i + 3, '          insecure_skip_verify = true')
        l.insert(i + 3, '          http = true')
        l.insert(i + 3, '        [plugins."io.containerd.grpc.v1.cri".registry.configs."172.28.0.165:30090"]')
        break

c = "\n".join(l)
open("/etc/containerd/config.toml", "w").write(c)
print("OK")