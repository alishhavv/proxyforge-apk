#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Proxy Forge v9.0 — Kivy GUI обёртка для Android APK
Оригинальный скрипт: proxy_forge.py (должен быть в той же директории)
"""

import sys
import os
import io
import threading
import queue
import platform

# Убеждаемся, что текущая директория в sys.path
_sys_path_ins = os.path.dirname(os.path.abspath(__file__))
if _sys_path_ins not in sys.path:
    sys.path.insert(0, _sys_path_ins)

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.checkbox import CheckBox
from kivy.uix.gridlayout import GridLayout
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.clock import Clock, mainthread
from kivy.core.window import Window
from kivy.utils import platform as kivy_platform

# ─── Цветовая схема (тёмная тема) ───────────────────────────────────────────
COLOR_BG = (0.12, 0.12, 0.14, 1.0)
COLOR_CARD = (0.18, 0.18, 0.22, 1.0)
COLOR_ACCENT = (0.26, 0.60, 0.98, 1.0)
COLOR_ACCENT_HOVER = (0.35, 0.68, 1.0, 1.0)
COLOR_DANGER = (0.90, 0.30, 0.30, 1.0)
COLOR_DANGER_HOVER = (1.0, 0.40, 0.40, 1.0)
COLOR_SUCCESS = (0.30, 0.80, 0.45, 1.0)
COLOR_TEXT = (0.92, 0.92, 0.95, 1.0)
COLOR_TEXT_DIM = (0.60, 0.60, 0.65, 1.0)
COLOR_INPUT_BG = (0.14, 0.14, 0.18, 1.0)
COLOR_BORDER = (0.28, 0.28, 0.34, 1.0)
COLOR_LOG_BG = (0.08, 0.08, 0.10, 1.0)

# ─── Перехват stdout/stderr для вывода логов в реальном времени ──────────────
_log_queue = queue.Queue()


class _StreamInterceptor(io.TextIOBase):
    """Перенаправляет write() в очередь для потоко-безопасного вывода."""

    def __init__(self, original, q: queue.Queue, prefix: str = ""):
        self.original = original
        self.q = q
        self.prefix = prefix

    def write(self, s):
        if s:
            self.q.put((self.prefix, s))
        return self.original.write(s)

    def flush(self):
        return self.original.flush()


def _patch_streams():
    sys.stdout = _StreamInterceptor(sys.__stdout__, _log_queue, "")
    sys.stderr = _StreamInterceptor(sys.__stderr__, _log_queue, "[E] ")


_patch_streams()

# ─── Kivy KV-стили (встроенные) ──────────────────────────────────────────────
KV = '''
<RootWidget>:
    orientation: "vertical"
    spacing: 0
    padding: 0

    # --- Заголовок ---
    BoxLayout:
        size_hint_y: None
        height: dp(56)
        padding: dp(16), 0
        canvas.before:
            Color:
                rgba: 0.14, 0.14, 0.20, 1
            Rectangle:
                pos: self.pos
                size: self.size
        Label:
            text: "Proxy Forge v9.0"
            font_size: sp(22)
            bold: True
            color: 0.26, 0.60, 0.98, 1
            halign: "left"
            valign: "center"
            size_hint_x: 1
        Label:
            text: "Android"
            font_size: sp(12)
            color: 0.55, 0.55, 0.60, 1
            halign: "right"
            valign: "center"
            size_hint_x: 0.3

    ScrollView:
        size_hint_y: 1
        do_scroll_x: False
        bar_width: dp(4)
        bar_color: 0.26, 0.60, 0.98, 0.5
        bar_inactive_color: 0.20, 0.20, 0.24, 0.5

        BoxLayout:
            orientation: "vertical"
            size_hint_y: None
            height: self.minimum_height
            padding: dp(12)
            spacing: dp(10)

            # ═══ Секция: Режим сканирования ═══
            BoxLayout:
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(6)
                canvas.before:
                    Color:
                        rgba: 0.18, 0.18, 0.22, 1
                    Rectangle:
                        pos: self.pos
                        size: self.size
                        radius: [dp(8)]
                padding: dp(12)

                Label:
                    text: "\\u2550\\u2550  РЕЖИМ СКАНИРОВАНИЯ  \\u2550\\u2550"
                    font_size: sp(13)
                    bold: True
                    color: 0.60, 0.60, 0.65, 1
                    size_hint_y: None
                    height: sp(24)

                GridLayout:
                    cols: 2
                    spacing: dp(8)
                    size_hint_y: None
                    height: self.minimum_height

                    ModeButton:
                        text: "\\U0001F50D  Полный скан"
                        mode: "full"
                        on_press: root.on_mode_press("full")
                    ModeButton:
                        text: "\\u26A1  Быстрый (без пинга)"
                        mode: "fast"
                        on_press: root.on_mode_press("fast")
                    ModeButton:
                        text: "\\U0001F3A8  Только Stealth"
                        mode: "stealth"
                        on_press: root.on_mode_press("stealth")
                    ModeButton:
                        text: "\\u2705  Whitelist режим"
                        mode: "whitelist"
                        on_press: root.on_mode_press("whitelist")

            # ═══ Секция: Параметры ═══
            BoxLayout:
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(6)
                canvas.before:
                    Color:
                        rgba: 0.18, 0.18, 0.22, 1
                    Rectangle:
                        pos: self.pos
                        size: self.size
                        radius: [dp(8)]
                padding: dp(12)

                Label:
                    text: "\\u2699\\uFE0F  ПАРАМЕТРЫ"
                    font_size: sp(13)
                    bold: True
                    color: 0.60, 0.60, 0.65, 1
                    size_hint_y: None
                    height: sp(24)

                GridLayout:
                    cols: 2
                    spacing: dp(8)
                    size_hint_y: None
                    height: self.minimum_height

                    Label:
                        text: "Топ (кол-во):"
                        font_size: sp(14)
                        color: 0.88, 0.88, 0.90, 1
                        size_hint_x: 0.4
                    ParamInput:
                        id: top_input
                        text: "20"
                        hint_text: "20"
                        multiline: False

                    Label:
                        text: "Страна:"
                        font_size: sp(14)
                        color: 0.88, 0.88, 0.90, 1
                        size_hint_x: 0.4
                    ParamInput:
                        id: country_input
                        text: ""
                        hint_text: "RU,UA,KZ,..."
                        multiline: False

                    Label:
                        text: "Протокол:"
                        font_size: sp(14)
                        color: 0.88, 0.88, 0.90, 1
                        size_hint_x: 0.4
                    ParamInput:
                        id: proto_input
                        text: "all"
                        hint_text: "all,socks5,http,..."
                        multiline: False

                    Label:
                        text: "Таймаут (сек):"
                        font_size: sp(14)
                        color: 0.88, 0.88, 0.90, 1
                        size_hint_x: 0.4
                    ParamInput:
                        id: timeout_input
                        text: "10"
                        hint_text: "10"
                        multiline: False

            # ═══ Секция: Опции ═══
            BoxLayout:
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(6)
                canvas.before:
                    Color:
                        rgba: 0.18, 0.18, 0.22, 1
                    Rectangle:
                        pos: self.pos
                        size: self.size
                        radius: [dp(8)]
                padding: dp(12)

                Label:
                    text: "\\U0001F527  ОПЦИИ"
                    font_size: sp(13)
                    bold: True
                    color: 0.60, 0.60, 0.65, 1
                    size_hint_y: None
                    height: sp(24)

                GridLayout:
                    cols: 1
                    spacing: dp(4)
                    size_hint_y: None
                    height: self.minimum_height

                    OptionRow:
                        id: opt_alive
                        label_text: "Только живые (--alive-only)"
                    OptionRow:
                        id: opt_clash
                        label_text: "Clash формат (--clash)"
                    OptionRow:
                        id: opt_b64
                        label_text: "Base64 кодирование (--b64)"
                    OptionRow:
                        id: opt_json
                        label_text: "JSON формат (--json)"
                    OptionRow:
                        id: opt_copy
                        label_text: "Копировать в буфер (--copy)"

            # ═══ Секция: Кнопки управления ═══
            BoxLayout:
                orientation: "horizontal"
                size_hint_y: None
                height: dp(52)
                spacing: dp(8)

                ActionButton:
                    id: btn_start
                    text: "\\u25B6  ЗАПУСК"
                    bg_color: 0.26, 0.60, 0.98, 1
                    bg_color_down: 0.35, 0.68, 1.0, 1
                    on_press: root.on_start_press()
                ActionButton:
                    id: btn_stop
                    text: "\\u23F9  СТОП"
                    bg_color: 0.90, 0.30, 0.30, 1
                    bg_color_down: 1.0, 0.40, 0.40, 1
                    disabled: True
                    on_press: root.on_stop_press()
                ActionButton:
                    id: btn_clear
                    text: "\\U0001F5D1  Очистить"
                    bg_color: 0.35, 0.35, 0.40, 1
                    bg_color_down: 0.45, 0.45, 0.50, 1
                    on_press: root.on_clear_press()

            # ═══ Секция: Лог вывода ═══
            BoxLayout:
                orientation: "vertical"
                size_hint_y: None
                height: dp(300)
                spacing: dp(6)
                canvas.before:
                    Color:
                        rgba: 0.18, 0.18, 0.22, 1
                    Rectangle:
                        pos: self.pos
                        size: self.size
                        radius: [dp(8)]
                padding: dp(8)

                Label:
                    text: "\\U0001F4CB  ВЫВОД ЛОГА"
                    font_size: sp(13)
                    bold: True
                    color: 0.60, 0.60, 0.65, 1
                    size_hint_y: None
                    height: sp(22)

                LogOutput:
                    id: log_output
                    size_hint_y: 1
                    font_name: "RobotoMono-Regular.ttf"
                    font_size: sp(11)
                    foreground_color: 0.75, 0.80, 0.75, 1
                    background_color: 0.06, 0.06, 0.08, 1
                    cursor_color: 0.26, 0.60, 0.98, 1
                    readonly: True
                    padding: dp(8), dp(6)
                    hint_text: "Здесь появится вывод команды..."
                    do_scroll_x: True

            # Нижний отступ
            Widget:
                size_hint_y: None
                height: dp(16)


<ModeButton@Button>:
    size_hint_y: None
    height: dp(44)
    font_size: sp(13)
    bold: True
    background_color: (0.22, 0.50, 0.85, 1) if self.state == "down" else (0.16, 0.16, 0.20, 1)
    color: (1, 1, 1, 1) if self.state == "down" else (0.82, 0.82, 0.85, 1)
    border_radius: dp(6)
    canvas.before:
        Color:
            rgba: 0.26, 0.60, 0.98, 0.35 if self.state == "down" else 0.15
        Line:
            width: 1.5 if self.state == "down" else 1
            rounded_rectangle: self.x, self.y, self.width, self.height, dp(6)


<ParamInput@TextInput>:
    font_size: sp(14)
    multiline: False
    padding: dp(10), dp(8)
    background_color: 0.14, 0.14, 0.18, 1
    foreground_color: 0.92, 0.92, 0.95, 1
    cursor_color: 0.26, 0.60, 0.98, 1
    hint_text_color: 0.45, 0.45, 0.50, 1
    selection_color: 0.26, 0.60, 0.98, 0.35
    border_radius: dp(6)
    canvas.after:
        Color:
            rgba: 0.35, 0.35, 0.42, 0.8
        Line:
            width: 1
            rounded_rectangle: self.x, self.y, self.width, self.height, dp(6)


<OptionRow@BoxLayout>:
    orientation: "horizontal"
    size_hint_y: None
    height: dp(36)
    spacing: dp(10)
    padding: 0, dp(4)

    CheckBox:
        size_hint_x: None
        width: dp(28)
        active: False
        color: 0.26, 0.60, 0.98, 1
        canvas.before:
            Color:
                rgba: 0.25, 0.25, 0.30, 1
            Rectangle:
                pos: self.center_x - dp(12), self.center_y - dp(12)
                size: dp(24), dp(24)
            Color:
                rgba: 0.26, 0.60, 0.98, 0.2
            Line:
                width: 1
                rounded_rectangle: self.center_x - dp(12), self.center_y - dp(12), dp(24), dp(24), dp(4)

    Label:
        text: root.label_text
        font_size: sp(13)
        color: 0.82, 0.82, 0.85, 1
        valign: "middle"


<ActionButton@Button>:
    size_hint_x: 1
    font_size: sp(14)
    bold: True
    border_radius: dp(8)
    background_normal: ""
    background_down: ""
    color: 1, 1, 1, 1
    canvas.before:
        Color:
            rgba: root.bg_color if not self.disabled else (0.25, 0.25, 0.28, 1)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(8)]


<LogOutput@TextInput>:
    readonly: True
    font_size: sp(11)
    background_color: 0.06, 0.06, 0.08, 1
    foreground_color: 0.75, 0.80, 0.75, 1
    cursor_blink: False
    border_radius: dp(4)
    canvas.after:
        Color:
            rgba: 0.30, 0.30, 0.36, 0.6
        Line:
            width: 1
            rounded_rectangle: self.x, self.y, self.width, self.height, dp(4)


<RoundedRectangle@Instruction>:
    pass
'''


# ─── Основной виджет ─────────────────────────────────────────────────────────
class RootWidget(BoxLayout):
    _worker_thread: threading.Thread | None = None
    _stop_event = threading.Event()
    _current_mode: str = "full"
    _running: bool = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._bind_ids()

    def _bind_ids(self):
        """Связываем ID после загрузки KV."""
        Clock.schedule_once(self._deferred_bind, 0.1)

    def _deferred_bind(self, dt):
        pass

    def on_mode_press(self, mode: str):
        self._current_mode = mode
        self._log(f"[UI] Выбран режим: {mode}")
        # Визуальная индикация через обновление дочерних кнопок
        for child in self.walk_reverse():
            if isinstance(child, Button) and hasattr(child, 'mode'):
                child.state = "down" if child.mode == mode else "normal"

    def on_start_press(self):
        if self._running:
            self._log("[UI] Скан уже запущен!")
            return
        self._run_proxy_forge()

    def on_stop_press(self):
        self._stop_event.set()
        self._log("[UI] Остановка...")
        self._set_buttons_state(running=False)

    def on_clear_press(self):
        log_output = self.ids.get("log_output")
        if log_output:
            log_output.text = ""

    def _set_buttons_state(self, running: bool):
        self._running = running
        btn_start = self.ids.get("btn_start")
        btn_stop = self.ids.get("btn_stop")
        if btn_start:
            btn_start.disabled = running
        if btn_stop:
            btn_stop.disabled = not running

    def _build_args(self) -> list[str]:
        """Собираем аргументы для proxy_forge.main() на основе UI."""
        args = []

        mode = self._current_mode
        if mode == "full":
            # По умолчанию — полный скан, без доп. флагов режима
            pass
        elif mode == "fast":
            args.extend(["--fast"])
        elif mode == "stealth":
            args.extend(["--stealth"])
        elif mode == "whitelist":
            args.extend(["--whitelist"])

        # --top
        top_val = self.ids.get("top_input")
        if top_val and top_val.text.strip():
            args.extend(["--top", top_val.text.strip()])

        # --country
        country_val = self.ids.get("country_input")
        if country_val and country_val.text.strip():
            args.extend(["--country", country_val.text.strip()])

        # --proto
        proto_val = self.ids.get("proto_input")
        if proto_val and proto_val.text.strip():
            args.extend(["--proto", proto_val.text.strip()])

        # --timeout
        timeout_val = self.ids.get("timeout_input")
        if timeout_val and timeout_val.text.strip():
            args.extend(["--timeout", timeout_val.text.strip()])

        # Чекбоксы
        if self.ids.get("opt_alive") and self.ids["opt_alive"].children[0].active:
            args.append("--alive-only")
        if self.ids.get("opt_clash") and self.ids["opt_clash"].children[0].active:
            args.append("--clash")
        if self.ids.get("opt_b64") and self.ids["opt_b64"].children[0].active:
            args.append("--b64")
        if self.ids.get("opt_json") and self.ids["opt_json"].children[0].active:
            args.append("--json")
        if self.ids.get("opt_copy") and self.ids["opt_copy"].children[0].active:
            args.append("--copy")

        return args

    def _run_proxy_forge(self):
        """Запуск proxy_forge в отдельном потоке."""
        self._stop_event.clear()
        args = self._build_args()
        self._log(f"[UI] Запуск с аргументами: {args}")
        self._set_buttons_state(running=True)

        self._worker_thread = threading.Thread(
            target=self._worker_func,
            args=(args,),
            daemon=True,
            name="proxy_forge_worker",
        )
        self._worker_thread.start()

        # Запуск опроса очереди логов
        Clock.schedule_interval(self._poll_logs, 0.1)

    def _worker_func(self, args: list[str]):
        """Рабочая функция — выполняется в отдельном потоке."""
        try:
            import proxy_forge
            self._log("[SYS] Модуль proxy_forge загружен успешно")
            # Ожидаем, что proxy_forge имеет функцию main(argv) или main()
            if hasattr(proxy_forge, "main"):
                proxy_forge.main(args)
            else:
                self._log("[E] ОШИБКА: proxy_forge не имеет функции main()")
        except ImportError:
            self._log("[E] ОШИБКА: Не удалось импортировать модуль proxy_forge")
            self._log("[E] Убедитесь, что proxy_forge.py находится рядом с main.py")
        except Exception as e:
            self._log(f"[E] Исключение: {type(e).__name__}: {e}")
        finally:
            Clock.schedule_once(lambda dt: self._set_buttons_state(running=False))

    def _poll_logs(self, dt):
        """Опрос очереди и обновление текстового поля лога."""
        log_output = self.ids.get("log_output")
        if not log_output:
            return

        updated = False
        chunks = []
        try:
            while True:
                prefix, text = _log_queue.get_nowait()
                chunks.append(prefix + text)
                updated = True
        except queue.Empty:
            pass

        if updated and log_output:
            combined = "".join(chunks)
            # Обновляем через Clock для потокобезопасности
            Clock.schedule_once(
                lambda dt, c=combined: self._append_log(c),
                0
            )

    def _append_log(self, text: str):
        log_output = self.ids.get("log_output")
        if log_output:
            if log_output.text:
                log_output.text += text
            else:
                log_output.text = text
            # Автопрокрутка
            log_output.cursor = (len(log_output.text), 0)
            log_output.focus = False

    def _log(self, msg: str):
        """Безопасная запись в лог из любого потока."""
        _log_queue.put(("", msg + "\n"))


# ─── Приложение ──────────────────────────────────────────────────────────────
class ProxyForgeApp(App):
    title = "Proxy Forge v9.0"
    icon = ""  # можно указать путь к иконке .png

    def build(self):
        Window.clearcolor = COLOR_BG
        Window.statusbar_text = (0.92, 0.92, 0.95, 1)
        if kivy_platform == "android":
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.INTERNET,
                Permission.ACCESS_NETWORK_STATE,
                Permission.WRITE_EXTERNAL_STORAGE,
                Permission.READ_EXTERNAL_STORAGE,
            ])
        return RootWidget()

    def on_pause(self):
        return True

    def on_resume(self):
        pass


def main():
    ProxyForgeApp().run()


if __name__ == "__main__":
    main()
