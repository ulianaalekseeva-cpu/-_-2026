import tkinter as tk
from tkinter import messagebox, font as tkfont
from datetime import datetime
import time
import math

BG_DARK      = "#1A1A1A"
BG_CARD      = "#2A2A2A"
BG_CARD_ALT  = "#333333"
BG_INPUT     = "#3A3A3A"
YELLOW       = "#FFDD2D"
YELLOW_DARK  = "#E6C628"
TEXT_WHITE   = "#FFFFFF"
TEXT_GRAY    = "#9E9E9E"
GREEN        = "#4CAF50"
RED          = "#F44336"

def _pick_font():
    available = set(tkfont.families())
    for name in ("Segoe UI", "Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"):
        if name in available:
            return name
    return "TkDefaultFont"

_APP_FONT = None
def _init_fonts():
    global _APP_FONT, FONT_MAIN, FONT_BOLD, FONT_TITLE, FONT_BALANCE, FONT_SMALL, FONT_INPUT
    _APP_FONT = _pick_font()
    FONT_MAIN    = (_APP_FONT, 11)
    FONT_BOLD    = (_APP_FONT, 12, "bold")
    FONT_TITLE   = (_APP_FONT, 20, "bold")
    FONT_BALANCE = (_APP_FONT, 30, "bold")
    FONT_SMALL   = (_APP_FONT, 9)
    FONT_INPUT   = (_APP_FONT, 12)


FONT_MAIN = FONT_BOLD = FONT_TITLE = FONT_BALANCE = FONT_SMALL = FONT_INPUT = ("TkDefaultFont", 11)

class Auth:
    MAX_ATTEMPTS = 3
    LOCK_SECONDS = 30

    def __init__(self):
        self.users = {
            "+79001234567": {"password": "qwerty123", "name": "Иван Иванов",  "balance": 128_450.75},
            "+79005551122": {"password": "password",  "name": "Анна Петрова", "balance": 45_000.00},
        }
        self.current_user = None
        self._attempts = {}   # phone -> (count, lock_until_ts)

    def normalize_phone(self, raw: str):
        """Возвращает +7XXXXXXXXXX или None."""
        if not raw:
            return None
        digits = "".join(ch for ch in raw if ch.isdigit())
        if len(digits) == 11 and digits[0] in "78":
            return "+7" + digits[1:]
        if len(digits) == 10:
            return "+7" + digits
        return None

    def is_locked(self, phone: str):
        rec = self._attempts.get(phone)
        if not rec:
            return 0
        count, lock_until = rec
        if lock_until and time.time() < lock_until:
            return int(lock_until - time.time()) + 1
        return 0

    def _register_fail(self, phone: str):
        count, _ = self._attempts.get(phone, (0, 0))
        count += 1
        lock_until = time.time() + self.LOCK_SECONDS if count >= self.MAX_ATTEMPTS else 0
        self._attempts[phone] = (count, lock_until)

    def _reset_attempts(self, phone: str):
        self._attempts.pop(phone, None)

    def login(self, phone: str, password: str):
        norm = self.normalize_phone(phone)
        if not norm:
            return False, "Введите корректный номер телефона"

        locked = self.is_locked(norm)
        if locked:
            return False, f"Слишком много попыток. Повторите через {locked} сек."

        if len(password) < 6:
            return False, "Пароль должен быть не короче 6 символов"

        user = self.users.get(norm)
        if not user:
            self._register_fail(norm)
            return False, "Пользователь с таким номером не найден"
        if user["password"] != password:
            self._register_fail(norm)
            left = self.MAX_ATTEMPTS - self._attempts.get(norm, (0, 0))[0]
            if left > 0:
                return False, f"Неверный пароль. Осталось попыток: {left}"
            return False, f"Аккаунт заблокирован на {self.LOCK_SECONDS} сек."

        self._reset_attempts(norm)
        self.current_user = {"phone": norm, **user}
        return True, ""

    def logout(self):
        self.current_user = None

    def save_balance(self, balance: float):
        """Синхронизирует баланс текущего пользователя в хранилище."""
        if self.current_user:
            self.current_user["balance"] = balance
            self.users[self.current_user["phone"]]["balance"] = balance



