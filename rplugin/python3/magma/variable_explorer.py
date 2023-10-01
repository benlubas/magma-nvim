from typing import Optional
from magma.runtime import JupyterRuntime
from magma.options import MagmaOptions
from magma.utils import set_win_options
from pynvim import Nvim
from pynvim.api import Buffer, Window

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


class VariableExplorer:
    """Class that handles all things variable explorer.
    Gets the data, parses and stores it. Opens the window, and formats and displays the information
    """

    nvim: Nvim
    runtime: JupyterRuntime
    options: MagmaOptions

    win: Optional[Window]
    buf: Optional[Buffer]

    def __init__(
        self, nvim: Nvim, runtime: JupyterRuntime, options: MagmaOptions
    ):
        self.nvim = nvim
        self.runtime = runtime
        self.win = None
        self.buf = None
        self.options = options

    def _open(self):
        """Open the variable explorer window and set it's options. Does not set the window buffer"""
        previous_win = (
            self.nvim.current.window
        )  # return to this window at the end

        width = self.options.var_exp_width
        self.nvim.command(f"vertical botright {width}vsplit")
        self.win = self.nvim.current.window

        # TODO: what options should go here?
        options = {
            "wrap": False,
            "spell": False,
            "signcolumn": "auto",
        }

        set_win_options(self.nvim, self.win.handle, options)

        # TODO: set win options

        self.nvim.api.set_current_win(previous_win)

    def is_open(self) -> bool:
        return self.win is not None and self.win.valid

    def display(self):
        """Display the variable explorer window. This includes fetching the information, populating
        the buffer, and opening the window with self._open().
        """
        if self.is_open():
            self.nvim.out_write("variable explorer is already open\n")
            return
        self._open()
        self.runtime.run_magic("%whos", self.whos_callback)

    def whos_callback(self, output: str):
        self.nvim.out_write(f"[whos_callback] output: {output}\n")
        if self.win is None:
            self._open()

        if self.buf is None:
            self.buf = self.nvim.buffers[
                self.nvim.funcs.nvim_create_buf(False, True)
            ]

        self.populate_buffer(self.buf, output)
        self.nvim.api.win_set_buf(self.win, self.buf)

    def populate_buffer(self, buf: Buffer, output: str):
        """Populate the buffer with the output from the %whos command"""
        self.nvim.out_write(f"populating buffer with {output}\n")
        self.nvim.api.buf_set_lines(
            buf, 0, -1, True, output["text"].split("\n")
        )
        buf.api.set_lines(0, -1, True, output["text"].split("\n"))
