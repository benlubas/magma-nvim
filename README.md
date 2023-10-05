# Magma

Magma is a NeoVim plugin for running code interactively with Jupyter.

![Feature Showcase (gif)](https://user-images.githubusercontent.com/15617291/128964224-f157022c-25cd-4a60-a0da-7d1462564ae4.gif)

## Requirements

- NeoVim 9.0+
- Python 3.10+
- Required Python packages:
  - [`pynvim`](https://github.com/neovim/pynvim) (for the Remote Plugin API)
  - [`jupyter_client`](https://github.com/jupyter/jupyter_client) (for interacting with Jupyter)
  - [`cairosvg`](https://cairosvg.org/) (for displaying SVG images)
  - [`pnglatex`](https://pypi.org/project/pnglatex/) (for displaying TeX formulas)
  - `plotly` and `kaleido` (for displaying Plotly figures)
  - `pyperclip` if you want to use `magma_copy_output`
- For .NET (C#, F#)
  - `dotnet tool install -g Microsoft.dotnet-interactive`
  - `dotnet interactive jupyter install`

You can do a `:checkhealth` to see if you are ready to go.

**Note:** Python packages which are used only for the display of some specific kind of output are only imported when that output actually appears.

## Installation

Use your favorite package/plugin manager.

<details>
<summary>Lazy</summary>

```lua
{ "dccsillag/magma-nvim", build = ":UpdateRemotePlugins" }
```
</details>

<details>
<summary>Packer</summary>

```lua
use { "dccsillag/magma-nvim", run = ":UpdateRemotePlugins" }
```

</details>

<details>
<summary>Plug</summary>

```vim
Plug 'dccsillag/magma-nvim', { 'do': ':UpdateRemotePlugins' }
```

</details>

**Note**: Keybindings are not set by default -- see [Keybindings](#keybindings).

## Quick-start

See the [Wiki Quick-start Guide](https://www.github.com/benlubas/magma-nvim/)

## Usage

The plugin provides a bunch of commands to enable interaction. It is recommended to map most of them to keys, as explained in [Keybindings](#keybindings). However, this section will refer to the commands by their names (so as to not depend on some specific mappings).

### Interface

When you execute some code, it will create a _cell_. You can recognize a cell because it will be highlighted when your cursor is in it.

A cell is delimited using two extmarks (see `:help api-extended-marks`), so it will adjust to you editing the text within it.

When your cursor is in a cell (i.e., you have an _active cell_), a floating window may be shown below the cell, reporting output. This is the _display window_, or _output window_. (To see more about whether a window is shown or not, see `:MagmaShowOutput` and `g:magma_automatically_open_output`). When you cursor is not in any cell, no cell is active.

The active cell is chosen from newest to oldest. That means that you can have a cell within another cell, and if the one within is newer, then that one will be selected. (Same goes for merely overlapping cells).

The output window has a header, containing the execution count and execution state (i.e., whether the cell is waiting to be run, running, has finished successfully or has finished with an error). Below the header are shown the outputs.

Jupyter provides a rich set of outputs. To see what we can currently handle, see [Output Chunks](#output-chunks).

### Commands Reference

| Command                  | Arguments             | Description                        |
|--------------------------|-----------------------|------------------------------------|
| `MagmaInit`              | `[kernel]`            | Initialize a kernel for the current buffer. If no kernel is given, prompts the user|
| `MagmaDeinit`            | none                  | De-initialize the current buffer's runtime and magma instance. (called automatically on vim close/buffer unload) |
| `MagmaEvaluateLine`      | none                  | Evaluate the current line |
| `MagmaEvaluateVisual`    | none                  | Evaluate the visual selection (**cannot be called with a range!**) |
| `MagmaEvaluateOperator`  | none                  | Evaluate text selected by the following operator. see [keymaps](#keymaps) for useage |
| `MagmaReevaluateCell`    | none                  | Re-evaluate the active cell (TODO: Does this include new code?) |
| `MagmaDelete`            | none                  | Delete the active cell (does nothing if there is no active cell) |
| `MagmaShowOutput`        | none                  | Shows the output window for the active cell |
| `MagmaHideOutput`        | none                  | Hide currently open output window |
| `MagmaInterrupt`         | none                  | Sends a keyboard interrupt to the kernel which stops any currently running code. (does nothing if there's no current output) |
| `MagmaRestart`           | `[!]`                 | Shuts down a restarts the current kernel. Deletes all outputs if used with a bang |
| `MagmaSave`              | `[path]`              | Save the current cells and evaluated outputs into a JSON file. When path is specified, save the file to `path`, otherwise save to `g:magma_save_path` |
| `MagmaLoad`              | `[path]`              | Loads cell locations and output from a JSON file generated by `MagmaSave`. path functions the same as `MagmaSave` |
| `MagmaEnterOutput`       | none                  | Move into the active cell's output window |

## Keybindings

The commands above should be mapped to keys for the best experience. There are more detailed setups
in the Wiki, but here are some example bindings.

```lua
vim.keymap.set("n", "<localleader>r", vim.api.nvim_exec2("MagmaEvaluateOperator", true), { expr = true, silent = true })
vim.keymap.set("n", "<localleader>rl", ":MagmaEvaluateLine<CR>", { silent = true })
vim.keymap.set("n", "<localleader>rc", ":MagmaReevaluateCell<CR>", { silent = true })
vim.keymap.set("v", "<localleader>r", ":<C-u>MagmaEvaluateVisual<CR>gv", { silent = true })
```

This way, `<LocalLeader>r` will behave just like standard keys such as `y` and `d`.

You can, of course, also map other commands:

```lua
vim.keymap.set("n", "<localleader>rd", ":MagmaDelete<CR>", { silent = true })
vim.keymap.set("n", "<localleader>ro", ":MagmaShowOutput<CR>", { silent = true })
vim.keymap.set("n", "<localleader>rq", ":noautocmd MagmaEnterOutput<CR>", { silent = true })
```

## Customization

Customization is done via variables.

### `g:magma_enter_output_behavior`

Configures the behavior of [MagmaEnterOutput](#magmaenteroutput)

- `"open_then_enter"` (default) -- open the window if it's closed. Enter the window if it's already open
- `"open_and_enter"` -- open and enter the window if it's closed. Otherwise enter as normal
- `"no_open"` -- enter the window when it's open, do nothing if it's closed

### `g:magma_image_provider`

Defaults to `"none"`.

This configures how to display images. The following options are available:

- `"none"` -- don't show images.
- `"ueberzug"` -- use [Ueberzug](https://github.com/seebye/ueberzug) to display images.
- `"kitty"` -- use the Kitty protocol to display images.

### `g:magma_automatically_open_output`

Defaults to `v:true`.

If this is true, then whenever you have an active cell its output window will be automatically shown.

If this is false, then the output window will only be automatically shown when you've just evaluated the code. So, if you take your cursor out of the cell, and then come back, the output window won't be opened (but the cell will be highlighted). This means that there will be nothing covering your code. You can then open the output window at will using [`:MagmaShowOutput`](#magma-show-output).

### `g:magma_wrap_output`

Defaults to `v:true`.

If this is true, then text output in the output window will be wrapped (akin to `set wrap`).

### `g:magma_output_window_borders`

Defaults to `v:true`.

If this is true, then the output window will have rounded borders. If it is false, it will have no borders.

### `g:magma_cell_highlight_group`

Defaults to `"CursorLine"`.

The highlight group to be used for highlighting cells.

### `g:magma_save_path`

Defaults to `stdpath("data") .. "/magma"`.

Where to save/load with [`:MagmaSave`](#magmasave) and [`:MagmaLoad`](#magmaload) (with no parameters).

The generated file is placed in this directory, with the filename itself being the buffer's name, with `%` replaced by `%%` and `/` replaced by `%`, and postfixed with the extension `.json`.

### `g:magma_copy_output`

Defaults to `v:false`.

To copy the evaluation output to clipboard automatically.

### [DEBUG] `g:magma_show_mimetype_debug`

Defaults to `v:false`.

If this is true, then before any non-iostream output chunk, Magma shows the mimetypes it received for it.

This is meant for debugging and adding new mimetypes.

## Autocommands

We provide some `User` autocommands (see `:help User`) for further customization. They are:

- `MagmaInitPre`: runs right before `MagmaInit` initialization happens for a buffer
- `MagmaInitPost`: runs right after `MagmaInit` initialization happens for a buffer
- `MagmaDeinitPre`: runs right before `MagmaDeinit` deinitialization happens for a buffer
- `MagmaDeinitPost`: runs right after `MagmaDeinit` deinitialization happens for a buffer

## Functions

There is a provided function `MagmaEvaluateRange(start_line, end_line)` which evaluates the code
between the given line numbers (inclusive). This is intended for use in scripts.

### Example Usage:

```lua
vim.fn.MagmaEvaluateRange(1, 23)
```

```vim
MagmaEvaluateRange(1, 23)
" from the command line
:call MagmaEvaluateRange(1, 23)
```

## Extras

### Output Chunks

In the Jupyter protocol, most output-related messages provide a dictionary of mimetypes which can be used to display the data. Theoretically, a `text/plain` field (i.e., plain text) is always present, so we (theoretically) always have that fallback.

Here is a list of the currently handled mimetypes:

- `text/plain`: Plain text. Shown as text in the output window's buffer.
- `image/png`: A PNG image. Shown according to `g:magma_image_provider`.
- `image/svg+xml`: A SVG image. Rendered into a PNG with [CairoSVG](https://cairosvg.org/) and shown with [Ueberzug](https://github.com/seebye/ueberzug).
- `application/vnd.plotly.v1+json`: A Plotly figure. Rendered into a PNG with [Plotly](https://plotly.com/python/) + [Kaleido](https://github.com/plotly/Kaleido) and shown with [Ueberzug](https://github.com/seebye/ueberzug).
- `text/latex`: A LaTeX formula. Rendered into a PNG with [pnglatex](https://pypi.org/project/pnglatex/) and shown with [Ueberzug](https://github.com/seebye/ueberzug).

This already provides quite a bit of basic functionality. As development continues, more mimetypes will be added.

### Correct progress bars and alike stuff

![](./caret.gif)

### Notifications

We use the `vim.notify` API. This means that you can use plugins such as [rcarriga/nvim-notify](https://github.com/rcarriga/nvim-notify) for pretty notifications.