class LoginScreen(tk.Frame):
    def __init__(self, master, auth: Auth, on_success):
        super().__init__(master, bg=BG_DARK)
        self.auth = auth
        self.on_success = on_success
        self._build()

    def _build(self):
        logo = tk.Canvas(self, width=80, height=80, bg=BG_DARK, highlightthickness=0)
        logo.pack(pady=(50, 10))
        logo.create_oval(2, 2, 78, 78, fill=YELLOW, outline="")
        logo.create_text(40, 40, text="Т", fill=BG_DARK,
                         font=(_APP_FONT, 38, "bold"))

        tk.Label(self, text="Добро пожаловать", font=FONT_TITLE,
                 fg=TEXT_WHITE, bg=BG_DARK).pack(pady=(6, 4))
        tk.Label(self, text="Войдите в личный кабинет", font=FONT_MAIN,
                 fg=TEXT_GRAY, bg=BG_DARK).pack(pady=(0, 24))

        tk.Label(self, text="Номер телефона", font=FONT_SMALL,
                 fg=TEXT_GRAY, bg=BG_DARK).pack(anchor="w", padx=40)
        self.phone_entry = tk.Entry(
            self, font=FONT_INPUT, bg=BG_INPUT, fg=TEXT_WHITE,
            insertbackground=YELLOW, relief="flat"
        )
        self.phone_entry.pack(fill="x", padx=40, pady=(4, 12), ipady=10)
        self.phone_entry.insert(0, "+7")
        self.phone_entry.bind("<Return>", lambda e: self.password_entry.focus_set())

        tk.Label(self, text="Пароль", font=FONT_SMALL,
                 fg=TEXT_GRAY, bg=BG_DARK).pack(anchor="w", padx=40)

        pwd_row = tk.Frame(self, bg=BG_DARK)
        pwd_row.pack(fill="x", padx=40, pady=(4, 6))

        self.password_entry = tk.Entry(
            pwd_row, font=FONT_INPUT, bg=BG_INPUT, fg=TEXT_WHITE,
            insertbackground=YELLOW, relief="flat", show="•"
        )
        self.password_entry.pack(side="left", fill="x", expand=True, ipady=10)
        self.password_entry.bind("<Return>", lambda e: self._do_login())

        self.show_pwd = tk.BooleanVar(value=False)
        tk.Checkbutton(
            pwd_row, text="показать", variable=self.show_pwd,
            command=self._toggle_pwd,
            bg=BG_DARK, fg=TEXT_GRAY, activebackground=BG_DARK,
            activeforeground=YELLOW, selectcolor=BG_INPUT,
            indicatoron=0, relief="flat", bd=0, padx=8,
            cursor="hand2", font=FONT_SMALL
        ).pack(side="left", padx=(6, 0))

        self.remember = tk.BooleanVar(value=True)
        tk.Checkbutton(
            self, text="Запомнить меня", variable=self.remember,
            bg=BG_DARK, fg=TEXT_GRAY, activebackground=BG_DARK,
            activeforeground=TEXT_WHITE, selectcolor=BG_INPUT,
            indicatoron=0, relief="flat", bd=0, padx=6,
            cursor="hand2", font=FONT_SMALL
        ).pack(anchor="w", padx=40, pady=(4, 12))

        self.error_label = tk.Label(self, text="", font=FONT_SMALL,
                                    fg=RED, bg=BG_DARK, wraplength=340)
        self.error_label.pack(pady=(0, 6))

        tk.Button(
            self, text="Войти", bg=YELLOW, fg=BG_DARK, font=FONT_BOLD,
            relief="flat", bd=0, pady=12, cursor="hand2",
            activebackground=YELLOW_DARK, command=self._do_login
        ).pack(fill="x", padx=40, pady=(4, 18))

        hint = tk.Frame(self, bg=BG_CARD, padx=14, pady=10)
        hint.pack(fill="x", padx=40)
        tk.Label(hint, text="Тестовые учётные данные", font=FONT_SMALL,
                 fg=YELLOW, bg=BG_CARD).pack(anchor="w")
        tk.Label(hint,
                 text="+7 900 123-45-67  /  qwerty123\n+7 900 555-11-22  /  password",
                 font=FONT_SMALL, fg=TEXT_GRAY, bg=BG_CARD,
                 justify="left").pack(anchor="w", pady=(2, 0))

    def _toggle_pwd(self):
        self.password_entry.config(show="" if self.show_pwd.get() else "•")

    def _do_login(self):
        phone = self.phone_entry.get().strip()
        pwd = self.password_entry.get()
        self.error_label.config(text="")

        ok, err = self.auth.login(phone, pwd)
        if not ok:
            self.error_label.config(text=err)
            self.password_entry.delete(0, "end")
            return

        self.on_success(self.auth.current_user)


