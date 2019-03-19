import urwid
import webbrowser
from scrape import *
from ScrollBar import *
from urwid.widget import BOX, FIXED, FLOW

# Scroll actions
SCROLL_LINE_UP = "line up"
SCROLL_LINE_DOWN = "line down"
SCROLL_PAGE_UP = "page up"
SCROLL_PAGE_DOWN = "page down"
SCROLL_TO_TOP = "to top"
SCROLL_TO_END = "to end"

# Scrollbar positions
SCROLLBAR_LEFT = "left"
SCROLLBAR_RIGHT = "right"


class App(object):
    def __init__(self, search_results):
        self.search_results, self.viewing_answers = search_results, False
        self.palette = [
            ("title", "light cyan,bold", "default", "standout"),
            ("stats", "light green", "default", "standout"),
            ("menu", "black", "light cyan", "standout"),
            ("reveal focus", "black", "light cyan", "standout"),
            ("no answers", "light red", "default", "standout"),
            ("code", "brown", "default", "standout")
        ]
        self.menu = urwid.Text([
            u'\n',
            ("menu", u" ENTER "), ("light gray", u" View answers "),
            ("menu", u" B "), ("light gray", u" Open browser "),
            ("menu", u" Q "), ("light gray", u" Quit"),
        ])

        results = list(map(lambda result: urwid.AttrMap(SelectableText(self._stylize_title(
            result)), None, "reveal focus"), self.search_results))  # TODO: Add a wrap='clip' attribute
        content = urwid.SimpleListWalker(results)
        self.content_container = urwid.ListBox(content)
        layout = urwid.Frame(body=self.content_container, footer=self.menu)

        self.main_loop = urwid.MainLoop(
            layout, self.palette, unhandled_input=self._handle_input)
        self.original_widget = self.main_loop.widget

        self.main_loop.run()

    def _handle_input(self, input):
        if input == "enter":  # View answers
            url = self._get_selected_link()

            if url != None:
                self.viewing_answers = True
                question_title, question_desc, question_stats, answers = get_question_and_answers(
                    url)

                pile = urwid.Pile(self._stylize_question(question_title, question_desc, question_stats) + [urwid.Divider('*')] +
                                  interleave(answers, [urwid.Divider('-')] * (len(answers) - 1)))
                padding = ScrollBar(Scrollable(
                    urwid.Padding(pile, left=2, right=2)))
                #filler = urwid.Filler(padding, valign="top")
                linebox = urwid.LineBox(padding)

                menu = urwid.Text([
                    u'\n',
                    ("menu", u" ESC "), ("light gray", u" Go back "),
                    ("menu", u" B "), ("light gray", u" Open browser "),
                    ("menu", u" Q "), ("light gray", u" Quit"),
                ])

                self.main_loop.widget = urwid.Frame(body=urwid.Overlay(
                    linebox, self.content_container, "center", ("relative", 60), "middle", 23), footer=menu)
        elif input in ('b', 'B'):  # Open link
            url = self._get_selected_link()

            if url != None:
                webbrowser.open(url)
        elif input == "esc":  # Close window
            if self.viewing_answers:
                self.main_loop.widget = self.original_widget
                self.viewing_answers = False
            else:
                raise urwid.ExitMainLoop()
        elif input in ('q', 'Q'):  # Quit
            raise urwid.ExitMainLoop()

    def _get_selected_link(self):
        focus_widget, idx = self.content_container.get_focus()  # Gets selected item
        title = focus_widget.base_widget.text

        for result in self.search_results:
            # Found selected title's search_result dict
            if title == self._stylize_title(result):
                return result["URL"]

    def _stylize_title(self, search_result):
        if search_result["Answers"] == 1:
            return "%s (1 Answer)" % search_result["Title"]
        else:
            return "%s (%s Answers)" % (search_result["Title"], search_result["Answers"])

    def _stylize_question(self, title, desc, stats):
        new_title = urwid.Text(("title", u"%s" % title))
        new_stats = urwid.Text(("stats", u"%s\n" % stats))

        return [new_title, desc, new_stats]


