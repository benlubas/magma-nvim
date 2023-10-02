from typing import List, Optional

from pynvim import Nvim
from pynvim.api import Buffer

from magma.images import Canvas
from magma.outputchunks import Output, OutputStatus
from magma.options import MagmaOptions
from magma.utils import Position


class OutputBuffer:
    nvim: Nvim
    canvas: Canvas

    output: Output

    display_buffer: Buffer
    display_window: Optional[int]

    options: MagmaOptions

    def __init__(self, nvim: Nvim, canvas: Canvas, options: MagmaOptions):
        self.nvim = nvim
        self.canvas = canvas

        self.output = Output(None)

        self.display_buffer = self.nvim.buffers[
            self.nvim.funcs.nvim_create_buf(False, True)
        ]
        self.display_window = None

        self.options = options

    def _buffer_to_window_lineno(self, lineno: int) -> int:
        win_top = self.nvim.funcs.line("w0")
        assert isinstance(win_top, int)

        # handle folds
        # (code modified from image.nvim https://github.com/3rd/image.nvim/blob/16f54077ca91fa8c4d1239cc3c1b6663dd169092/lua/image/renderer.lua#L254)
        offset = 0
        if self.nvim.current.window.options["foldenable"]:
            i = win_top
            while i <= lineno:
                fold_start = self.nvim.funcs.foldclosed(i)
                fold_end = self.nvim.funcs.foldclosedend(i)
                if fold_start != -1 and fold_end != -1:
                    offset += (fold_end - fold_start)
                    i = fold_end + 1
                else:
                    i += 1

        return lineno - win_top + 1 - offset

    def _get_header_text(self, output: Output) -> str:
        if output.execution_count is None:
            execution_count = "..."
        else:
            execution_count = str(output.execution_count)

        if output.status == OutputStatus.HOLD:
            status = "* On Hold"
        elif output.status == OutputStatus.DONE:
            if output.success:
                status = "✓ Done"
            else:
                status = "✗ Failed"
        elif output.status == OutputStatus.RUNNING:
            status = "... Running"
        else:
            raise ValueError("bad output.status: %s" % output.status)

        if output.old:
            old = "[OLD] "
        else:
            old = ""

        return f"{old}Out[{execution_count}]: {status}"

    def enter(self, anchor: Position) -> None:
        if self.display_window is None:
            if self.options.enter_output_behavior == "open_then_enter":
                self.show(anchor)
                return
            elif self.options.enter_output_behavior == "open_and_enter":
                self.show(anchor)
                self.nvim.funcs.nvim_set_current_win(self.display_window)
                return
        elif self.options.enter_output_behavior != "no_open":
            self.nvim.funcs.nvim_set_current_win(self.display_window)

    def clear_interface(self) -> None:
        if self.display_window is not None:
            self.nvim.funcs.nvim_win_close(self.display_window, True)
            self.display_window = None

    def show(self, anchor: Position) -> None:  # XXX .show_outputs(_, anchor)
        # FIXME use `anchor.buffer`, Not `self.nvim.current.window`

        # Get width&height, etc
        win = self.nvim.current.window
        win_col = win.col
        win_row = self._buffer_to_window_lineno(anchor.lineno + 1)
        win_width = win.width
        win_height = win.height

        if self.options.output_window_borders:
            win_height -= 2

        # Clear buffer:
        self.nvim.funcs.deletebufline(self.display_buffer.number, 1, "$")
        # Add output chunks to buffer
        lines_str = ""
        lineno = 0
        # images are rendered with virtual lines by image.nvim
        virtual_lines = 0
        sign_col_width = self.nvim.funcs.getwininfo(win.handle)[0]["textoff"]
        shape = (
            win_col + sign_col_width,
            win_row,
            win_width - sign_col_width,
            win_height,
        )
        if len(self.output.chunks) > 0:
            for chunk in self.output.chunks:
                chunktext, virt_lines = chunk.place(
                    self.display_buffer.number,
                    self.options,
                    lineno,
                    shape,
                    self.canvas,
                )
                lines_str += chunktext
                lineno += chunktext.count("\n")
                virtual_lines += virt_lines

            lines = handle_progress_bars(lines_str)
            lineno = len(lines)
        else:
            lines = [lines_str]

        self.display_buffer[0] = self._get_header_text(self.output)
        self.display_buffer.append(lines)

        # Open output window
        assert self.display_window is None
        if win_row < win_height:
            self.display_window = self.nvim.api.open_win(
                self.display_buffer.number,
                False,
                {
                    "relative": "win",
                    "row": win_row,
                    "col": sign_col_width,
                    "width": win_width - sign_col_width,
                    "height": min(
                        win_height - win_row, lineno + virtual_lines + 1
                    ),
                    "style": "minimal",
                    "border": (
                        "rounded"
                        if self.options.output_window_borders
                        else "none"
                    ),
                    "focusable": False,
                },
            )
            self.canvas.present()

def handle_progress_bars(line_str: str) -> List[str]:
    """ Progress bars like tqdm use special chars (`\\r`) and some trick to work
    This is fine for the terminal, but in a text editor we have so do some extra work
    """
    actual_lines = []
    lines = line_str.split("\n")
    for line in lines:
        parts = line.split('\r')
        last = parts[-1]
        if last != "":
            actual_lines.append(last)
            lines = actual_lines

    return actual_lines
