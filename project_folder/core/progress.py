import time
from datetime import datetime, timedelta
from rich.progress import (
    BarColumn,
    Progress,
    TaskID,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
    DownloadColumn,
    TimeElapsedColumn,
)
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

class ProgressTracker:
    """Manages Rich library integration for CLI feedback with ETA calculations."""

    def __init__(self):
        # Enhanced file progress with more detailed information
        self.file_progress = Progress(
            TextColumn("[bold blue]{task.fields[filename]}", justify="right"),
            BarColumn(bar_width=None),
            "[progress.percentage]{task.percentage:>3.1f}%",
            "•",
            DownloadColumn(),
            "•",
            TransferSpeedColumn(),
            "•",
            TimeRemainingColumn(),
        )
        
        # Enhanced overall progress with ETA
        self.overall_progress = Progress(
            TimeElapsedColumn(),
            BarColumn(bar_width=None),
            "[progress.percentage]{task.percentage:>3.1f}%",
            "•",
            TextColumn("{task.description}"),
            "•",
            TimeRemainingColumn(),
        )
        
        self.tasks = {}
        self.overall_task = self.overall_progress.add_task("Overall Progress", total=0)
        self.start_time = None
        self.total_files = 0
        self.completed_files = 0

        self.live = Live(self._create_layout())

    def _create_layout(self) -> Panel:
        """Creates the layout for the live display with ETA information."""
        layout = Table.grid()
        
        # Add ETA summary at the top
        eta_info = self._get_eta_summary()
        if eta_info:
            layout.add_row(Text(eta_info, style="bold yellow"))
            layout.add_row("")  # Empty row for spacing
        
        layout.add_row(self.overall_progress)
        layout.add_row(self.file_progress)
        
        return Panel(layout, title="[bold green]SharePoint Uploader - SSH Transfer[/bold green]")

    def _get_eta_summary(self) -> str:
        """Generate ETA summary information."""
        if not self.start_time:
            return ""
        
        try:
            elapsed = time.time() - self.start_time
            
            # Get overall progress
            overall_task = self.overall_progress.tasks[self.overall_task]
            if overall_task.total and overall_task.total > 0:
                progress_ratio = overall_task.completed / overall_task.total
                
                if progress_ratio > 0:
                    estimated_total_time = elapsed / progress_ratio
                    remaining_time = estimated_total_time - elapsed
                    
                    # Format remaining time
                    remaining_timedelta = timedelta(seconds=int(max(0, remaining_time)))
                    eta_time = datetime.now() + remaining_timedelta
                    
                    # Calculate transfer speed
                    speed_bps = overall_task.completed / elapsed if elapsed > 0 else 0
                    speed_mbps = speed_bps / (1024 * 1024)
                    
                    file_info = f"Files: {self.completed_files}/{self.total_files}" if self.total_files > 0 else ""
                    speed_info = f"Speed: {speed_mbps:.2f} MB/s"
                    eta_info = f"ETA: {eta_time.strftime('%H:%M:%S')} ({remaining_timedelta})"
                    
                    return f"📊 {file_info} • {speed_info} • {eta_info}"
        except Exception as e:
            # If ETA calculation fails, just return basic info
            return f"📊 Files: {self.completed_files}/{self.total_files}" if self.total_files > 0 else ""
        
        return ""

    def set_total_files(self, total: int):
        """Set the total number of files for better ETA calculation."""
        self.total_files = total

    def add_task(self, name: str, total_size: int, completed: int = 0) -> TaskID:
        """Adds a new task to the progress bar."""
        if self.start_time is None:
            self.start_time = time.time()
            
        task_id = self.file_progress.add_task(
            name, total=total_size, filename=name, start=completed > 0, completed=completed
        )
        self.tasks[name] = task_id
        
        # Get current overall task total and add the new task's size
        current_total = self.overall_progress.tasks[self.overall_task].total or 0
        self.overall_progress.update(self.overall_task, total=current_total + total_size)
        
        return task_id

    def update(self, name: str, advance: int):
        """Updates the progress of a task."""
        if name in self.tasks:
            self.file_progress.update(self.tasks[name], advance=advance)
            self.overall_progress.update(self.overall_task, advance=advance)

    def complete_file(self, name: str):
        """Mark a file as completed for better file count tracking."""
        if name in self.tasks:
            self.completed_files += 1
            # Mark task as finished but don't remove to avoid display issues
            task_id = self.tasks[name]
            self.file_progress.update(task_id, completed=self.file_progress.tasks[task_id].total)
            # Optionally remove the task after a short delay to keep display clean
            # For now, let's keep it to avoid index errors

    def update_status(self, status: str):
        """Update the overall status description."""
        self.overall_progress.update(self.overall_task, description=status)

    def get_eta_info(self) -> dict:
        """Get detailed ETA information as a dictionary."""
        if not self.start_time:
            return {}
        
        elapsed = time.time() - self.start_time
        overall_task = self.overall_progress.tasks[self.overall_task]
        
        if overall_task.total and overall_task.total > 0:
            progress_ratio = overall_task.completed / overall_task.total
            
            if progress_ratio > 0:
                estimated_total_time = elapsed / progress_ratio
                remaining_time = estimated_total_time - elapsed
                eta_time = datetime.now() + timedelta(seconds=int(remaining_time))
                
                speed_bps = overall_task.completed / elapsed if elapsed > 0 else 0
                
                return {
                    'elapsed_seconds': elapsed,
                    'remaining_seconds': remaining_time,
                    'eta_datetime': eta_time,
                    'progress_percentage': progress_ratio * 100,
                    'speed_bps': speed_bps,
                    'speed_mbps': speed_bps / (1024 * 1024),
                    'completed_bytes': overall_task.completed,
                    'total_bytes': overall_task.total,
                    'completed_files': self.completed_files,
                    'total_files': self.total_files
                }
        
        return {}

    def start(self):
        """Starts the progress bar display."""
        self.live.start()

    def stop(self):
        """Stops the progress bar display."""
        self.live.stop()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()