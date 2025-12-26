"""
Connection and error handling utilities for async operations.

Provides decorators and context managers for:
- Handling socket/connection errors
- Retry logic with exponential backoff
- Timeout handling
- Graceful degradation
- AsyncIO socket shutdown error suppression
"""

import asyncio
import logging
import socket
from functools import wraps
from typing import Any, Callable, Optional, TypeVar, Union

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


class ConnectionError(Exception):
    """Raised when a connection-related error occurs."""
    pass


class TimeoutError(Exception):
    """Raised when an operation times out."""
    pass


def handle_connection_errors(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    timeout: Optional[float] = None,
):
    """
    Decorator to handle connection errors with retry logic and exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay between retries (seconds)
        backoff_factor: Multiplier for delay between retries
        timeout: Timeout for the operation (seconds)
    
    Example:
        @handle_connection_errors(max_retries=3, timeout=30)
        async def fetch_data():
            # Your async operation
            pass
    """
    def decorator(func: F) -> F:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    if timeout:
                        return await asyncio.wait_for(
                            func(*args, **kwargs),
                            timeout=timeout
                        )
                    else:
                        return await func(*args, **kwargs)
                        
                except asyncio.TimeoutError as e:
                    last_exception = e
                    logger.warning(
                        f"[{func.__name__}] Timeout on attempt {attempt + 1}/{max_retries + 1}"
                    )
                    if attempt < max_retries:
                        await asyncio.sleep(delay)
                        delay *= backoff_factor
                    else:
                        logger.error(
                            f"[{func.__name__}] All {max_retries + 1} attempts failed with timeout"
                        )
                        raise TimeoutError(
                            f"Operation timed out after {max_retries + 1} attempts"
                        ) from e
                        
                except ConnectionResetError as e:
                    last_exception = e
                    logger.warning(
                        f"[{func.__name__}] Connection reset on attempt {attempt + 1}/{max_retries + 1}"
                    )
                    if attempt < max_retries:
                        await asyncio.sleep(delay)
                        delay *= backoff_factor
                    else:
                        logger.error(
                            f"[{func.__name__}] Connection closed by remote host after {max_retries + 1} attempts"
                        )
                        raise ConnectionError(
                            "Connection was closed by the remote host"
                        ) from e
                        
                except (ConnectionAbortedError, ConnectionRefusedError, BrokenPipeError) as e:
                    last_exception = e
                    logger.warning(
                        f"[{func.__name__}] Connection error on attempt {attempt + 1}/{max_retries + 1}: {type(e).__name__}"
                    )
                    if attempt < max_retries:
                        await asyncio.sleep(delay)
                        delay *= backoff_factor
                    else:
                        logger.error(
                            f"[{func.__name__}] Connection failed after {max_retries + 1} attempts"
                        )
                        raise ConnectionError(f"Connection failed: {e}") from e
                        
                except Exception as e:
                    # Don't retry on non-connection errors
                    logger.error(f"[{func.__name__}] Non-recoverable error: {e}")
                    raise
            
            # Should not reach here, but just in case
            if last_exception:
                raise last_exception
                
        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            # For sync functions, just execute without retry
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"[{func.__name__}] Sync operation failed: {e}")
                raise
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        else:
            return sync_wrapper  # type: ignore
    
    return decorator


async def handle_socket_read(
    reader: asyncio.StreamReader,
    size: int = 100,
    timeout: float = 30.0,
) -> bytes:
    """
    Safely read from a socket with error handling.
    
    Args:
        reader: AsyncIO StreamReader
        size: Number of bytes to read
        timeout: Read timeout in seconds
    
    Returns:
        Bytes read from socket
        
    Raises:
        ConnectionError: If connection is closed or reset
        TimeoutError: If operation times out
    """
    try:
        data = await asyncio.wait_for(
            reader.read(size),
            timeout=timeout
        )
        if not data:
            raise ConnectionError("Connection closed by remote host (empty read)")
        return data
    except asyncio.TimeoutError as e:
        logger.error(f"Socket read timeout after {timeout} seconds")
        raise TimeoutError(f"Socket read timeout after {timeout} seconds") from e
    except ConnectionResetError as e:
        logger.error("Connection was reset by remote host")
        raise ConnectionError("Connection was reset by remote host") from e
    except Exception as e:
        logger.error(f"Socket read error: {e}")
        raise


