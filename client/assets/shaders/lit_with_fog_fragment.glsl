#version 430

in vec3 world_position;
in vec3 normal;
in vec2 texcoord;

uniform sampler2D p3d_Texture0;
uniform vec3 camera_pos;
uniform vec4 fog_color = vec4(0.0,0.0,0.0,1.0);
uniform float fog_density = 0.08;

out vec4 fragColor;

void main() {
    vec4 base_color = texture(p3d_Texture0, texcoord);

    // простое освещение
    vec3 light_dir = normalize(vec3(1,1,1));
    float diff = max(dot(normal, light_dir), 0.0);
    vec3 lighting = base_color.rgb * (0.2 + diff*0.8);

    // туман
    float dist = length(camera_pos - world_position);
    float fog_factor = exp(-pow((dist*fog_density),2.0));
    fog_factor = clamp(fog_factor,0.0,1.0);

    vec3 final_color = mix(fog_color.rgb, lighting, fog_factor);
    fragColor = vec4(final_color, base_color.a);
}
