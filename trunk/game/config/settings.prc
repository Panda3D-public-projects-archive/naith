# Don't limit us to the arbvp1/arbfp1 shader profiles
basic-shaders-only #f

# Automatically determine that the GPU supports textures-power-2...
textures-power-2 up
textures-auto-power-2 #t

# Enable multisampling...
framebuffer-multisample #t
multisamples 1

# Portal support so we can clip large chunks of geometry...
allow-portal-cull 1
show-portal-debug 0

window-title Naith
