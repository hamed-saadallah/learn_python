import logging
import json
import time
from datetime import datetime
from functools import wraps
from typing import Any, Callable
from config import settings


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)

        return json.dumps(log_data)


def setup_logger(name: str) -> logging.Logger:
    """Setup and return a configured logger instance."""
    logger = logging.getLogger(name)
    logger.setLevel(settings.log_level)

    if not logger.handlers:
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(settings.log_level)

        formatter = JSONFormatter()
        console_handler.setFormatter(formatter)

        logger.addHandler(console_handler)

    return logger


def log_execution(logger: logging.Logger) -> Callable:
    """Decorator to log function execution with timing and error handling."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            func_name = func.__name__
            start_time = time.time()

            try:
                logger.info(
                    f"Starting execution of {func_name}",
                    extra={"extra_data": {"function": func_name, "args_count": len(args)}},
                )
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                logger.info(
                    f"Completed execution of {func_name}",
                    extra={
                        "extra_data": {
                            "function": func_name,
                            "duration_seconds": duration,
                            "status": "success",
                        }
                    },
                )
                return result

            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"Error in {func_name}: {str(e)}",
                    exc_info=True,
                    extra={
                        "extra_data": {
                            "function": func_name,
                            "duration_seconds": duration,
                            "status": "error",
                            "error_type": type(e).__name__,
                        }
                    },
                )
                raise

        return wrapper

    return decorator


# Global logger instance
logger = setup_logger(__name__)
