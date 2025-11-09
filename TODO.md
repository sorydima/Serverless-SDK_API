# TODO: System Refactor and Enhancements for Serverless-SDK_API

## 1. Codebase Organizer
- [x] Create new directories: /core, /frontend, /backend, /infra, /ai, /docs, /mesh
- [x] Move rust/ to core/
- [x] Move synapse/ to backend/
- [x] Move platforms/ to frontend/
- [x] Move docker/contrib/scripts-dev/ to infra/
- [x] Move bridges/ai/ and bridges/blockchain/ to ai/
- [x] Move docs/ to docs/ (already there, but ensure)
- [x] Create mesh/ directory
- [ ] Update all import paths in Python/Rust files after moves
- [ ] Update Cargo.toml and pyproject.toml paths if needed

## 2. Platform Builder
- [x] Create platforms/android/ with build.gradle, AndroidManifest.xml, basic src/
- [x] Create platforms/auroraos/ with CMakeLists.txt, basic app files
- [x] Create platforms/harmonyos/ with CMakeLists.txt, basic app files

## 3. Cross-Compile Prompt
- [x] Create build/ directory
- [x] Add CMakeLists.txt for cross-platform builds with Yandex SDK and userver integration
- [x] Add flutter.yaml for Flutter builds on mobile/web platforms

## 4. System Refactor
- [x] Analyze backend/ (synapse) and core/ (rust) for mesh integration
- [x] Add mesh routing logic in mesh/ directory
- [x] Integrate userver (C++ backend) in core/ or backend/, ensuring compatibility
- [x] Update architecture docs in docs/

## 5. Quantum Core Prompt
- [x] Create ai/ai_quantum_core/ directory
- [x] Add Python module for graph-based ML training (e.g., using networkx or PyTorch)
- [ ] Add Rust bindings if needed for performance
- [ ] Integrate with existing AI bridges

## Followup Steps
- [x] Update dependencies in Cargo.toml/pyproject.toml for new modules
- [x] Test builds on added platforms
- [x] Update README.md and docs with new structure and features
- [x] Verify backward compatibility with Synapse features
