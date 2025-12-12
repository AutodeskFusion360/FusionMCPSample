"""
Task Manager Module

This module provides a TaskManager class for handling custom events and task execution
within the Fusion 360 environment.
"""

import json
import uuid
from typing import Dict, Callable, Any, Optional

try:
    import adsk.core
    app = adsk.core.Application.get()
except ImportError:
    app = None


class TaskManager:
    """
    TaskManager class for handling custom events and task execution.

    Provides a mechanism to post tasks with callbacks that will be executed
    when custom events are fired in the Fusion 360 environment.
    Acts as a singleton with class methods for global access.
    """

    _instance = None
    _event_handler = None
    _custom_event = None
    _pending_tasks: Dict[str, Dict[str, Any]] = {}
    _is_running = False

    def __new__(cls):
        """Ensure only one instance exists (singleton pattern)."""
        if cls._instance is None:
            cls._instance = super(TaskManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the TaskManager (only called once due to singleton)."""
        # Only initialize if not already initialized
        if not hasattr(self, '_initialized'):
            self._event_handler = None
            self._custom_event = None
            self._pending_tasks = {}
            self._is_running = False
            self._initialized = True

    @classmethod
    def start(cls) -> bool:
        """
        Start the TaskManager by registering a custom event and handler.

        Returns:
            True if started successfully, False otherwise
        """
        if not app:
            print("TaskManager: Fusion 360 application not available")
            return False

        if cls._is_running:
            print("TaskManager: Already running")
            return True

        try:
            # Create custom event using the Application API
            cls._custom_event = app.registerCustomEvent('Fusion MCP Addin.TaskManagerEvent')

            # Create and register event handler
            cls._event_handler = TaskEventHandler(cls._pending_tasks)
            cls._custom_event.add(cls._event_handler)

            cls._is_running = True
            if app:
                app.log("TaskManager: Started successfully")
            return True

        except Exception as e:
            print(f"TaskManager: Failed to start - {str(e)}")
            if app:
                app.log(f"TaskManager: Failed to start - {str(e)}")
            return False

    @classmethod
    def stop(cls) -> bool:
        """
        Stop the TaskManager by removing the event handler.

        Returns:
            True if stopped successfully, False otherwise
        """
        if not cls._is_running:
            print("TaskManager: Not running")
            return True

        try:
            if cls._custom_event and cls._event_handler:
                cls._custom_event.remove(cls._event_handler)
                cls._event_handler = None
                cls._custom_event = None

            # Clear any pending tasks
            cls._pending_tasks.clear()
            cls._is_running = False

            if app:
                app.log("TaskManager: Stopped successfully")
            return True

        except Exception as e:
            print(f"TaskManager: Failed to stop - {str(e)}")
            if app:
                app.log(f"TaskManager: Failed to stop - {str(e)}")
            return False

    @classmethod
    def post(cls, command: str, callback: Callable[[Dict[str, Any]], None], data: Dict[str, Any]) -> Optional[str]:
        """
        Post a task with a callback to be executed when the custom event is fired.

        Args:
            command: Command string to identify the task type
            callback: Callable function to execute with the data
            data: Dictionary containing task data

        Returns:
            Task ID if posted successfully, None otherwise
        """
        if not cls._is_running:
            print("TaskManager: Not running, cannot post task")
            return None

        if not callable(callback):
            print("TaskManager: Callback must be callable")
            return None

        try:
            # Generate unique task ID
            task_id = str(uuid.uuid4())

            # Store task information
            cls._pending_tasks[task_id] = {
                'command': command,
                'callback': callback,
                'data': data
            }

            # Create event data
            event_data = {
                'task_id': task_id,
                'command': command,
                'data': data
            }

            # Fire the custom event
            app.fireCustomEvent(cls._custom_event.eventId, json.dumps(event_data))

            app.log(f"TaskManager: Posted task {task_id} with command '{command}'")

            return task_id

        except Exception as e:
            print(f"TaskManager: Failed to post task - {str(e)}")
            app.log(f"TaskManager: Failed to post task - {str(e)}")
            return None

    @classmethod
    def is_running(cls) -> bool:
        """
        Check if the TaskManager is currently running.

        Returns:
            True if running, False otherwise
        """
        return cls._is_running

    @classmethod
    def get_pending_task_count(cls) -> int:
        """
        Get the number of pending tasks.

        Returns:
            Number of pending tasks
        """
        return len(cls._pending_tasks)


class TaskEventHandler(adsk.core.CustomEventHandler):
    """
    Event handler for TaskManager custom events.

    Handles the execution of callbacks when custom events are received.
    """

    def __init__(self, pending_tasks: Dict[str, Dict[str, Any]]):
        """
        Initialize the TaskEventHandler.

        Args:
            pending_tasks: Dictionary of pending tasks to manage
        """
        super().__init__()
        self._pending_tasks = pending_tasks

    def notify(self, args: adsk.core.CustomEventArgs):
        """
        Handle the custom event notification.

        Args:
            args: Custom event arguments containing the event data
        """
        try:
            # Parse the event data
            event_data = json.loads(args.additionalInfo)
            task_id = event_data.get('task_id')
            command = event_data.get('command')
            data = event_data.get('data', {})

            if not task_id or task_id not in self._pending_tasks:
                if app:
                    app.log(f"TaskManager: Unknown task ID {task_id}")
                return

            # Get task information
            task_info = self._pending_tasks[task_id]
            callback = task_info['callback']

            # Execute the callback with the data
            try:
                callback(data)
                if app:
                    app.log(f"TaskManager: Executed task {task_id} with command '{command}'")
            except Exception as callback_error:
                print(f"TaskManager: Callback error for task {task_id}: {str(callback_error)}")
                if app:
                    app.log(f"TaskManager: Callback error for task {task_id}: {str(callback_error)}")

            # Remove the completed task
            del self._pending_tasks[task_id]

        except json.JSONDecodeError as e:
            print(f"TaskManager: Failed to parse event data: {str(e)}")
            if app:
                app.log(f"TaskManager: Failed to parse event data: {str(e)}")
        except Exception as e:
            print(f"TaskManager: Event handler error: {str(e)}")
            if app:
                app.log(f"TaskManager: Event handler error: {str(e)}")


def start_task_manager() -> bool:
    """
    Start the TaskManager singleton.

    Returns:
        True if started successfully, False otherwise
    """
    return TaskManager.start()


def stop_task_manager() -> bool:
    """
    Stop the TaskManager singleton.

    Returns:
        True if stopped successfully, False otherwise
    """
    return TaskManager.stop()