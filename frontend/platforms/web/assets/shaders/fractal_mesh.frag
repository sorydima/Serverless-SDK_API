// Fractal Mesh Shader
// Creates fractal patterns representing mesh network topology

#version 320 es
precision mediump float;

uniform vec2 u_resolution;
uniform float u_time;
uniform vec2 u_mouse;

out vec4 fragColor;

#define PI 3.14159265359
#define ITERATIONS 8

// Fractal parameters
const float SCALE = 2.0;
const vec2 OFFSET = vec2(-0.5, 0.0);

// Complex number operations for fractal calculation
vec2 complexMultiply(vec2 a, vec2 b) {
    return vec2(a.x * b.x - a.y * b.y, a.x * b.y + a.y * b.x);
}

vec2 complexSquare(vec2 z) {
    return vec2(z.x * z.x - z.y * z.y, 2.0 * z.x * z.y);
}

// Mandelbrot fractal calculation
float mandelbrot(vec2 c) {
    vec2 z = vec2(0.0);
    float iterations = 0.0;

    for(int i = 0; i < ITERATIONS; i++) {
        if(length(z) > 2.0) break;
        z = complexSquare(z) + c;
        iterations += 1.0;
    }

    return iterations / float(ITERATIONS);
}

// Julia set fractal
float julia(vec2 z, vec2 c) {
    float iterations = 0.0;

    for(int i = 0; i < ITERATIONS; i++) {
        if(length(z) > 2.0) break;
        z = complexSquare(z) + c;
        iterations += 1.0;
    }

    return iterations / float(ITERATIONS);
}

// Mesh network inspired color palette
vec3 meshColor(float value) {
    vec3 colors[5] = vec3[](
        vec3(0.0, 0.2, 0.4),  // Deep blue (disconnected)
        vec3(0.0, 0.4, 0.8),  // Blue (connecting)
        vec3(0.0, 0.8, 0.4),  // Green (connected)
        vec3(0.8, 0.8, 0.0),  // Yellow (weak signal)
        vec3(0.8, 0.4, 0.0)   // Orange (strong signal)
    );

    float index = value * 4.0;
    int i = int(index);
    float frac = index - float(i);

    if(i >= 4) return colors[4];
    return mix(colors[i], colors[i + 1], frac);
}

// Add mesh network overlay
vec3 addMeshOverlay(vec2 uv, vec3 baseColor) {
    // Create hexagonal mesh pattern
    vec2 hexUV = uv * 10.0;
    vec2 hex = vec2(hexUV.x + hexUV.y * 0.5, hexUV.y * 0.866);

    vec2 grid = fract(hex) - 0.5;
    float dist = length(grid);

    float mesh = smoothstep(0.4, 0.5, dist);

    // Animate mesh connections
    float pulse = sin(u_time * 2.0 + uv.x * 10.0 + uv.y * 10.0) * 0.5 + 0.5;
    vec3 meshColor = vec3(0.2, 0.6, 1.0) * pulse;

    return mix(baseColor, meshColor, mesh * 0.3);
}

void main() {
    vec2 uv = gl_FragCoord.xy / u_resolution.xy;
    uv = uv * 2.0 - 1.0; // Normalize to [-1, 1]
    uv.x *= u_resolution.x / u_resolution.y; // Correct aspect ratio

    // Mouse interaction
    vec2 mouse = (u_mouse - 0.5) * 2.0;

    // Create animated fractal
    vec2 c = uv * SCALE + OFFSET;
    c += mouse * 0.5; // Mouse affects fractal position

    // Combine Mandelbrot and Julia sets
    float mandelbrotValue = mandelbrot(c);
    vec2 juliaC = vec2(sin(u_time * 0.3) * 0.5, cos(u_time * 0.2) * 0.5);
    float juliaValue = julia(uv * 1.5, juliaC);

    // Mix the fractals
    float fractalValue = mix(mandelbrotValue, juliaValue, sin(u_time) * 0.5 + 0.5);

    // Apply mesh-inspired coloring
    vec3 color = meshColor(fractalValue);

    // Add mesh network overlay
    color = addMeshOverlay(uv, color);

    // Add time-based animation
    float timeEffect = sin(u_time + uv.x * 5.0 + uv.y * 5.0) * 0.1;
    color += vec3(timeEffect);

    fragColor = vec4(color, 0.7);
}
