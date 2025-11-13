// Neural Network Visualization Shader
// Creates animated neural network connections and nodes

#version 320 es
precision mediump float;

uniform vec2 u_resolution;
uniform float u_time;
uniform vec2 u_mouse;

out vec4 fragColor;

#define PI 3.14159265359
#define NODE_COUNT 15

// Neural network parameters
const float CONNECTION_THICKNESS = 0.002;
const float NODE_SIZE = 0.02;
const float SIGNAL_SPEED = 2.0;

// Node positions (simulating neural network layers)
vec2 nodePositions[NODE_COUNT] = vec2[](
    vec2(-0.8, 0.8), vec2(-0.8, 0.4), vec2(-0.8, 0.0), vec2(-0.8, -0.4), vec2(-0.8, -0.8),
    vec2(-0.4, 0.6), vec2(-0.4, 0.2), vec2(-0.4, -0.2), vec2(-0.4, -0.6),
    vec2(0.0, 0.4), vec2(0.0, 0.0), vec2(0.0, -0.4),
    vec2(0.4, 0.2), vec2(0.4, -0.2),
    vec2(0.8, 0.0)
);

// Connection matrix (which nodes are connected)
bool connections[NODE_COUNT * NODE_COUNT] = bool[](
    // Layer 1 to Layer 2
    false, false, false, false, false, true, true, true, true, false, false, false, false, false, false,
    false, false, false, false, false, true, true, true, true, false, false, false, false, false, false,
    false, false, false, false, false, true, true, true, true, false, false, false, false, false, false,
    false, false, false, false, false, true, true, true, true, false, false, false, false, false, false,
    false, false, false, false, false, true, true, true, true, false, false, false, false, false, false,

    // Layer 2 to Layer 3
    false, false, false, false, false, false, false, false, false, true, true, true, false, false, false,
    false, false, false, false, false, false, false, false, false, true, true, true, false, false, false,
    false, false, false, false, false, false, false, false, false, true, true, true, false, false, false,
    false, false, false, false, false, false, false, false, false, true, true, true, false, false, false,

    // Layer 3 to Layer 4
    false, false, false, false, false, false, false, false, false, false, false, false, true, true, false,
    false, false, false, false, false, false, false, false, false, false, false, false, true, true, false,
    false, false, false, false, false, false, false, false, false, false, false, false, true, true, false,

    // Layer 4 to Output
    false, false, false, false, false, false, false, false, false, false, false, false, false, false, true,
    false, false, false, false, false, false, false, false, false, false, false, false, false, false, true
);

// Draw a connection between two points with animated signal
vec3 drawConnection(vec2 uv, vec2 start, vec2 end, float signalOffset) {
    vec2 dir = normalize(end - start);
    vec2 perp = vec2(-dir.y, dir.x);

    vec2 toStart = uv - start;
    float alongLine = dot(toStart, dir);
    float perpDist = abs(dot(toStart, perp));

    // Connection thickness
    float connection = smoothstep(CONNECTION_THICKNESS, 0.0, perpDist);

    // Animated signal
    float signalPos = mod(u_time * SIGNAL_SPEED + signalOffset, 1.0);
    float signal = smoothstep(0.02, 0.0, abs(alongLine - signalPos));

    return vec3(0.2, 0.8, 1.0) * connection + vec3(1.0, 0.5, 0.0) * signal * connection;
}

// Draw a node
vec3 drawNode(vec2 uv, vec2 pos, float activation) {
    float dist = length(uv - pos);
    float node = smoothstep(NODE_SIZE, 0.0, dist);

    // Activation color
    vec3 color = mix(
        vec3(0.2, 0.2, 0.3), // Inactive
        vec3(0.0, 1.0, 0.5), // Active
        activation
    );

    return color * node;
}

void main() {
    vec2 uv = gl_FragCoord.xy / u_resolution.xy;
    uv = uv * 2.0 - 1.0; // Normalize to [-1, 1]
    uv.x *= u_resolution.x / u_resolution.y; // Correct aspect ratio

    vec3 finalColor = vec3(0.0);

    // Draw connections
    int connectionIndex = 0;
    for(int i = 0; i < NODE_COUNT; i++) {
        for(int j = 0; j < NODE_COUNT; j++) {
            if(connections[connectionIndex]) {
                float signalOffset = float(i + j) * 0.1;
                finalColor += drawConnection(uv, nodePositions[i], nodePositions[j], signalOffset);
            }
            connectionIndex++;
        }
    }

    // Draw nodes with activation
    for(int i = 0; i < NODE_COUNT; i++) {
        float activation = sin(u_time * 0.5 + float(i) * 0.3) * 0.5 + 0.5;
        finalColor += drawNode(uv, nodePositions[i], activation);
    }

    // Add subtle background glow
    float glow = length(uv) * 0.1;
    finalColor += vec3(0.1, 0.1, 0.2) * (1.0 - glow);

    fragColor = vec4(finalColor, 0.8);
}