async def handle_socket_write(
    writer: asyncio.StreamWriter,
    data: bytes,
    timeout: float = 30.0,
) -> None:
    """
    Safely write to a socket with error handling.
    
    Args:
        writer: AsyncIO StreamWriter
        data: Data to write
        timeout: Write timeout in seconds
        
    Raises:
        ConnectionError: If connection is closed
        TimeoutError: If operation times out
    """
    try:
        writer.write(data)
        await asyncio.wait_for(
            writer.drain(),
            timeout=timeout
        )
    except asyncio.TimeoutError as e:
        logger.error(f"Socket write timeout after {timeout} seconds")
        raise TimeoutError(f"Socket write timeout after {timeout} seconds") from e
    except ConnectionResetError as e:
        logger.error("Connection was reset by remote host during write")
        raise ConnectionError("Connection was reset by remote host") from e
    except BrokenPipeError as e:
        logger.error("Pipe broken - connection closed")
        raise ConnectionError("Connection closed") from e
    except Exception as e:
        logger.error(f"Socket write error: {e}")
        raise


class AsyncContextRetry:
    """
    Context manager for async operations with retry logic.
    
    Example:
        async with AsyncContextRetry(max_retries=3) as ctx:
            await some_operation()
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        backoff_factor: float = 2.0,
    ):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.backoff_factor = backoff_factor
        self.attempt = 0
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            return False
            
        # Handle connection-related exceptions
        connection_errors = (
            ConnectionResetError,
            ConnectionAbortedError,
            ConnectionRefusedError,
            BrokenPipeError,
        )
        
        if isinstance(exc_val, connection_errors) or isinstance(exc_val, asyncio.TimeoutError):
            if self.attempt < self.max_retries:
                delay = self.initial_delay * (self.backoff_factor ** self.attempt)
                logger.warning(
                    f"Connection error on attempt {self.attempt + 1}, retrying in {delay}s: {exc_val}"
                )
                await asyncio.sleep(delay)
                self.attempt += 1
                return True  # Suppress exception to retry
            else:
                logger.error(f"All {self.max_retries + 1} retry attempts exhausted")
                return False  # Re-raise exception
        
        return False  # Re-raise non-connection errors


def suppress_asyncio_socket_shutdown_errors() -> None:
    """
    Suppress expected ConnectionResetError exceptions that occur during asyncio socket shutdown.
    
    These errors are harmless and occur when:
    1. Clients disconnect during streaming (206 Partial Content responses)
    2. AsyncIO attempts to shutdown the socket with socket.SHUT_RDWR
    3. The socket is already closed by the remote host
    
    This reduces log noise while maintaining error handling for actual connection issues.
    
    Usage:
        In your FastAPI app initialization:
        
        from src.utils.error_handlers import suppress_asyncio_socket_shutdown_errors
        
        suppress_asyncio_socket_shutdown_errors()
    
    Reference:
        This handles errors like:
        Exception in callback _ProactorBasePipeTransport._call_connection_lost(None)
        ConnectionResetError: [WinError 10054] An existing connection was forcibly closed by the remote host
    """
    
    def handle_exception(loop, context: dict) -> None:
        """
        Custom exception handler for asyncio event loop.
        
        Suppresses harmless socket shutdown errors while logging other exceptions.
        """
        exception = context.get("exception")
        
        # Suppress expected socket shutdown errors
        if isinstance(exception, ConnectionResetError):
            # Check if this is a socket shutdown error
            error_msg = str(exception).lower()
            if any(x in error_msg for x in [
                "connection was forcibly closed",
                "connection reset by peer",
                "winerror 10054",
                "shutdown"
            ]):
                # This is a harmless socket shutdown error - suppress it
                logger.debug(
                    f"[AsyncIO] Suppressed socket shutdown error (client disconnected): {exception}"
                )
                return
        
        # Suppress BrokenPipeError during socket shutdown (Windows)
        if isinstance(exception, BrokenPipeError):
            logger.debug(f"[AsyncIO] Suppressed broken pipe error during shutdown: {exception}")
            return
        
        # Log other exceptions normally (but not as ERROR to avoid noise)
        # These might be harmless connection issues during streaming
        if "transport" in str(context).lower() or "connection" in str(context).lower():
            logger.debug(f"[AsyncIO] Transport/connection event: {context}")
        else:
            logger.warning(f"[AsyncIO] Uncaught exception in event loop: {context}", exc_info=exception)
    
    # Set the custom exception handler on the running loop
    try:
        loop = asyncio.get_running_loop()
        loop.set_exception_handler(handle_exception)
        logger.info("[AsyncIO] Socket shutdown error suppression enabled")
    except RuntimeError:
        # No running loop yet, try to get the event loop
        try:
            loop = asyncio.get_event_loop()
            loop.set_exception_handler(handle_exception)
            logger.info("[AsyncIO] Socket shutdown error suppression enabled (on default loop)")
        except Exception as e:
            logger.warning(f"[AsyncIO] Could not set exception handler: {e}")