class Scrollable(urwid.WidgetDecoration):
    # TODO: Fix scrolling behavior (works with up/down keys, not with cursor)

    def sizing(self):
        return frozenset([BOX, ])

    def selectable(self):
        return True

    def __init__(self, widget):
        """Box widget (wrapper) that makes a fixed or flow widget vertically scrollable."""
        self._trim_top = 0
        self._scroll_action = None
        self._forward_keypress = None
        self._old_cursor_coords = None
        self._rows_max_cached = 0
        self._rows_max_displayable = 0
        self.__super.__init__(widget)

    def render(self, size, focus=False):
        maxcol, maxrow = size

        # Render complete original widget
        ow = self._original_widget
        ow_size = self._get_original_widget_size(size)
        canv = urwid.CompositeCanvas(ow.render(ow_size, focus))
        canv_cols, canv_rows = canv.cols(), canv.rows()

        if canv_cols <= maxcol:
            pad_width = maxcol - canv_cols
            if pad_width > 0:  # Canvas is narrower than available horizontal space
                canv.pad_trim_left_right(0, pad_width)

        if canv_rows <= maxrow:
            fill_height = maxrow - canv_rows
            if fill_height > 0:  # Canvas is lower than available vertical space
                canv.pad_trim_top_bottom(0, fill_height)
        self._rows_max_displayable = maxrow
        if canv_cols <= maxcol and canv_rows <= maxrow:  # Canvas is small enough to fit without trimming
            return canv

        self._adjust_trim_top(canv, size)

        # Trim canvas if necessary
        trim_top = self._trim_top
        trim_end = canv_rows - maxrow - trim_top
        trim_right = canv_cols - maxcol
        if trim_top > 0:
            canv.trim(trim_top)
        if trim_end > 0:
            canv.trim_end(trim_end)
        if trim_right > 0:
            canv.pad_trim_left_right(0, -trim_right)

        # Disable cursor display if cursor is outside of visible canvas parts
        if canv.cursor is not None:
            curscol, cursrow = canv.cursor
            if cursrow >= maxrow or cursrow < 0:
                canv.cursor = None

        # Let keypress() know if original_widget should get keys
        self._forward_keypress = bool(canv.cursor)

        return canv

    def keypress(self, size, key):
        if self._forward_keypress:
            ow = self._original_widget
            ow_size = self._get_original_widget_size(size)

            # Remember previous cursor position if possible
            if hasattr(ow, "get_cursor_coords"):
                self._old_cursor_coords = ow.get_cursor_coords(ow_size)

            key = ow.keypress(ow_size, key)
            if key is None:
                return None

        # Handle up/down, page up/down, etc
        command_map = self._command_map
        if command_map[key] == urwid.CURSOR_UP:
            self._scroll_action = SCROLL_LINE_UP
        elif command_map[key] == urwid.CURSOR_DOWN:
            self._scroll_action = SCROLL_LINE_DOWN
        elif command_map[key] == urwid.CURSOR_PAGE_UP:
            self._scroll_action = SCROLL_PAGE_UP
        elif command_map[key] == urwid.CURSOR_PAGE_DOWN:
            self._scroll_action = SCROLL_PAGE_DOWN
        elif command_map[key] == urwid.CURSOR_MAX_LEFT:  # "home"
            self._scroll_action = SCROLL_TO_TOP
        elif command_map[key] == urwid.CURSOR_MAX_RIGHT:  # "end"
            self._scroll_action = SCROLL_TO_END
        else:
            return key

        self._invalidate()

    def mouse_event(self, size, event, button, col, row, focus):
        ow = self._original_widget
        if hasattr(ow, "mouse_event"):
            ow_size = self._get_original_widget_size(size)
            row += self._trim_top
            return ow.mouse_event(ow_size, event, button, col, row, focus)
        else:
            return False

    def _adjust_trim_top(self, canv, size):
        """Adjust self._trim_top according to self._scroll_action"""
        action = self._scroll_action
        self._scroll_action = None

        maxcol, maxrow = size
        trim_top = self._trim_top
        canv_rows = canv.rows()

        if trim_top < 0:
            # Negative trim_top values use bottom of canvas as reference
            trim_top = canv_rows - maxrow + trim_top + 1

        if canv_rows <= maxrow:
            self._trim_top = 0  # Reset scroll position
            return

        def ensure_bounds(new_trim_top):
            return max(0, min(canv_rows - maxrow, new_trim_top))

        if action == SCROLL_LINE_UP:
            self._trim_top = ensure_bounds(trim_top - 1)
        elif action == SCROLL_LINE_DOWN:
            self._trim_top = ensure_bounds(trim_top + 1)
        elif action == SCROLL_PAGE_UP:
            self._trim_top = ensure_bounds(trim_top - maxrow+1)
        elif action == SCROLL_PAGE_DOWN:
            self._trim_top = ensure_bounds(trim_top + maxrow-1)
        elif action == SCROLL_TO_TOP:
            self._trim_top = 0
        elif action == SCROLL_TO_END:
            self._trim_top = canv_rows - maxrow
        else:
            self._trim_top = ensure_bounds(trim_top)

        if self._old_cursor_coords is not None and self._old_cursor_coords != canv.cursor:
            self._old_cursor_coords = None
            curscol, cursrow = canv.cursor
            if cursrow < self._trim_top:
                self._trim_top = cursrow
            elif cursrow >= self._trim_top + maxrow:
                self._trim_top = max(0, cursrow - maxrow + 1)

    def _get_original_widget_size(self, size):
        ow = self._original_widget
        sizing = ow.sizing()
        if FIXED in sizing:
            return ()
        elif FLOW in sizing:
            return (size[0],)

    def get_scrollpos(self, size=None, focus=False):
        return self._trim_top

    def set_scrollpos(self, position):
        self._trim_top = int(position)
        self._invalidate()

    def rows_max(self, size=None, focus=False):
        if size is not None:
            ow = self._original_widget
            ow_size = self._get_original_widget_size(size)
            sizing = ow.sizing()
            if FIXED in sizing:
                self._rows_max_cached = ow.pack(ow_size, focus)[1]
            elif FLOW in sizing:
                self._rows_max_cached = ow.rows(ow_size, focus)
            else:
                raise RuntimeError("Not a flow/box widget: %r" %
                                   self._original_widget)
        return self._rows_max_cached

    @property
    def scroll_ratio(self):
        return self._rows_max_cached / self._rows_max_displayable


def interleave(a, b):
    result = []
    while a and b:
        result.append(a.pop(0))
        result.append(b.pop(0))

    result.extend(a)
    result.extend(b)

    return result

class SelectableText(urwid.Text):
    def selectable(self):
        return True

    def keypress(self, size, key):
        return key
