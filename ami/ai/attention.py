""" AI Attention mechinism. Threaded Async event loop with logging and safe shutdown features. """
import asyncio
from threading import Thread
from typing import Coroutine, Any

from gunicorn.app.base import traceback

from ami.base import Base

class Attention(Base):
    """
    Manages an asynchronous task queue in a thread.

    This class allows scheduling of coroutines to be run asynchronously
    in a dedicated thread, providing a way to handle background tasks.
    """

    def __init__(self, worker_timeout: float=1.0, ignore_coroname_logging: list=[]):
        """
        Initialize an instance of Attention.

        Args:
            worker_timeout (float, optional): The timeout value in seconds for the worker thread.
                Defaults to 1.0.
            ignore_coroname_logging (list, optional): List of coro names to ignore logging for.
                Defaults to an empty list.

        Attributes:
            ignore_coroname_scheduling (list): A list of coro names to ignore logging for.
            queue (asyncio.Queue): An asynchronous queue for storing tasks.
            loop (asyncio.AbstractEventLoop): The event loop used for asynchronous operations.
            thread (Thread or None): Internal thread responsible for executing tasks from the queue.
            worker_timeout (float): The timeout value in seconds for the worker thread.
            shutdown_event (asyncio.Event): An event used to signal the worker thread to shut down.
        """
        super().__init__()
        self.ignore_coroname_scheduling = ignore_coroname_logging
        self.queue: asyncio.Queue = asyncio.Queue()
        self.loop: asyncio.AbstractEventLoop = asyncio.new_event_loop()
        self.thread: Thread | None = None
        self.worker_timeout: float = worker_timeout
        self.shutdown_event: asyncio.Event = asyncio.Event()

    async def worker(self) -> None:
        """Main worker coroutine that processes tasks from the queue."""
        while not self.shutdown_event.is_set():
            try:
                coro = await asyncio.wait_for(self.queue.get(), timeout=self.worker_timeout)
                await coro
                self.queue.task_done()
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                error_msg = f"Error in worker: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
                self.logs.critical(f"Error in worker: {error_msg}")

    def start(self) -> None:
        """Start the attention thread if it's not already running."""
        if self.thread is not None:
            return
        self.shutdown_event.clear()
        self.thread = Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        self.logs.info("Attention Thread started.")

    def stop(self) -> None:
        """Stop the attention thread and wait for it to finish."""
        if not self.thread:
            return
        self.logs.info("Stopping Attention Thread...")
        self.loop.call_soon_threadsafe(self.shutdown_event.set)
        self.thread.join()
        self.thread = None
        self.logs.info("Attention Thread stopped.")

    def _run_loop(self) -> None:
        """Run the event loop in the separate thread."""
        asyncio.set_event_loop(self.loop)
        self.logs.info("Attention event loop started.")
        try:
            self.loop.run_until_complete(self.worker())
        finally:
            self._cleanup_loop()

    def _cleanup_loop(self) -> None:
        """Clean up any remaining tasks and close the loop."""
        pending = asyncio.all_tasks(self.loop)
        for task in pending:
            task.cancel()
        self.loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        self.loop.close()
        self.logs.info("Attention event loop closed.")

    def schedule(self, coro: Coroutine[Any, Any, Any]) -> None:
        """
        Schedule a coroutine to be run by the worker.

        :param coro: The coroutine to be scheduled.
        """
        if self.shutdown_event.is_set():
            self.logs.warn(f"Attention is in a shutdown state. Cannot schedule `{coro.__name__}`. Cancelling coroutine.")
            coro.close()
        else:
            if coro.__name__ not in self.ignore_coroname_scheduling:
                self.logs.info(f"Attention.scheduled job: {coro}")
            asyncio.run_coroutine_threadsafe(self.queue.put(coro), self.loop)
