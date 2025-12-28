"""Unit tests for error handlers."""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch

from src.utils.error_handlers import (
    handle_connection_errors,
    handle_socket_read,
    handle_socket_write,
    AsyncContextRetry,
    suppress_asyncio_socket_shutdown_errors,
    ConnectionError,
    TimeoutError,
)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_handle_connection_errors_success():
    """Test decorator with successful operation."""
    @handle_connection_errors(max_retries=2, timeout=30)
    async def test_func():
        return "success"
    
    result = await test_func()
    assert result == "success"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_handle_connection_errors_timeout_retry():
    """Test decorator retries on timeout."""
    call_count = 0
    
    @handle_connection_errors(max_retries=2, timeout=30)
    async def test_func():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise asyncio.TimeoutError("Timeout")
        return "success"
    
    result = await test_func()
    assert result == "success"
    assert call_count == 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_handle_connection_errors_connection_reset():
    """Test decorator retries on ConnectionResetError."""
    call_count = 0
    
    @handle_connection_errors(max_retries=2)
    async def test_func():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise ConnectionResetError("Reset")
        return "success"
    
    result = await test_func()
    assert result == "success"
    assert call_count == 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_handle_connection_errors_max_retries_exceeded():
    """Test decorator raises after max retries."""
    @handle_connection_errors(max_retries=1)
    async def test_func():
        raise ConnectionResetError("Reset")
    
    with pytest.raises(ConnectionError):
        await test_func()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_handle_connection_errors_connection_refused():
    """Test decorator handles ConnectionRefusedError."""
    call_count = 0
    
    @handle_connection_errors(max_retries=1)
    async def test_func():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise ConnectionRefusedError("Refused")
        return "success"
    
    result = await test_func()
    assert result == "success"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_handle_connection_errors_non_connection_error():
    """Test decorator doesn't retry on non-connection errors."""
    @handle_connection_errors(max_retries=2)
    async def test_func():
        raise ValueError("Not a connection error")
    
    with pytest.raises(ValueError):
        await test_func()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_handle_socket_read_success():
    """Test successful socket read."""
    mock_reader = MagicMock()
    mock_reader.read = AsyncMock(return_value=b"test data")
    
    result = await handle_socket_read(mock_reader, size=100, timeout=30.0)
    
    assert result == b"test data"
    mock_reader.read.assert_called_once_with(100)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_handle_socket_read_empty():
    """Test socket read with empty data raises ConnectionError."""
    mock_reader = MagicMock()
    mock_reader.read = AsyncMock(return_value=b"")
    
    with pytest.raises(ConnectionError, match="closed"):
        await handle_socket_read(mock_reader, size=100, timeout=30.0)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_handle_socket_read_timeout():
    """Test socket read timeout."""
    mock_reader = MagicMock()
    mock_reader.read = AsyncMock(side_effect=asyncio.TimeoutError())
    
    with pytest.raises(TimeoutError, match="timeout"):
        await handle_socket_read(mock_reader, size=100, timeout=30.0)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_handle_socket_read_connection_reset():
    """Test socket read with connection reset."""
    mock_reader = MagicMock()
    mock_reader.read = AsyncMock(side_effect=ConnectionResetError("Reset"))
    
    with pytest.raises(ConnectionError, match="reset"):
        await handle_socket_read(mock_reader, size=100, timeout=30.0)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_handle_socket_write_success():
    """Test successful socket write."""
    mock_writer = MagicMock()
    mock_writer.write = MagicMock()
    mock_writer.drain = AsyncMock()
    
    await handle_socket_write(mock_writer, b"test data", timeout=30.0)
    
    mock_writer.write.assert_called_once_with(b"test data")
    mock_writer.drain.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_handle_socket_write_timeout():
    """Test socket write timeout."""
    mock_writer = MagicMock()
    mock_writer.write = MagicMock()
    mock_writer.drain = AsyncMock(side_effect=asyncio.TimeoutError())
    
    with pytest.raises(TimeoutError, match="timeout"):
        await handle_socket_write(mock_writer, b"test data", timeout=30.0)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_handle_socket_write_connection_reset():
    """Test socket write with connection reset."""
    mock_writer = MagicMock()
    mock_writer.write = MagicMock()
    mock_writer.drain = AsyncMock(side_effect=ConnectionResetError("Reset"))
    
    with pytest.raises(ConnectionError, match="reset"):
        await handle_socket_write(mock_writer, b"test data", timeout=30.0)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_handle_socket_write_broken_pipe():
    """Test socket write with broken pipe."""
    mock_writer = MagicMock()
    mock_writer.write = MagicMock()
    mock_writer.drain = AsyncMock(side_effect=BrokenPipeError("Broken"))
    
    with pytest.raises(ConnectionError, match="closed"):
        await handle_socket_write(mock_writer, b"test data", timeout=30.0)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_async_context_retry_success():
    """Test AsyncContextRetry with successful operation."""
    retry = AsyncContextRetry(max_retries=2)
    
    async with retry:
        result = "success"
    
    assert result == "success"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_async_context_retry_retries_on_connection_error():
    """Test AsyncContextRetry suppresses exception to allow retries."""
    # Note: AsyncContextRetry suppresses exceptions when attempt < max_retries
    # This allows the caller to retry the operation in a loop
    retry = AsyncContextRetry(max_retries=2, initial_delay=0.01)
    
    # Test that exception is suppressed on first attempt (attempt starts at 0, max_retries=2)
    exception_suppressed = False
    try:
        async with retry:
            raise ConnectionResetError("Reset")
        # If we get here, exception was suppressed
        exception_suppressed = True
    except ConnectionResetError:
        # Exception was not suppressed
        pass
    
    # Exception should be suppressed when attempt (0) < max_retries (2)
    assert exception_suppressed
    assert retry.attempt == 1  # Attempt counter should be incremented