class MainApp(tk.Frame):
    def __init__(self, master, auth: Auth, on_logout):
        super().__init__(master, bg=BG_DARK)
        self.auth = auth
        self.on_logout = on_logout
        self.user = auth.current_user

        self.balance = self.user["balance"]
        self.cards = [
            {"name": "Black",  "number": "•••• 4521", "color": "#000000"},
            {"name": "Credit", "number": "•••• 8830", "color": "#3A3A3A"},
        ]
        self.operations = [
            ("Кофейня «Шоколадница»", -320.00,   "Сегодня, 09:14"),
            ("Зарплата",              +85_000.00,"Вчера, 10:00"),
            ("Ozon",                  -2_490.00, "Вчера, 18:32"),
            ("Перевод от Анны",       +1_500.00, "12 ноя, 20:05"),
            ("Аптека",                -740.50,   "12 ноя, 15:47"),
        ]

        self.container = tk.Frame(self, bg=BG_DARK)
        self.container.pack(fill="both", expand=True)

        self._show_main()

    # ---------- служебное ----------
    def _clear(self):
        try:
            self.unbind_all("<MouseWheel>")
        except tk.TclError:
            pass
        for w in self.container.winfo_children():
            w.destroy()

    def _bind_wheel(self, canvas):
        def _on_wheel(e):
            canvas.yview_scroll(int(-e.delta / 120), "units")
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_wheel))
        canvas.bind("<Leave>", lambda e: self.unbind_all("<MouseWheel>"))

    def _sync_balance(self):
        self.auth.save_balance(self.balance)

    def _show_main(self):
        self._clear()
        self._build_header()
        self._build_balance_card()
        self._build_quick_actions()
        self._build_cards_section()
        self._build_operations()

    def _build_header(self):
        header = tk.Frame(self.container, bg=BG_DARK, pady=16, padx=20)
        header.pack(fill="x")

        first_name = self.user["name"].split()[0]
        tk.Label(header, text=f"Привет, {first_name} 👋", font=FONT_BOLD,
                 fg=TEXT_WHITE, bg=BG_DARK).pack(side="left")

        avatar = tk.Canvas(header, width=36, height=36, bg=BG_DARK,
                           highlightthickness=0, cursor="hand2")
        avatar.pack(side="right")
        avatar.create_oval(2, 2, 34, 34, fill=YELLOW, outline="")
        avatar.create_text(18, 18, text=first_name[0], fill=BG_DARK,
                           font=(_APP_FONT, 14, "bold"))
        avatar.bind("<Button-1>", lambda e: self._show_profile())

    def _build_balance_card(self):
        card = tk.Frame(self.container, bg=BG_CARD, padx=24, pady=20)
        card.pack(fill="x", padx=20)

        tk.Label(card, text="Общий баланс", font=FONT_MAIN,
                 fg=TEXT_GRAY, bg=BG_CARD).pack(anchor="w")

        self.balance_label = tk.Label(
            card, text=self._fmt(self.balance), font=FONT_BALANCE,
            fg=TEXT_WHITE, bg=BG_CARD
        )
        self.balance_label.pack(anchor="w", pady=(4, 12))

        row = tk.Frame(card, bg=BG_CARD)
        row.pack(fill="x")
        self._pill_button(row, "Пополнить", self._dialog_topup, YELLOW, BG_DARK)
        self._pill_button(row, "Перевести", self._dialog_transfer, BG_CARD_ALT, TEXT_WHITE)

    def _build_quick_actions(self):
        wrap = tk.Frame(self.container, bg=BG_DARK, pady=20, padx=20)
        wrap.pack(fill="x")

        actions = [
            ("💳", "Платежи",          self._show_payments),
            ("📱", "Мобильная\nсвязь", self._dialog_mobile),
            ("🔄", "Переводы",         self._dialog_transfer),
            ("📊", "Инвест-\nции",     self._show_invest),
        ]
        for emoji, label, cmd in actions:
            col = tk.Frame(wrap, bg=BG_DARK)
            col.pack(side="left", expand=True)

            circle = tk.Canvas(col, width=52, height=52, bg=BG_DARK,
                               highlightthickness=0, cursor="hand2")
            circle.pack()
            circle.create_oval(2, 2, 50, 50, fill=BG_CARD, outline="")
            circle.create_text(26, 26, text=emoji, font=(_APP_FONT, 20))
            circle.bind("<Button-1>", lambda e, c=cmd: c())

            lbl = tk.Label(col, text=label, font=FONT_SMALL, fg=TEXT_GRAY,
                           bg=BG_DARK, justify="center", cursor="hand2")
            lbl.pack(pady=(6, 0))
            lbl.bind("<Button-1>", lambda e, c=cmd: c())

    def _build_cards_section(self):
        wrap = tk.Frame(self.container, bg=BG_DARK, padx=20)
        wrap.pack(fill="x", pady=(4, 0))

        tk.Label(wrap, text="Мои карты", font=FONT_BOLD,
                 fg=TEXT_WHITE, bg=BG_DARK).pack(anchor="w", pady=(0, 8))

        for card in self.cards:
            self._make_bank_card(wrap, card)

    def _make_bank_card(self, parent, card):
        frame = tk.Frame(parent, bg=card["color"], padx=16, pady=14,
                         cursor="hand2")
        frame.pack(fill="x", pady=4)

        top = tk.Frame(frame, bg=card["color"])
        top.pack(fill="x")
        tk.Label(top, text=card["name"], font=FONT_BOLD,
                 fg=YELLOW, bg=card["color"]).pack(side="left")
        tk.Label(top, text="МИР", font=FONT_SMALL,
                 fg=TEXT_GRAY, bg=card["color"]).pack(side="right")

        card_balance = self.balance if card["name"] == "Black" else 45_000.00
        tk.Label(frame, text=card["number"], font=(_APP_FONT, 14, "bold"),
                 fg=TEXT_WHITE, bg=card["color"]).pack(anchor="w", pady=(10, 0))
        tk.Label(frame, text=self._fmt(card_balance), font=FONT_MAIN,
                 fg=TEXT_WHITE, bg=card["color"]).pack(anchor="w", pady=(2, 0))

        def bind_rec(w):
            w.bind("<Button-1>", lambda e, c=card: self._show_card_details(c))
            for child in w.winfo_children():
                bind_rec(child)
        bind_rec(frame)

    def _build_operations(self):
        wrap = tk.Frame(self.container, bg=BG_DARK, padx=20, pady=16)
        wrap.pack(fill="both", expand=True)

        head = tk.Frame(wrap, bg=BG_DARK)
        head.pack(fill="x", pady=(0, 8))
        tk.Label(head, text="История операций", font=FONT_BOLD,
                 fg=TEXT_WHITE, bg=BG_DARK).pack(side="left")
        tk.Button(head, text="Вся история", font=FONT_SMALL,
                  bg=BG_DARK, fg=YELLOW, relief="flat", bd=0,
                  activebackground=BG_DARK, activeforeground=YELLOW,
                  cursor="hand2", command=self._show_all_operations).pack(side="right")

        self._operations_list(wrap, limit=5)

    def _operations_list(self, parent, limit=None):
        canvas = tk.Canvas(parent, bg=BG_DARK, highlightthickness=0)
        scroll = tk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=BG_DARK)

        inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scroll.set)

        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self._bind_wheel(canvas)

        ops = self.operations if limit is None else self.operations[:limit]
        for name, amount, when in ops:
            self._make_operation_row(inner, name, amount, when)
        return canvas

    def _make_operation_row(self, parent, name, amount, when):
        row = tk.Frame(parent, bg=BG_CARD, padx=12, pady=10, cursor="hand2")
        row.pack(fill="x", pady=3)

        icon = tk.Canvas(row, width=36, height=36, bg=BG_CARD,
                         highlightthickness=0)
        icon.pack(side="left")
        icon.create_oval(2, 2, 34, 34, fill=BG_CARD_ALT, outline="")
        icon.create_text(18, 18, text=name[0].upper(),
                         fill=TEXT_WHITE, font=(_APP_FONT, 12, "bold"))

        info = tk.Frame(row, bg=BG_CARD)
        info.pack(side="left", padx=10, fill="x", expand=True)
        tk.Label(info, text=name, font=FONT_MAIN, fg=TEXT_WHITE,
                 bg=BG_CARD, anchor="w").pack(anchor="w")
        tk.Label(info, text=when, font=FONT_SMALL, fg=TEXT_GRAY,
                 bg=BG_CARD, anchor="w").pack(anchor="w")

        color = GREEN if amount > 0 else TEXT_WHITE
        sign = "+" if amount > 0 else "−"
        tk.Label(row, text=f"{sign}{self._fmt(abs(amount))}",
                 font=FONT_BOLD, fg=color, bg=BG_CARD).pack(side="right")

        def bind_rec(w):
            w.bind("<Button-1>",
                   lambda e, n=name, a=amount, t=when: self._show_op_detail(n, a, t))
            for child in w.winfo_children():
                bind_rec(child)
        bind_rec(row)

    def _show_payments(self):
        self._clear()
        self._sub_header("Платежи")

        services = [
            ("🛒", "Супермаркеты", lambda: self._dialog_pay("Супермаркеты")),
            ("🍔", "Рестораны",    lambda: self._dialog_pay("Рестораны")),
            ("⛽", "АЗС",          lambda: self._dialog_pay("АЗС")),
            ("🏥", "Аптеки",       lambda: self._dialog_pay("Аптеки")),
            ("🎬", "Кино",         lambda: self._dialog_pay("Кино")),
            ("✈️", "Путешествия",  lambda: self._dialog_pay("Путешествия")),
        ]
        wrap = tk.Frame(self.container, bg=BG_DARK, padx=20, pady=10)
        wrap.pack(fill="both", expand=True)

        for i, (emoji, label, cmd) in enumerate(services):
            card = tk.Frame(wrap, bg=BG_CARD, padx=14, pady=14, cursor="hand2")
            card.grid(row=i // 2, column=i % 2, padx=4, pady=4, sticky="nsew")
            wrap.columnconfigure(i % 2, weight=1)

            tk.Label(card, text=emoji, font=(_APP_FONT, 22),
                     bg=BG_CARD).pack(anchor="w")
            tk.Label(card, text=label, font=FONT_MAIN, fg=TEXT_WHITE,
                     bg=BG_CARD).pack(anchor="w", pady=(6, 0))

            def bind_rec(w, c=cmd):
                w.bind("<Button-1>", lambda e: c())
                for child in w.winfo_children():
                    bind_rec(child)
            bind_rec(card)


    def _show_invest(self):
        self._clear()
        self._sub_header("Инвестиции")

        wrap = tk.Frame(self.container, bg=BG_DARK, padx=20, pady=10)
        wrap.pack(fill="both", expand=True)

        portfolio = [
            ("Сбербанк", "SBER", 250, 318.5,  +12400.0),
            ("Газпром",  "GAZP", 100, 165.2,  -3200.0),
            ("Яндекс",   "YNDX", 10,  4120.0, +8700.0),
        ]
        tk.Label(wrap, text="Портфель", font=FONT_BOLD,
                 fg=TEXT_WHITE, bg=BG_DARK).pack(anchor="w", pady=(0, 8))

        for name, ticker, qty, price, pnl in portfolio:
            card = tk.Frame(wrap, bg=BG_CARD, padx=14, pady=12)
            card.pack(fill="x", pady=4)

            left = tk.Frame(card, bg=BG_CARD)
            left.pack(side="left", anchor="w")
            tk.Label(left, text=name, font=FONT_BOLD, fg=TEXT_WHITE,
                     bg=BG_CARD).pack(anchor="w")
            tk.Label(left, text=f"{ticker} · {qty} шт × {price:,.2f} ₽",
                     font=FONT_SMALL, fg=TEXT_GRAY, bg=BG_CARD).pack(anchor="w")

            color = GREEN if pnl >= 0 else RED
            sign = "+" if pnl >= 0 else "−"
            tk.Label(card, text=f"{sign}{abs(pnl):,.2f} ₽",
                     font=FONT_BOLD, fg=color, bg=BG_CARD).pack(side="right")

        tk.Button(wrap, text="Пополнить брокерский счёт",
                  bg=YELLOW, fg=BG_DARK, font=FONT_BOLD, relief="flat",
                  bd=0, pady=10, cursor="hand2",
                  activebackground=YELLOW_DARK,
                  command=self._dialog_broker_topup).pack(fill="x", pady=(16, 0))


    def _show_card_details(self, card):
        self._clear()
        self._sub_header(f"Карта {card['name']}")

        wrap = tk.Frame(self.container, bg=BG_DARK, padx=20, pady=10)
        wrap.pack(fill="both", expand=True)

        card_balance = self.balance if card["name"] == "Black" else 45_000.00
        preview = tk.Frame(wrap, bg=card["color"], padx=20, pady=24)
        preview.pack(fill="x")
        tk.Label(preview, text=card["name"], font=FONT_BOLD,
                 fg=YELLOW, bg=card["color"]).pack(anchor="w")
        tk.Label(preview, text=card["number"], font=(_APP_FONT, 16, "bold"),
                 fg=TEXT_WHITE, bg=card["color"]).pack(anchor="w", pady=(10, 0))
        tk.Label(preview, text=self._fmt(card_balance), font=FONT_MAIN,
                 fg=TEXT_WHITE, bg=card["color"]).pack(anchor="w", pady=(4, 0))

        actions = [
            ("Пополнить",     self._dialog_topup),
            ("Перевести",     self._dialog_transfer),
            ("Заблокировать", lambda: self._block_card(card)),
            ("Реквизиты",     lambda: self._show_requisites(card)),
        ]
        for text, cmd in actions:
            tk.Button(wrap, text=text, font=FONT_MAIN, anchor="w",
                      bg=BG_CARD, fg=TEXT_WHITE, relief="flat", bd=0,
                      padx=16, pady=12, cursor="hand2",
                      activebackground=BG_CARD_ALT, activeforeground=TEXT_WHITE,
                      command=cmd).pack(fill="x", pady=3)

    def _block_card(self, card):
        if messagebox.askyesno("Блокировка", f"Заблокировать карту {card['number']}?"):
            self._add_operation(f"Блокировка {card['number']}", 0.0)
            messagebox.showinfo("Готово", "Карта заблокирована (демо).")

    def _show_requisites(self, card):
        messagebox.showinfo(
            "Реквизиты",
            f"Карта: {card['name']} {card['number']}\n"
            f"Счёт: 40817 810 0 0000 0000000\n"
            f"БИК: 044525974 (Т-Банк)"
        )

    def _show_profile(self):
        self._clear()
        self._sub_header("Профиль")

        wrap = tk.Frame(self.container, bg=BG_DARK, padx=20, pady=10)
        wrap.pack(fill="both", expand=True)

        top = tk.Frame(wrap, bg=BG_DARK)
        top.pack(fill="x", pady=10)
        av = tk.Canvas(top, width=64, height=64, bg=BG_DARK, highlightthickness=0)
        av.pack(side="left")
        av.create_oval(2, 2, 62, 62, fill=YELLOW, outline="")
        av.create_text(32, 32, text=self.user["name"][0], fill=BG_DARK,
                       font=(_APP_FONT, 26, "bold"))

        info = tk.Frame(top, bg=BG_DARK)
        info.pack(side="left", padx=14)
        tk.Label(info, text=self.user["name"], font=FONT_BOLD,
                 fg=TEXT_WHITE, bg=BG_DARK).pack(anchor="w")
        tk.Label(info, text=self.user["phone"], font=FONT_SMALL,
                 fg=TEXT_GRAY, bg=BG_DARK).pack(anchor="w")

        items = [
            ("📄 Личные данные", lambda: messagebox.showinfo(
                "Личные данные", f"{self.user['name']}\n{self.user['phone']}")),
            ("🔒 Безопасность",  lambda: messagebox.showinfo(
                "Безопасность", "Вход по Face ID: включён\nПин-код: установлен")),
            ("🔔 Уведомления",   self._toggle_notifications),
            ("ℹ️ О приложении",  lambda: messagebox.showinfo(
                "О приложении", "Прототип банковского приложения\nTkinter demo v1.2")),
        ]
        for text, cmd in items:
            tk.Button(wrap, text=text, font=FONT_MAIN, anchor="w",
                      bg=BG_CARD, fg=TEXT_WHITE, relief="flat", bd=0,
                      padx=16, pady=12, cursor="hand2",
                      activebackground=BG_CARD_ALT, activeforeground=TEXT_WHITE,
                      command=cmd).pack(fill="x", pady=3)

        tk.Button(wrap, text="Выйти из аккаунта", font=FONT_BOLD,
                  bg=BG_DARK, fg=RED, relief="flat", bd=0, pady=14,
                  cursor="hand2", activebackground=BG_DARK,
                  activeforeground=YELLOW,
                  command=self._confirm_logout).pack(fill="x", pady=(20, 0))

    def _toggle_notifications(self):
        self.notifications_on = not getattr(self, "notifications_on", True)
        state = "включены" if self.notifications_on else "выключены"
        messagebox.showinfo("Уведомления", f"Push-уведомления {state}.")

    def _confirm_logout(self):
        if messagebox.askyesno("Выход", "Вы уверены, что хотите выйти?"):
            self.on_logout()

    def _show_all_operations(self):
        self._clear()
        self._sub_header("Все операции")

        wrap = tk.Frame(self.container, bg=BG_DARK, padx=20, pady=10)
        wrap.pack(fill="both", expand=True)
        self._operations_list(wrap, limit=None)

    def _show_op_detail(self, name, amount, when):
        sign = "+" if amount > 0 else "−"
        messagebox.showinfo(
            "Операция",
            f"{name}\n{when}\n\nСумма: {sign}{self._fmt(abs(amount))}\n"
            f"Статус: Выполнено"
        )

    def _modal(self, title, build_fn, height=280):
        win = tk.Toplevel(self)
        win.title(title)
        win.geometry(f"340x{height}")
        win.configure(bg=BG_CARD)
        win.transient(self.winfo_toplevel())
        win.grab_set()
        win.resizable(False, False)

        tk.Label(win, text=title, font=FONT_BOLD, fg=TEXT_WHITE,
                 bg=BG_CARD).pack(pady=(18, 10), padx=20, anchor="w")
        build_fn(win)
        return win

    def _dialog_buttons(self, win, on_confirm):
        row = tk.Frame(win, bg=BG_CARD)
        row.pack(fill="x", padx=20, pady=(6, 14), side="bottom")
        tk.Button(row, text="Отмена", bg=BG_CARD_ALT, fg=TEXT_WHITE,
                  font=FONT_MAIN, relief="flat", bd=0, padx=12, pady=8,
                  cursor="hand2", command=win.destroy).pack(
                      side="left", expand=True, fill="x", padx=(0, 4))
        tk.Button(row, text="Готово", bg=YELLOW, fg=BG_DARK,
                  font=FONT_BOLD, relief="flat", bd=0, padx=12, pady=8,
                  cursor="hand2", activebackground=YELLOW_DARK,
                  command=on_confirm).pack(
                      side="left", expand=True, fill="x", padx=(4, 0))

    def _parse_amount(self, raw: str):
        """Возвращает float > 0 или None. Поддерживает '1 000', '1000,5'."""
        try:
            cleaned = raw.replace(" ", "").replace(",", ".")
            val = float(cleaned)
            if not math.isfinite(val) or val <= 0:
                return None
            return val
        except ValueError:
            return None

    def _dialog_topup(self):
        def build(win):
            tk.Label(win, text="Сумма, ₽", font=FONT_SMALL, fg=TEXT_GRAY,
                     bg=BG_CARD).pack(anchor="w", padx=20)
            entry = tk.Entry(win, font=FONT_MAIN, bg=BG_CARD_ALT, fg=TEXT_WHITE,
                             insertbackground=TEXT_WHITE, relief="flat")
            entry.pack(fill="x", padx=20, pady=(4, 16), ipady=8)
            entry.insert(0, "1000")
            entry.focus_set()

            def confirm():
                amount = self._parse_amount(entry.get())
                if amount is None:
                    messagebox.showerror("Ошибка", "Введите положительное число")
                    return
                self.balance += amount
                self._sync_balance()
                self._add_operation("Пополнение", amount)
                win.destroy()
                self._show_main()

            self._dialog_buttons(win, confirm)
        self._modal("Пополнить", build)

    def _dialog_transfer(self):
        def build(win):
            tk.Label(win, text="Получатель", font=FONT_SMALL, fg=TEXT_GRAY,
                     bg=BG_CARD).pack(anchor="w", padx=20)
            to_entry = tk.Entry(win, font=FONT_MAIN, bg=BG_CARD_ALT, fg=TEXT_WHITE,
                                insertbackground=TEXT_WHITE, relief="flat")
            to_entry.pack(fill="x", padx=20, pady=(4, 10), ipady=6)
            to_entry.insert(0, "+7 900 555-11-22")

            tk.Label(win, text="Сумма, ₽", font=FONT_SMALL, fg=TEXT_GRAY,
                     bg=BG_CARD).pack(anchor="w", padx=20)
            amount_entry = tk.Entry(win, font=FONT_MAIN, bg=BG_CARD_ALT, fg=TEXT_WHITE,
                                    insertbackground=TEXT_WHITE, relief="flat")
            amount_entry.pack(fill="x", padx=20, pady=(4, 16), ipady=6)
            amount_entry.insert(0, "500")

            def confirm():
                amount = self._parse_amount(amount_entry.get())
                if amount is None:
                    messagebox.showerror("Ошибка", "Введите положительное число")
                    return
                recipient_phone = self.auth.normalize_phone(to_entry.get())
                if not recipient_phone:
                    messagebox.showerror("Ошибка", "Некорректный номер получателя")
                    return
                if recipient_phone == self.user["phone"]:
                    messagebox.showerror("Ошибка", "Нельзя перевести самому себе")
                    return
                if amount > self.balance:
                    messagebox.showerror("Ошибка", "Недостаточно средств")
                    return
                self.balance -= amount
                self._sync_balance()
                self._add_operation(f"Перевод: {recipient_phone}", -amount)
                win.destroy()
                self._show_main()
                messagebox.showinfo("Готово", f"Переведено {self._fmt(amount)}")

            self._dialog_buttons(win, confirm)
        self._modal("Перевод", build, height=300)

    def _dialog_mobile(self):
        def build(win):
            tk.Label(win, text="Номер телефона", font=FONT_SMALL, fg=TEXT_GRAY,
                     bg=BG_CARD).pack(anchor="w", padx=20)
            phone = tk.Entry(win, font=FONT_MAIN, bg=BG_CARD_ALT, fg=TEXT_WHITE,
                             insertbackground=TEXT_WHITE, relief="flat")
            phone.pack(fill="x", padx=20, pady=(4, 10), ipady=6)
            phone.insert(0, "+7 900 123-45-67")

            tk.Label(win, text="Сумма, ₽", font=FONT_SMALL, fg=TEXT_GRAY,
                     bg=BG_CARD).pack(anchor="w", padx=20)
            amount_entry = tk.Entry(win, font=FONT_MAIN, bg=BG_CARD_ALT, fg=TEXT_WHITE,
                                    insertbackground=TEXT_WHITE, relief="flat")
            amount_entry.pack(fill="x", padx=20, pady=(4, 16), ipady=6)
            amount_entry.insert(0, "300")

            def confirm():
                amount = self._parse_amount(amount_entry.get())
                if amount is None:
                    messagebox.showerror("Ошибка", "Введите положительное число")
                    return
                if not self.auth.normalize_phone(phone.get()):
                    messagebox.showerror("Ошибка", "Некорректный номер")
                    return
                if amount > self.balance:
                    messagebox.showerror("Ошибка", "Недостаточно средств")
                    return
                self.balance -= amount
                self._sync_balance()
                self._add_operation(f"Моб. связь {phone.get()}", -amount)
                win.destroy()
                self._show_main()
                messagebox.showinfo("Готово", "Платёж проведён")

            self._dialog_buttons(win, confirm)
        self._modal("Мобильная связь", build, height=300)

    def _dialog_pay(self, category):
        def build(win):
            tk.Label(win, text=f"Оплата: {category}", font=FONT_SMALL,
                     fg=TEXT_GRAY, bg=BG_CARD).pack(anchor="w", padx=20)
            entry = tk.Entry(win, font=FONT_MAIN, bg=BG_CARD_ALT, fg=TEXT_WHITE,
                             insertbackground=TEXT_WHITE, relief="flat")
            entry.pack(fill="x", padx=20, pady=(4, 16), ipady=8)
            entry.insert(0, "1000")
            entry.focus_set()

            def confirm():
                amount = self._parse_amount(entry.get())
                if amount is None:
                    messagebox.showerror("Ошибка", "Введите положительное число")
                    return
                if amount > self.balance:
                    messagebox.showerror("Ошибка", "Недостаточно средств")
                    return
                self.balance -= amount
                self._sync_balance()
                self._add_operation(f"Оплата: {category}", -amount)
                win.destroy()
                self._show_main()
                messagebox.showinfo("Готово", "Оплачено")

            self._dialog_buttons(win, confirm)
        self._modal(f"Оплата: {category}", build, height=260)

    def _dialog_broker_topup(self):
        def build(win):
            tk.Label(win, text="Сумма пополнения, ₽", font=FONT_SMALL,
                     fg=TEXT_GRAY, bg=BG_CARD).pack(anchor="w", padx=20)
            entry = tk.Entry(win, font=FONT_MAIN, bg=BG_CARD_ALT, fg=TEXT_WHITE,
                             insertbackground=TEXT_WHITE, relief="flat")
            entry.pack(fill="x", padx=20, pady=(4, 16), ipady=8)
            entry.insert(0, "5000")
            entry.focus_set()

            def confirm():
                amount = self._parse_amount(entry.get())
                if amount is None:
                    messagebox.showerror("Ошибка", "Введите положительное число")
                    return
                if amount > self.balance:
                    messagebox.showerror("Ошибка", "Недостаточно средств")
                    return
                self.balance -= amount
                self._sync_balance()
                self._add_operation("Брокерский счёт", -amount)
                win.destroy()
                self._show_main()
                messagebox.showinfo("Готово", "Счёт пополнен")

            self._dialog_buttons(win, confirm)
        self._modal("Брокерский счёт", build)

    def _sub_header(self, title):
        head = tk.Frame(self.container, bg=BG_DARK, pady=14, padx=20)
        head.pack(fill="x")
        tk.Button(head, text="←", font=(_APP_FONT, 16, "bold"),
                  bg=BG_DARK, fg=TEXT_WHITE, relief="flat", bd=0,
                  cursor="hand2", activebackground=BG_DARK,
                  activeforeground=YELLOW,
                  command=self._show_main).pack(side="left")
        tk.Label(head, text=title, font=FONT_BOLD, fg=TEXT_WHITE,
                 bg=BG_DARK).pack(side="left", padx=12)

    def _pill_button(self, parent, text, command, bg, fg):
        btn = tk.Button(parent, text=text, command=command,
                        bg=bg, fg=fg, font=FONT_MAIN,
                        relief="flat", bd=0, padx=16, pady=8,
                        activebackground=bg, activeforeground=fg,
                        cursor="hand2")
        btn.pack(side="left", padx=(0, 8))
        return btn

    def _add_operation(self, name, amount):
        now = datetime.now().strftime("%H:%M")
        self.operations.insert(0, (name, amount, f"Сегодня, {now}"))

    def _fmt(self, value):
        return f"{value:,.2f} ₽".replace(",", " ")



class BankApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Т-Банк (прототип)")
        self.geometry("420x720")
        self.configure(bg=BG_DARK)
        self.resizable(False, False)
        _init_fonts()

        self.auth = Auth()
        self.current_screen = None
        self._show_login()

    def _clear_screen(self):
        if self.current_screen:
            self.current_screen.destroy()
            self.current_screen = None
        try:
            self.unbind_all("<MouseWheel>")
        except tk.TclError:
            pass

    def _show_login(self):
        self._clear_screen()
        self.auth.logout()
        self.current_screen = LoginScreen(self, self.auth, self._on_login_success)
        self.current_screen.pack(fill="both", expand=True)

    def _on_login_success(self, user):
        self._clear_screen()
        self.current_screen = MainApp(self, self.auth, self._show_login)
        self.current_screen.pack(fill="both", expand=True)


if __name__ == "__main__":
    app = BankApp()
    app.mainloop()
