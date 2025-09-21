#version 430

in vec4 p3d_Vertex;
in vec3 p3d_Normal;
in vec2 p3d_MultiTexCoord0;

uniform mat4 p3d_ModelViewProjectionMatrix;
uniform mat4 p3d_ModelMatrix;

out vec3 world_position;
out vec3 normal;
out vec2 texcoord;

void main() {
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    world_position = (p3d_ModelMatrix * p3d_Vertex).xyz;
    normal = normalize((p3d_ModelMatrix * vec4(p3d_Normal, 0.0)).xyz);
    texcoord = p3d_MultiTexCoord0;
}
