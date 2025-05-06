# gui_tooltip.py
"""
Simple ToolTip class for Tkinter widgets.
Displays a small pop-up window with help text when the mouse hovers
over a widget. This enhances user experience by providing contextual information.
"""
import tkinter as tk
from typing import Optional, Any # For type hinting

import config # For FONT_TOOLTIP and other potential shared UI constants
# from logger import logger # Not strictly needed for this simple class unless debugging its behavior

# DO NOT HAVE THIS LINE: from gui_tooltip import ToolTip 

class ToolTip:
    """
    Creates a tooltip for a given tkinter widget.
    The tooltip appears when the mouse enters the widget and disappears
    when the mouse leaves.
    """
    def __init__(self, widget: tk.Widget, text: str) -> None:
        """
        Initialize the ToolTip.

        Args:
            widget: The tkinter widget this tooltip is associated with.
            text: The text to display in the tooltip.
        """
        self.widget: tk.Widget = widget
        self.text: str = text
        self.tooltip_window: Optional[tk.Toplevel] = None
        self._bind_events()

    def _bind_events(self) -> None:
        """Binds mouse enter and leave events to show/hide the tooltip."""
        self.widget.bind("<Enter>", self.show_tooltip, '+') # '+' allows other bindings to also fire
        self.widget.bind("<Leave>", self.hide_tooltip, '+')

    def show_tooltip(self, event: Optional[tk.Event] = None) -> None: # pylint: disable=unused-argument
        """Displays the tooltip window near the widget."""
        if self.tooltip_window or not self.text:
            return # Do nothing if tooltip is already shown or no text to display

        x = self.widget.winfo_rootx() + 20 
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5 

        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True) 
        tw.wm_geometry(f"+{x}+{y}") 

        label = tk.Label(tw, text=self.text, justify='left',
                         background="#ffffe0", 
                         relief='solid', borderwidth=1,
                         font=config.FONT_TOOLTIP, 
                         wraplength=250) 
        label.pack(ipadx=3, ipady=3) 

    def hide_tooltip(self, event: Optional[tk.Event] = None) -> None: # pylint: disable=unused-argument
        """Hides/destroys the tooltip window."""
        if self.tooltip_window:
            try:
                self.tooltip_window.destroy()
            except tk.TclError:
                pass
        self.tooltip_window = None