@pytest.mark.unit
@pytest.mark.asyncio
async def test_async_context_retry_max_retries():
    """Test AsyncContextRetry doesn't suppress after max retries."""
    # Note: AsyncContextRetry suppresses exceptions when attempt < max_retries
    # When attempt >= max_retries, it returns False (doesn't suppress), so exception propagates
    retry = AsyncContextRetry(max_retries=1, initial_delay=0.01)
    retry.attempt = 1  # Set to max_retries to test non-suppression
    
    exception_raised = False
    try:
        async with retry:
            raise ConnectionResetError("Reset")
    except ConnectionResetError:
        exception_raised = True
    
    # When attempt >= max_retries, exception should propagate (not suppressed)
    assert exception_raised


@pytest.mark.unit
@pytest.mark.asyncio
async def test_async_context_retry_timeout_error():
    """Test AsyncContextRetry suppresses timeout errors."""
    retry = AsyncContextRetry(max_retries=2, initial_delay=0.01)
    
    # Test that timeout exception is suppressed
    exception_suppressed = False
    try:
        async with retry:
            raise asyncio.TimeoutError()
        exception_suppressed = True
    except asyncio.TimeoutError:
        pass
    
    # Exception should be suppressed when attempt < max_retries
    assert exception_suppressed
    assert retry.attempt == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_async_context_retry_non_connection_error():
    """Test AsyncContextRetry doesn't retry non-connection errors."""
    retry = AsyncContextRetry(max_retries=2)
    
    with pytest.raises(ValueError):
        async with retry:
            raise ValueError("Not retryable")


@pytest.mark.unit
def test_suppress_asyncio_socket_shutdown_errors():
    """Test suppress_asyncio_socket_shutdown_errors sets exception handler."""
    with patch('asyncio.get_running_loop') as mock_get_loop:
        mock_loop = MagicMock()
        mock_get_loop.return_value = mock_loop
        
        suppress_asyncio_socket_shutdown_errors()
        
        mock_loop.set_exception_handler.assert_called_once()


@pytest.mark.unit
def test_suppress_asyncio_socket_shutdown_errors_no_running_loop():
    """Test suppress_asyncio_socket_shutdown_errors handles no running loop."""
    with patch('asyncio.get_running_loop', side_effect=RuntimeError("No loop")):
        with patch('asyncio.get_event_loop') as mock_get_event_loop:
            mock_loop = MagicMock()
            mock_get_event_loop.return_value = mock_loop
            
            suppress_asyncio_socket_shutdown_errors()
            
            mock_loop.set_exception_handler.assert_called_once()


@pytest.mark.unit
def test_suppress_asyncio_socket_shutdown_errors_no_event_loop():
    """Test suppress_asyncio_socket_shutdown_errors handles no event loop."""
    with patch('asyncio.get_running_loop', side_effect=RuntimeError("No loop")):
        with patch('asyncio.get_event_loop', side_effect=Exception("No event loop")):
            # Should not raise, just log warning
            suppress_asyncio_socket_shutdown_errors()


@pytest.mark.unit
def test_connection_error_exception():
    """Test ConnectionError exception class."""
    error = ConnectionError("Test error")
    assert str(error) == "Test error"


@pytest.mark.unit
def test_timeout_error_exception():
    """Test TimeoutError exception class."""
    error = TimeoutError("Test timeout")
    assert str(error) == "Test timeout"


@pytest.mark.unit
def test_handle_connection_errors_sync_function():
    """Test decorator works with sync functions."""
    @handle_connection_errors(max_retries=2)
    def sync_func():
        return "sync success"
    
    result = sync_func()
    assert result == "sync success"


@pytest.mark.unit
def test_handle_connection_errors_sync_function_error():
    """Test decorator with sync function that raises."""
    @handle_connection_errors(max_retries=2)
    def sync_func():
        raise ValueError("Sync error")
    
    with pytest.raises(ValueError):
        sync_func()

