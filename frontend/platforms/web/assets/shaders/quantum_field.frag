// Quantum Field Shader
// Creates a dynamic quantum field effect with particles and waves

#version 320 es
precision mediump float;

uniform vec2 u_resolution;
uniform float u_time;
uniform vec2 u_mouse;

out vec4 fragColor;

#define PI 3.14159265359

// Quantum field parameters
const float PARTICLE_COUNT = 50.0;
const float WAVE_SPEED = 0.5;
const float FIELD_INTENSITY = 0.8;

// Noise function for organic movement
float noise(vec2 st) {
    return fract(sin(dot(st.xy, vec2(12.9898,78.233))) * 43758.5453123);
}

// Quantum particle
vec3 quantumParticle(vec2 uv, vec2 pos, float time) {
    vec2 diff = uv - pos;
    float dist = length(diff);

    // Quantum wave function
    float wave = sin(dist * 10.0 - time * WAVE_SPEED) * 0.5 + 0.5;
    float probability = exp(-dist * dist * 4.0);

    // Color based on quantum state
    vec3 color = vec3(
        0.2 + wave * 0.3,  // Blue component
        0.1 + probability * 0.4,  // Green component
        0.8 - wave * 0.2   // Red component
    );

    return color * probability * FIELD_INTENSITY;
}

void main() {
    vec2 uv = gl_FragCoord.xy / u_resolution.xy;
    uv = uv * 2.0 - 1.0; // Normalize to [-1, 1]

    vec3 finalColor = vec3(0.0);

    // Generate quantum field
    for(float i = 0.0; i < PARTICLE_COUNT; i++) {
        // Particle position with noise-based movement
        vec2 particlePos = vec2(
            sin(u_time * 0.3 + i * 0.1) * 0.8,
            cos(u_time * 0.2 + i * 0.15) * 0.6
        );

        // Add mouse influence
        particlePos += (u_mouse - 0.5) * 0.2;

        finalColor += quantumParticle(uv, particlePos, u_time + i);
    }

    // Add interference patterns
    float interference = sin(uv.x * 20.0 + u_time) * sin(uv.y * 20.0 + u_time) * 0.1;
    finalColor += vec3(interference);

    // Add quantum uncertainty (random fluctuations)
    float uncertainty = noise(uv + u_time * 0.1) * 0.05;
    finalColor += vec3(uncertainty);

    fragColor = vec4(finalColor, 0.3);
}
