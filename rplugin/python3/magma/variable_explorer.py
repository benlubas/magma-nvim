from dataclasses import dataclass
from typing import Dict, Optional
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


@dataclass
class VarData:
    type_: str
    value: str
    changed: bool = False


class VariableExplorer:
    """Class that handles all things variable explorer.
    Gets the data, parses and stores it. Opens the window, and formats and displays the information
    """

    nvim: Nvim
    runtime: JupyterRuntime
    options: MagmaOptions

    win: Optional[Window]
    buf: Optional[Buffer]

    # each key is a variable name
    var_data: Dict[str, VarData]
    changed_namespace: str

    def __init__(
        self, nvim: Nvim, runtime: JupyterRuntime, options: MagmaOptions
    ):
        self.nvim = nvim
        self.runtime = runtime
        self.win = None
        self.buf = None
        self.options = options
        self.var_data = dict()
        self.changed_namespace = nvim.api.create_namespace(
            "magma_changed_vars"
        )

    def _open(self):
        """Open the variable explorer window and set it's options. Does not set the window buffer"""
        previous_win = self.nvim.current.window

        width = self.options.var_expl_width
        self.nvim.command(f"vertical botright {width}vsplit")
        self.win = self.nvim.current.window

        # TODO: what other options should go here?
        options = {
            "wrap": False,
            "spell": False,
            "signcolumn": "auto",
        }
        set_win_options(self.nvim, self.win.handle, options)

        self.nvim.api.set_current_win(previous_win)

    def is_open(self) -> bool:
        return self.win is not None and self.win.valid

    def display(self):
        """Display the variable explorer window. This includes fetching the information, populating
        the buffer, and opening the window with self._open().
        """
        if self.is_open():
            self.nvim.api.set_current_win(self.win)
            return
        self._open()
        self.runtime.run_magic("%whos", self.whos_callback)

    def refresh(self):
        if self.is_open():
            self.runtime.run_magic("%whos", self.whos_callback)

    def whos_callback(self, output: Dict):
        self.nvim.out_write(f"[whos_callback] output: {output}\n")
        if self.win is None:
            return  # the window has been closed since this request was made

        if self.buf is None:
            self.buf = self.nvim.buffers[
                self.nvim.funcs.nvim_create_buf(False, True)
            ]

        self.populate_buffer(self.buf, output)
        self.nvim.api.win_set_buf(self.win, self.buf)

    def populate_buffer(self, buf: Buffer, output: Dict):
        """Populate the buffer with the output from the %whos command"""
        self.nvim.out_write(f"populating buffer with {output}\n")
        new_data = self.parse_output_text(output["text"])

        # compare new and old data, see what's changed
        for key, value in new_data.items():
            if key not in self.var_data or self.var_data[key] != value:
                self.var_data[key] = value
                self.var_data[key].changed = True

        # convert this data to buffer lines
        lines = []
        changes = False
        for key, value in self.var_data.items():
            lines.append(f"{key}: {value.type_} = {value.value}")
            if value.changed and self.buf:
                changes = True
                self.nvim.funcs.nvim_buf_add_highlight(
                    self.buf.number,
                    self.changed_namespace,
                    self.options.var_expl_changed_highlight,
                    len(lines) - 1,
                    0,
                    -1,
                )

        if changes and self.buf:
            # Clear the new changes namespace after 300ms
            self.nvim.exec_lua(
                f"""
                local buf = {self.buf.handle}
                vim.defer_fn(function()
                    if vim.api.nvim_buf_is_valid(buf) then
                        vim.api.nvim_buf_clear_namespace(buf, {self.changed_namespace}, 0, -1)
                    end
                end, 300)
                """
            )

        self.nvim.api.buf_set_lines(buf, 0, -1, True, lines)

    def parse_output_text(self, output: str) -> Dict[str, VarData]:
        """Parse the output from the %whos command into a dictionary"""
        data = dict()
        for line in output.split("\n")[2:]:
            words = line.split()
            if len(words) < 3:
                continue
            self.nvim.out_write(f"words: {words}\n")
            data[words[0]] = VarData(words[1], " ".join(words[2:]))
        return data
