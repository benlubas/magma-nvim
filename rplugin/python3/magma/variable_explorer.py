from typing import Optional
from magma.magmabuffer import MagmaBuffer
from magma.runtime import JupyterRuntime
from pynvim import Nvim
from pynvim.api import Buffer

# this is the format of tho output from the %whos ipython command
"""
Variable   Type         Data/Info
---------------------------------
counts     int          3
data       dict         n=3
df         DataFrame      name  age     location\<...>n2  sam   19      vermont
names      list         n=3
pd         module       <module 'pandas' from '/h<...>ages/pandas/__init__.py'>
"""

class VariableExplorer():
    """ Class that handles all things variable explorer.
    Gets the data, parses and stores it. Opens the window, and formats and displays the information
    """
    nvim: Nvim
    runtime: JupyterRuntime

    win: Optional[int]
    buf: Optional[Buffer]

    def __init__(self, nvim: Nvim, runtime: JupyterRuntime):
        self.nvim = nvim
        self.runtime = runtime
        self.win = None
        self.buf = None

    def _open(self):
        """Open the variable explorer window.
        requires that self.buf is set to a Buffer
        """
        if not self.buf:
            return

        self.win = self.nvim.api.open_win(self.buf, False, {
            # TODO: fill this in
        })

    def display(self):
        """ Display the variable explorer window. This includes fetching the information, populating
        the buffer, and opening the window with self._open().
        """
        self.runtime.run_magic("%whos")
