# Backend Component Documentation

## Directory Structure

```
backend/                           # FastAPI-based Backend Component
├── __init__.py                   # Package initialization
├── main.py                       # Main application and server management
├── markdown_api.py               # Markdown file management API
├── log_api.py                    # Log access and management API
└── settings_api.py               # System settings management API
```

## Architecture

**FastAPI-based Backend with Modular API Components**

The backend component is built using FastAPI and follows a modular architecture with the following key aspects:

### Core Components

1. **Main Application (`main.py`)**
   - Application factory and configuration
   - Component mounting and management
   - Server runtime configuration
   - Health check endpoints
   - Process management utilities

2. **Markdown API (`markdown_api.py`)**
   - File management operations
   - Content storage and retrieval
   - File metadata handling
   - Attachment management

3. **Log API (`log_api.py`)**
   - Log entry access and filtering
   - Log source management
   - Log level filtering
   - Log export functionality

4. **Settings API (`settings_api.py`)**
   - System settings management
   - Configuration persistence
   - Setting validation
   - Import/export functionality

## State and Data Flow

1. **Application State**
   - Component-level state isolation
   - Shared configuration management
   - Runtime state monitoring
   - Health status tracking

2. **Data Management**
   - File system interactions
   - Log aggregation and storage
   - Settings persistence
   - Cache management

3. **API Communication**
   - RESTful endpoint handling
   - CORS configuration
   - Error propagation
   - Response formatting

## Process Management

The backend can operate in multiple modes:

1. **Subprocess Mode**
   ```python
   from ami.backend.main import run_server
   run_server(port=58744)
   ```

2. **Main Process Mode**
   ```bash
   python -m ami.backend.main --port 58744
   ```

3. **Component Testing**
   ```python
   from ami.backend.main import create_app
   app = create_app(enable_markdown=True, enable_logs=False)
   ```

## Configuration Options

### Server Configuration
- Host binding (default: 0.0.0.0)
- Port selection (default: 58744)
- Auto-reload for development
- Component enabling/disabling
- Log level selection

### Component-specific Settings
- Markdown file storage location
- Log retention policies
- Settings persistence path
- CORS configuration

## Development Guidelines

1. **API Development**
   - Follow RESTful principles
   - Implement proper validation
   - Document all endpoints
   - Handle errors gracefully

2. **Testing Strategy**
   - Unit tests per component
   - Integration tests for APIs
   - Performance testing
   - Load testing

3. **Performance Considerations**
   - Async operations for I/O
   - Proper resource cleanup
   - Connection pooling
   - Response caching

## Error Handling

Comprehensive error handling across all components:
- Input validation
- File system operations
- Configuration errors
- Runtime exceptions
- Client communication errors

## Security Considerations

1. **API Security**
   - CORS configuration
   - Input sanitization
   - Resource access control
   - Error message safety

2. **File Operations**
   - Path traversal prevention
   - File type validation
   - Size limitations
   - Permission management

## Integration Points

1. **Frontend Integration**
   - RESTful API endpoints
   - Real-time updates
   - Error handling
   - State synchronization

2. **AI Service Integration**
   - gRPC client functionality
   - State propagation
   - Error handling
   - Service discovery

## Usage Examples

1. **Running the Full Server**
   ```bash
   python -m ami.backend.main
   ```

2. **Running with Specific Components**
   ```bash
   python -m ami.backend.main --no-logs --port 58744
   ```

3. **Development Mode**
   ```bash
   python -m ami.backend.main --reload --log-level debug
   ```

4. **Programmatic Usage**
   ```python
   from ami.backend.main import create_app, run_server
   
   # Create custom app instance
   app = create_app(enable_markdown=True, enable_logs=True)
   
   # Run server with custom configuration
   run_server(port=58744, reload=True)
   ```