"""输入框灰色参考示例；提示不进入 Text 内容或撤销记录。"""
import tkinter as tk

KEYWORDS_HINT = '格式参考：\n错误\n失败\n超时'
PATTERNS_HINT = r'''格式参考：
\berror\b
\bwarn(?:ing)?\b
\bfail(?:ed|ure)?\b
\b(?:error|fatal|panic)\b
温度[:：]\s*\d+(?:\.\d+)?
\b0[xX][0-9A-Fa-f]+\b'''


class HintText(tk.Text):
    def __init__(self, parent, hint, **kwargs):
        super().__init__(parent, **kwargs)
        self.hint = tk.Label(self, text=hint, fg='#7A8494', bg=self.cget('background'),
                             font=self.cget('font'), justify='left', anchor='nw', padx=0, pady=0)
        self.hint.bind('<Button-1>', lambda event: self.focus_set())
        self.bind('<<Modified>>', self._modified, add='+')
        self.sync_hint()

    def _modified(self, event=None):
        if self.edit_modified():
            self.edit_modified(False)
            self.sync_hint()
            self.event_generate('<<InputChanged>>')

    def sync_hint(self):
        if self.cget('state') != 'disabled' and not self.get('1.0', 'end-1c'):
            self.hint.place(x=4, y=4)
        else:
            self.hint.place_forget()
