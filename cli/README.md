
# AMI Command Line Interface

## Architecture Overview
The AMI CLI is a binary to manage AMI system level commands.

## Build Pipeline

### Compilation Process

The C binary is compiled using GCC with the following flags:
- `-DSOURCE_DIR`: Compile-time constant for the project root directory

```bash
gcc -Wall -Wextra -o cli/ami cli/main.c -DSOURCE_DIR="$(pwd)"

gcc -Wall -g -Iinclude -c src/main.c -o src/main.o
gcc -Wall -g -Iinclude -c src/commands.c -o src/commands.o
gcc -Wall -g -Iinclude -c src/utils.c -o src/utils.o
gcc -Wall -g -Iinclude -c src/api.c -o src/api.o
gcc -Wall -g -Iinclude -c src/config.c -o src/config.o
gcc -Wall -g -Iinclude -c src/error.c -o src/error.o
gcc src/main.o src/commands.o src/utils.o src/api.o src/config.o src/error.o -o ami -lcurl
```

### Installation Pipeline
*Makefile located at the root of this repo*
1. **Compile**: `make cli` compiles the C binary
2. **Install**: `make install` performs full installation:
   - Syncs UV environment
   - Compiles CLI binary
   - Copies binary to `~/.local/bin/ami`

### Build Dependencies

- **GCC**: C compiler
- **Make**: Build system
- **UV**: Python package manager (for Python CLI components)

## Command Structure

### C Binary Commands (`cli/main.c`)

#### Core Operations
- `ami run`: Execute the main Python application
- `ami update`: Update source repository to latest tag and run tests
- `ami gethead <user>/<repo>`: Download headspace plugins from GitHub

#### Autostart Management
- `ami autostart enable`: Create systemd user service for auto-startup
- `ami autostart disable`: Stop and disable systemd service

#### Plugin Management (Delegated)
- `ami plugin list`: List the Plugin name and its status
- `ami plugin enable <name>`: Disable the Plugin at the `~/.ami/ami_config.yaml` level
- `ami plugin disable <name>`: Enable the Plugin at the `~/.ami/ami_config.yaml` level

## Technical Implementation Details

### C Binary Specifics

#### Memory Management
- Dynamic allocation for command strings with proper cleanup
- Buffer overflow protection with `snprintf()`
- Error handling for failed allocations

#### Repository Validation
```c
int is_valid_repo(const char *repo) {
    // Validates user/repo format
    // Checks for single slash separator
    // Validates alphanumeric characters, hyphens, underscores
}
```

#### Systemd Integration
- Creates `~/.config/systemd/user/ami.service`
- Configures automatic restart with 10-second delay
- Sets proper environment variables and working directory

#### Configuration Management
- Reads/writes YAML configuration files
- Updates `enabled_headspaces` list
- Maintains plugin state persistence

## File Locations

### Build Artifacts
- `cli/ami`: Compiled C binary
- `~/.local/bin/ami`: Installed binary location

### Configuration Files
- `config_template.yaml`: Default configuration template
- `~/.ami/config.yaml`: User configuration
- `~/.config/systemd/user/ami.service`: Systemd service file

### Plugin Storage
- `~/.ami/plugins/`: Downloaded headspace plugins

## Error Handling

### C Binary
- Exit codes: 0 (success), 1 (failure)
- Stderr output for error messages
- Validation for repository formats and environment variables

## Performance Considerations

### C Binary Advantages
- Fast startup time (~1ms vs ~100ms for Python)
- Minimal memory footprint
- No dependency loading overhead

## Testing Framework

### Test Structure

```
tests/cli/
├── __init__.py
├── test_c_cli.py          # C binary functionality tests
└── test_python_cli.py     # Python CLI functionality tests

cli/
└── test_cli.py           # Test runner script
```

### Running Tests

**Single Command Test Execution:**
```bash
python cli/test_cli.py
```

This command will:
1. Compile the C binary if not present
2. Run all CLI unit tests
3. Run integration tests
4. Generate coverage reports

**Manual Test Execution:**
```bash
# Run specific test files
uv run pytest tests/cli/test_c_cli.py -v
uv run pytest tests/cli/test_python_cli.py -v

# Run with coverage
uv run pytest tests/cli/ --cov=ami.cli --cov-report=term-missing
```

### Test Categories

#### Unit Tests (`test_python_cli.py`)
- **AMICLIManager**: Plugin management operations
- **Configuration**: YAML file manipulation
- **IPC Integration**: Inter-process communication
- **Error Handling**: Exception scenarios

#### Integration Tests (`test_c_cli.py`)  
- **Command Parsing**: Argument validation
- **Repository Validation**: GitHub repo format checking
- **System Integration**: File system operations
- **Process Delegation**: C to Python CLI handoff

#### Test Coverage Areas

1. **Command Line Parsing**
   - Argument validation
   - Flag handling (-v, --verbose)
   - Command delegation

2. **Plugin Management**
   - List/enable/disable operations
   - Configuration persistence
   - Status reporting

3. **Repository Operations**
   - GitHub clone functionality
   - Path validation
   - Error handling

4. **System Integration**
   - Systemd service management
   - Environment variable handling
   - File system operations

5. **Error Scenarios**
   - Missing dependencies
   - Invalid inputs
   - Network failures
   - Permission issues

### Mock Strategy

#### C Binary Testing
- Uses subprocess calls to test actual binary behavior
- Temporary directories for file system operations
- Environment variable manipulation for isolation

#### Python CLI Testing
- Mock objects for IPC and registry components
- Temporary configuration files
- Isolated test environments

### Continuous Integration

Tests are designed to run without external dependencies:
- No network calls required
- Temporary file cleanup
- Mock system services
- Cross-platform compatibility

### Test Data Management

#### Fixtures
- `temp_config`: Temporary YAML configuration files
- `cli_manager`: Isolated CLI manager instances
- `mock_environment`: Controlled environment variables

#### Test Isolation
- Each test runs in isolation
- No shared state between tests
- Automatic cleanup of temporary resources

## Security Considerations

- Input validation for repository names
- Path traversal protection
- Safe system command execution
- Environment variable sanitization
